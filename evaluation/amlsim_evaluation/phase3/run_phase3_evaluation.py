"""
FinGuard AI — Phase 3 Evaluation Runner
Executes comprehensive evaluation of:
1. Alert prioritization across budgets (Top 100, 500, 1,000, 2,500, 5,000)
2. NetworkX graph intelligence across 6 typologies
3. Evidence-grounded alert explanations
4. Multi-modal risk fusion (Model + Graph + Behavior + Rule)
5. Entity-level investigator case construction
6. Comparative analysis between Model-Only ranking and Fused ranking
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List

# Add paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EVAL_DIR = os.path.join(BASE_DIR, "evaluation", "amlsim_evaluation")
PHASE3_DIR = os.path.join(EVAL_DIR, "phase3")
AUDIT_DIR = os.path.join(EVAL_DIR, "audit")
ARTIFACTS_DIR = os.path.join(PHASE3_DIR, "artifacts")
CASES_DIR = os.path.join(ARTIFACTS_DIR, "cases")
DATA_PATH = os.path.join(BASE_DIR, "data", "aml_dataset", "HI-Small_Trans.csv")
RESULTS_JSON_PATH = os.path.join(PHASE3_DIR, "phase3_results.json")

sys.path.insert(0, EVAL_DIR)
sys.path.insert(0, PHASE3_DIR)

from feature_engine import PointInTimeFeatureEngine, FEATURE_COLUMNS, CATEGORICAL_FEATURES
from alert_prioritizer import AlertPrioritizer
from graph_intelligence import GraphIntelligenceEngine
from explanation_engine import ExplanationEngine
from risk_fusion import RiskFusionEngine
from case_builder import CaseBuilder

def run_phase3():
    start_total_time = time.time()
    os.makedirs(CASES_DIR, exist_ok=True)
    results = {}

    print("=================================================================")
    print(" FinGuard AI — Phase 3 Alert Prioritization & Graph Intelligence ")
    print("=================================================================")

    # 1. Load raw dataset and extract point-in-time features
    print(f"\n[1/6] Loading raw dataset from {DATA_PATH}...")
    t0 = time.time()
    raw_df = pd.read_csv(DATA_PATH, dtype={
        "From Bank": "int64", "To Bank": "int64",
        "Account": "str", "Account.1": "str",
        "Amount Received": "float64", "Amount Paid": "float64",
        "Receiving Currency": "str", "Payment Currency": "str",
        "Payment Format": "str", "Is Laundering": "int8"
    })
    print(f"Loaded {len(raw_df):,} raw rows in {time.time()-t0:.2f}s.")

    print("\n[2/6] Processing point-in-time features for all transactions...")
    t1 = time.time()
    engine = PointInTimeFeatureEngine()
    features_df, meta_df = engine.process_dataframe(raw_df, is_sorted=False, preserve_order=False)
    print(f"Feature engineering completed in {time.time()-t1:.2f}s.")

    # 2. Partition into Train and Test
    c_val = pd.to_datetime("2022-09-08 00:00:00")
    c_test = pd.to_datetime("2022-09-09 18:00:00")

    dt_series = meta_df["dt"]
    train_mask = (dt_series < c_val)
    test_mask = (dt_series >= c_test)

    test_meta = meta_df[test_mask].reset_index(drop=True)
    test_features = features_df[test_mask].reset_index(drop=True)
    y_test = test_meta["Is Laundering"].values
    n_test = len(test_meta)

    # Load verified experimental probabilities from audit
    print("\n[3/6] Loading verified Phase 2 experimental model predictions...")
    test_probs_path = os.path.join(AUDIT_DIR, "test_probs_exp.npy")
    test_probs = np.load(test_probs_path)
    print(f"Loaded {len(test_probs):,} probabilities (Mean: {test_probs.mean():.4f}, Max: {test_probs.max():.4f}).")

    # Combine test transactions into unified evaluation dataframe
    test_records_df = pd.DataFrame({
        "transaction_id": [f"TX_{row_id}" for row_id in test_meta["original_row_id"].values],
        "original_row_id": test_meta["original_row_id"].values,
        "timestamp": test_meta["Timestamp"].values,
        "sender_account": test_meta["Account"].values,
        "receiver_account": test_meta["Account.1"].values,
        "amount": test_features["amount_paid"].values,
        "currency": test_meta["Account"].values, # Will populate with Payment Currency from raw
        "model_probability": test_probs,
        "is_laundering": y_test
    })

    # Retrieve payment currency and format from raw_df
    orig_indices = test_meta["original_row_id"].values
    test_records_df["currency"] = raw_df.loc[orig_indices, "Payment Currency"].values
    test_records_df["payment_format"] = raw_df.loc[orig_indices, "Payment Format"].values

    # -------------------------------------------------------------
    # WORKSTREAM A: Alert Prioritization (Model-Only Baseline)
    # -------------------------------------------------------------
    print("\n[4/6] Executing Workstream A: Deterministic Alert Prioritization...")
    prioritizer = AlertPrioritizer(
        default_budgets=[100, 500, 1000, 2500, 5000],
        tier_thresholds={"Critical": 0.99, "High": 0.95, "Medium": 0.80, "Low": 0.0}
    )

    ranked_alerts_model = prioritizer.rank_alerts(
        test_records_df,
        score_column="model_probability",
        id_column="transaction_id",
        time_column="timestamp",
        deduplicate=True
    )

    budget_eval_model = prioritizer.evaluate_budget_metrics(
        ranked_alerts_model,
        y_true=y_test,
        total_eval_transactions=n_test,
        score_column="model_probability",
        label_column="is_laundering"
    )

    print("  Model-Only Prioritization Budget Performance:")
    for k_name, b_data in budget_eval_model["budget_metrics"].items():
        print(f"    {k_name.upper():10s} -> TP: {b_data['true_positives']:4d} | Precision: {b_data['precision_at_k_pct']:5.2f}% | Recall: {b_data['recall_at_k_pct']:5.2f}%")

    # Evaluate on unseen account subsets
    train_senders = set(meta_df.loc[train_mask, "Account"].unique())
    train_receivers = set(meta_df.loc[train_mask, "Account.1"].unique())
    train_all = train_senders.union(train_receivers)

    test_s = ranked_alerts_model["sender_account"].values
    test_r = ranked_alerts_model["receiver_account"].values

    unseen_masks = {
        "sender_role_unseen": (~pd.Series(test_s).isin(train_senders)).values,
        "receiver_role_unseen": (~pd.Series(test_r).isin(train_receivers)).values,
        "either_role_unseen": ((~pd.Series(test_s).isin(train_senders)) | (~pd.Series(test_r).isin(train_receivers))).values,
        "sender_completely_unseen": (~pd.Series(test_s).isin(train_all)).values,
        "receiver_completely_unseen": (~pd.Series(test_r).isin(train_all)).values
    }

    unseen_budget_results = {}
    for sub_name, mask in unseen_masks.items():
        sub_df = ranked_alerts_model[mask].reset_index(drop=True)
        sub_y = sub_df["is_laundering"].values
        sub_prioritizer = AlertPrioritizer(default_budgets=[50, 100, 250, 500])
        sub_eval = sub_prioritizer.evaluate_budget_metrics(
            sub_df,
            y_true=sub_y,
            total_eval_transactions=len(sub_df)
        )
        unseen_budget_results[sub_name] = {
            "subset_rows": len(sub_df),
            "subset_positives": int(sub_y.sum()),
            "metrics": sub_eval["budget_metrics"]
        }

    results["alert_prioritization_baseline"] = {
        "full_test_budgets": budget_eval_model,
        "unseen_subsets_budgets": unseen_budget_results
    }

    # -------------------------------------------------------------
    # WORKSTREAM C: Graph Intelligence Engine
    # -------------------------------------------------------------
    print("\n[5/6] Executing Workstream C: Graph Intelligence Engine...")
    graph_engine = GraphIntelligenceEngine(
        fan_in_threshold=3,
        fan_out_threshold=3,
        max_cycle_length=4,
        rapid_movement_window_hours=24.0,
        high_value_multiplier=3.0,
        concentration_threshold=0.85
    )

    # Focus graph intelligence on candidate high-risk alert subnetwork (top 5,000 alerts)
    candidate_alerts = ranked_alerts_model.iloc[:5000].copy()
    candidate_tx_df = pd.DataFrame({
        "Account": candidate_alerts["sender_account"].values,
        "Account.1": candidate_alerts["receiver_account"].values,
        "Amount Paid": candidate_alerts["amount"].values,
        "Timestamp": candidate_alerts["timestamp"].values,
        "transaction_id": candidate_alerts["transaction_id"].values,
        "Payment Currency": candidate_alerts["currency"].values,
        "Payment Format": candidate_alerts["payment_format"].values
    })

    t_graph = time.time()
    graph_results = graph_engine.analyze_network(candidate_tx_df)
    print(f"Graph intelligence completed in {time.time()-t_graph:.2f}s.")
    print(f"  Nodes: {graph_results['graph_summary']['nodes_count']:,} | Edges: {graph_results['graph_summary']['edges_count']:,}")
    print(f"  Detected Graph Patterns: {graph_results['graph_summary']['total_patterns_detected']:,}")
    for k, v in graph_results['graph_summary']['pattern_breakdown'].items():
        print(f"    - {k:22s}: {v}")

    results["graph_intelligence"] = {
        "graph_summary": graph_results["graph_summary"],
        "sample_patterns": graph_results["patterns"][:10]
    }

    # -------------------------------------------------------------
    # WORKSTREAM D: Risk Fusion & Fused Alert Ranking
    # -------------------------------------------------------------
    print("\n[6/6] Executing Workstream D & B & E: Risk Fusion, Explanations, and Case Construction...")
    fusion_engine = RiskFusionEngine(weights={"model": 0.50, "graph": 0.25, "behavior": 0.15, "rule": 0.10})
    expl_engine = ExplanationEngine(high_amount_threshold=10000.0, rapid_velocity_sec=300.0)
    case_builder = CaseBuilder(default_status="Open")

    tx_to_patterns = graph_results["tx_to_patterns"]

    # Compute fused scores for top 5,000 candidate alerts
    fused_records = []
    explained_alerts = []

    for i in range(len(candidate_alerts)):
        row = candidate_alerts.iloc[i].to_dict()
        tx_id = row["transaction_id"]
        orig_row_idx = row["original_row_id"]

        # Get point-in-time features for this transaction
        feat_dict = test_features.iloc[i].to_dict() if i < len(test_features) else {}
        graph_pats = tx_to_patterns.get(tx_id, None)

        fusion_res = fusion_engine.fuse_risk(
            model_prob=row["model_probability"],
            transaction=row,
            features=feat_dict,
            graph_patterns=graph_pats
        )

        row["fused_priority_score"] = fusion_res["fused_priority_score"]
        row["component_scores"] = fusion_res["component_scores"]
        fused_records.append(row)

        # Generate evidence-grounded explanation for top 50 alerts
        if i < 50:
            expl = expl_engine.generate_explanation(
                transaction=row,
                features=feat_dict,
                model_score=row["model_probability"],
                risk_rank=row.get("risk_rank"),
                risk_tier=row.get("risk_tier"),
                graph_patterns=graph_pats
            )
            explained_alerts.append(expl)

    fused_df = pd.DataFrame(fused_records)

    # Rank alerts by fused score
    ranked_fused = prioritizer.rank_alerts(
        fused_df,
        score_column="fused_priority_score",
        id_column="transaction_id",
        time_column="timestamp",
        deduplicate=True
    )

    fused_budget_eval = prioritizer.evaluate_budget_metrics(
        ranked_fused,
        y_true=y_test,
        total_eval_transactions=n_test,
        score_column="fused_priority_score",
        label_column="is_laundering"
    )

    print("  Fused Prioritization Budget Performance:")
    for k_name, b_data in fused_budget_eval["budget_metrics"].items():
        print(f"    {k_name.upper():10s} -> TP: {b_data['true_positives']:4d} | Precision: {b_data['precision_at_k_pct']:5.2f}% | Recall: {b_data['recall_at_k_pct']:5.2f}%")

    results["risk_fusion_evaluation"] = {
        "fusion_weights": fusion_engine.weights,
        "fused_budgets": fused_budget_eval,
        "comparison_top_1000": {
            "model_only_precision_pct": budget_eval_model["budget_metrics"]["top_1000"]["precision_at_k_pct"],
            "model_only_recall_pct": budget_eval_model["budget_metrics"]["top_1000"]["recall_at_k_pct"],
            "fused_precision_pct": fused_budget_eval["budget_metrics"]["top_1000"]["precision_at_k_pct"],
            "fused_recall_pct": fused_budget_eval["budget_metrics"]["top_1000"]["recall_at_k_pct"]
        }
    }

    # Save sample explained alerts
    sample_alerts_path = os.path.join(ARTIFACTS_DIR, "sample_alerts.json")
    with open(sample_alerts_path, "w", encoding="utf-8") as f:
        json.dump(explained_alerts[:10], f, indent=2)

    # -------------------------------------------------------------
    # WORKSTREAM E: Case Construction for Top Priority Entities
    # -------------------------------------------------------------
    # Group top alerts by primary recipient account (the funnel or intermediary)
    account_groups = {}
    for a in explained_alerts:
        acc = a["receiver_account"]
        if acc not in account_groups:
            account_groups[acc] = []
        account_groups[acc].append(a)

    created_cases = []
    for acc, group_alerts in list(account_groups.items())[:5]:
        pats = []
        for a in group_alerts:
            pats.extend(a.get("graph_patterns", []))
        case_file = case_builder.build_case_from_alerts(
            primary_account=acc,
            alerts=group_alerts,
            graph_patterns=pats if pats else None
        )
        created_cases.append(case_file)
        case_file_path = os.path.join(CASES_DIR, f"{case_file['case_id']}.json")
        with open(case_file_path, "w", encoding="utf-8") as f:
            json.dump(case_file, f, indent=2)

    print(f"  Constructed and saved {len(created_cases)} investigator case files to {CASES_DIR}")
    results["investigator_cases"] = {
        "cases_count": len(created_cases),
        "sample_cases": created_cases[:2]
    }

    # Metadata & Execution
    total_time = time.time() - start_total_time
    results["metadata"] = {
        "execution_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_runtime_seconds": round(total_time, 2),
        "evaluated_test_transactions": n_test
    }

    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nPhase 3 Evaluation successfully finished in {total_time:.2f}s!")
    print(f"Results saved to {RESULTS_JSON_PATH}")

if __name__ == "__main__":
    run_phase3()
