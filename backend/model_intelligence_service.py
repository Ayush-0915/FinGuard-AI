"""
FinGuard AI — Model Intelligence Service
Aggregates audited metadata, model architecture parameters, performance metrics,
feature importance rankings, risk fusion mechanics, alert budget tradeoffs,
and explainability insights for the Model Intelligence & Performance Dashboard.
"""

import os
import json
import hashlib
from typing import Dict, Any

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR = os.path.join(ROOT_DIR, "models")
EVAL_DIR = os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation")
IBM_EXPORT_DIR = os.path.join(EVAL_DIR, "ibm_export", "artifacts")


def _calc_sha256(path: str) -> str:
    """Computes SHA-256 hash of a file or returns fallback."""
    if not os.path.exists(path):
        return "N/A"
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "N/A"


def _load_json(path: str, default: Any = None) -> Any:
    """Safely loads a JSON file or returns default."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def get_model_intelligence_data() -> Dict[str, Any]:
    """
    Assembles comprehensive Model Intelligence data from models, configs,
    audited evaluation results, and dataset manifests.
    """
    feat_cols = _load_json(os.path.join(MODELS_DIR, "feature_columns.json"), [
        "from_bank", "to_bank", "amount_received", "receiving_currency",
        "amount_paid", "payment_currency", "payment_format", "hour",
        "day_of_week", "amount_diff", "amount_ratio", "currency_match",
        "same_bank", "sender_transaction_count", "sender_total_amount",
        "sender_avg_amount", "sender_max_amount", "sender_unique_receivers",
        "sender_unique_banks", "receiver_transaction_count", "receiver_total_amount",
        "receiver_avg_amount", "receiver_max_amount", "receiver_unique_senders",
        "receiver_unique_banks", "seconds_since_previous"
    ])

    lgb_cfg = _load_json(os.path.join(MODELS_DIR, "lightgbm_config.json"), {
        "best_iteration": 242,
        "scale_pos_weight": 1231.80,
        "max_depth": 6,
        "num_leaves": 31,
        "learning_rate": 0.05
    })

    iso_cfg = _load_json(os.path.join(MODELS_DIR, "isolation_forest_config.json"), {
        "n_estimators": 300,
        "max_samples": 256,
        "contamination": "auto"
    })

    phase2_res = _load_json(os.path.join(EVAL_DIR, "phase2_results.json"), {})
    exp_overall = phase2_res.get("experimental_model", {}).get("test_overall", {})
    zero_overall = phase2_res.get("zero_shot_baseline", {}).get("test_overall", {})

    # Compute model SHA-256 hashes
    prod_lgb_sha = _calc_sha256(os.path.join(MODELS_DIR, "muleguard_lightgbm.pkl"))
    prod_enc_sha = _calc_sha256(os.path.join(MODELS_DIR, "category_encoders.pkl"))
    prod_iso_sha = _calc_sha256(os.path.join(MODELS_DIR, "muleguard_isolation_forest.pkl"))
    exp_lgb_sha = _calc_sha256(os.path.join(EVAL_DIR, "artifacts", "experimental_lightgbm.pkl"))
    shap_sha = _calc_sha256(os.path.join(MODELS_DIR, "shap_explainer.pkl"))

    # Feature descriptions and groupings
    feature_meta = {
        "currency_match": {
            "category": "Transaction Attributes",
            "desc": "Binary indicator whether originating and destination currencies match (FX flag)",
            "gain_rank": 1,
            "gain_pct": 53.64,
            "splits": 8,
            "fusion": True
        },
        "amount_paid": {
            "category": "Transaction Attributes",
            "desc": "Monetary transfer amount debited from sender in originating currency",
            "gain_rank": 2,
            "gain_pct": 7.18,
            "splits": 39,
            "fusion": True
        },
        "receiver_unique_senders": {
            "category": "Receiver Behavior",
            "desc": "Cumulative count of distinct originating accounts transferring into this receiver",
            "gain_rank": 3,
            "gain_pct": 5.32,
            "splits": 9,
            "fusion": True
        },
        "from_bank": {
            "category": "Transaction Attributes",
            "desc": "Originating institutional identifier / bank routing domain (categorical)",
            "gain_rank": 4,
            "gain_pct": 3.39,
            "splits": 7,
            "fusion": False
        },
        "sender_transaction_count": {
            "category": "Sender Behavior",
            "desc": "Cumulative point-in-time outbound transaction velocity of sender account",
            "gain_rank": 5,
            "gain_pct": 1.69,
            "splits": 16,
            "fusion": True
        },
        "seconds_since_previous": {
            "category": "Temporal Behavior",
            "desc": "Elapsed seconds since the sender account's immediately preceding transaction",
            "gain_rank": 6,
            "gain_pct": 0.91,
            "splits": 20,
            "fusion": True
        },
        "sender_avg_amount": {
            "category": "Sender Behavior",
            "desc": "Point-in-time historical mean transaction value transferred by sender",
            "gain_rank": 7,
            "gain_pct": 0.87,
            "splits": 13,
            "fusion": False
        },
        "receiver_unique_banks": {
            "category": "Receiver Behavior",
            "desc": "Number of distinct banking institutions that have transferred funds to receiver",
            "gain_rank": 8,
            "gain_pct": 0.87,
            "splits": 10,
            "fusion": False
        },
        "receiver_transaction_count": {
            "category": "Receiver Behavior",
            "desc": "Cumulative point-in-time inbound transfer frequency to destination account",
            "gain_rank": 9,
            "gain_pct": 0.82,
            "splits": 15,
            "fusion": True
        },
        "sender_unique_receivers": {
            "category": "Sender Behavior",
            "desc": "Number of distinct counterparties funded by sender (fan-out dispersion)",
            "gain_rank": 10,
            "gain_pct": 0.79,
            "splits": 13,
            "fusion": True
        },
        "receiver_max_amount": {
            "category": "Receiver Behavior",
            "desc": "Historical single-transaction peak amount received by destination account",
            "gain_rank": 11,
            "gain_pct": 0.32,
            "splits": 16,
            "fusion": False
        },
        "sender_total_amount": {
            "category": "Sender Behavior",
            "desc": "Cumulative outbound transaction volume dispatched by sender account",
            "gain_rank": 12,
            "gain_pct": 0.29,
            "splits": 5,
            "fusion": True
        },
        "hour": {
            "category": "Temporal Behavior",
            "desc": "Hour of transaction execution [0-23] (cyclic temporal feature)",
            "gain_rank": 13,
            "gain_pct": 0.14,
            "splits": 13,
            "fusion": False
        },
        "amount_received": {
            "category": "Transaction Attributes",
            "desc": "Monetary transfer value credited to destination account in receiving currency",
            "gain_rank": 14,
            "gain_pct": 0.11,
            "splits": 11,
            "fusion": False
        },
        "payment_format": {
            "category": "Transaction Attributes",
            "desc": "Payment mechanism rail (ACH, Wire, Cheque, Cash, Credit Card, Reinvestment)",
            "gain_rank": 15,
            "gain_pct": 0.10,
            "splits": 3,
            "fusion": True
        },
        "day_of_week": {
            "category": "Temporal Behavior",
            "desc": "Day of the week [0=Monday, 6=Sunday] (weekly cyclic pattern)",
            "gain_rank": 16,
            "gain_pct": 0.10,
            "splits": 5,
            "fusion": False
        },
        "receiver_avg_amount": {
            "category": "Receiver Behavior",
            "desc": "Historical mean transaction value received by destination account",
            "gain_rank": 17,
            "gain_pct": 0.08,
            "splits": 11,
            "fusion": False
        },
        "receiver_total_amount": {
            "category": "Receiver Behavior",
            "desc": "Cumulative volume received by destination account across prior transactions",
            "gain_rank": 18,
            "gain_pct": 0.04,
            "splits": 10,
            "fusion": True
        },
        "sender_unique_banks": {
            "category": "Sender Behavior",
            "desc": "Number of distinct destination institutions funded by sender account",
            "gain_rank": 19,
            "gain_pct": 0.03,
            "splits": 4,
            "fusion": False
        },
        "same_bank": {
            "category": "Transaction Attributes",
            "desc": "Binary indicator if transaction is internal book transfer within same bank",
            "gain_rank": 20,
            "gain_pct": 0.03,
            "splits": 5,
            "fusion": False
        },
        "to_bank": {
            "category": "Transaction Attributes",
            "desc": "Destination institutional identifier / beneficiary bank routing domain",
            "gain_rank": 21,
            "gain_pct": 0.01,
            "splits": 3,
            "fusion": False
        },
        "sender_max_amount": {
            "category": "Sender Behavior",
            "desc": "Historical single-transaction peak amount initiated by sender account",
            "gain_rank": 22,
            "gain_pct": 0.01,
            "splits": 3,
            "fusion": False
        },
        "payment_currency": {
            "category": "Transaction Attributes",
            "desc": "ISO currency code of the originating debit account (categorical)",
            "gain_rank": 23,
            "gain_pct": 0.003,
            "splits": 2,
            "fusion": False
        },
        "amount_ratio": {
            "category": "Transaction Attributes",
            "desc": "Ratio of amount received to amount paid (indicative of FX commission cut)",
            "gain_rank": 24,
            "gain_pct": 0.002,
            "splits": 7,
            "fusion": False
        },
        "receiving_currency": {
            "category": "Transaction Attributes",
            "desc": "ISO currency code of the destination credit account (categorical)",
            "gain_rank": 25,
            "gain_pct": 0.0,
            "splits": 0,
            "fusion": False
        },
        "amount_diff": {
            "category": "Transaction Attributes",
            "desc": "Absolute discrepancy between paid amount and received amount",
            "gain_rank": 26,
            "gain_pct": 0.0,
            "splits": 0,
            "fusion": False
        }
    }

    feature_table = []
    for col in feat_cols:
        meta = feature_meta.get(col, {
            "category": "Transaction Attributes",
            "desc": "Engineered tabular feature",
            "gain_rank": 26,
            "gain_pct": 0.0,
            "splits": 0,
            "fusion": False
        })
        feature_table.append({
            "name": col,
            "category": meta["category"],
            "description": meta["desc"],
            "gain_rank": meta["gain_rank"],
            "gain_pct": meta["gain_pct"],
            "splits": meta["splits"],
            "data_source": "Point-in-Time Streaming State Engine",
            "used_in_lightgbm": True,
            "used_in_fusion": meta["fusion"]
        })

    # Sort by gain rank
    feature_table.sort(key=lambda x: x["gain_rank"])

    # Audited alert budget data
    alert_budgets = [
        {
            "budget": 100,
            "tp": 60,
            "fp": 40,
            "precision": 0.60,
            "recall": 0.0493,
            "tier": "Rapid Strike Queue",
            "desc": "6 out of 10 alerts confirmed money laundering. Zero analyst fatigue."
        },
        {
            "budget": 500,
            "tp": 293,
            "fp": 207,
            "precision": 0.586,
            "recall": 0.2408,
            "tier": "Standard Daily Triage",
            "desc": "Captures nearly 1 in 4 laundering cases with 58.6% precision."
        },
        {
            "budget": 1000,
            "tp": 589,
            "fp": 411,
            "precision": 0.589,
            "recall": 0.4840,
            "tier": "Optimal Operational Queue",
            "desc": "Captures ~50% of all laundering cases with ~3 reviews per confirmed case."
        },
        {
            "budget": 2500,
            "tp": 624,
            "fp": 1876,
            "precision": 0.2496,
            "recall": 0.5127,
            "tier": "Secondary Review Queue",
            "desc": "Captures 51.3% of illicit cases. Precision drops to ~25%."
        },
        {
            "budget": 5000,
            "tp": 643,
            "fp": 4357,
            "precision": 0.1286,
            "recall": 0.5283,
            "tier": "Extended Regulatory Scan",
            "desc": "Captures 52.8% of cases with 87% false positives."
        },
        {
            "budget": 10000,
            "tp": 680,
            "fp": 9320,
            "precision": 0.0680,
            "recall": 0.5588,
            "tier": "Batch Audit Queue",
            "desc": "Captures 55.9% of cases with 93% false positives."
        },
        {
            "budget": 25000,
            "tp": 857,
            "fp": 24143,
            "precision": 0.0343,
            "recall": 0.7042,
            "tier": "Deep Forensic Scan",
            "desc": "Captures 70.4% of cases with 96.6% false positives."
        },
        {
            "budget": 50000,
            "tp": 1139,
            "fp": 48861,
            "precision": 0.0228,
            "recall": 0.9359,
            "tier": "Full Regulatory Audit Threshold",
            "desc": "Near-total completeness (93.6% recall), high investigator burden."
        }
    ]

    return {
        "status": "success",
        "production_model": {
            "model_name": "MuleGuard LightGBM Production Classifier",
            "model_file": "models/muleguard_lightgbm.pkl",
            "algorithm": "Gradient Boosted Decision Trees (LightGBM 4.5.0)",
            "num_features": 26,
            "best_iteration": lgb_cfg.get("best_iteration", 242),
            "scale_pos_weight": lgb_cfg.get("scale_pos_weight", 1231.80),
            "max_depth": lgb_cfg.get("max_depth", 6),
            "num_leaves": lgb_cfg.get("num_leaves", 31),
            "learning_rate": lgb_cfg.get("learning_rate", 0.05),
            "objective": "binary",
            "sha256": prod_lgb_sha,
            "encoders_file": "models/category_encoders.pkl",
            "encoders_sha256": prod_enc_sha,
            "isolation_forest_file": "models/muleguard_isolation_forest.pkl",
            "isolation_forest_sha256": prod_iso_sha,
            "shap_explainer_file": "models/shap_explainer.pkl",
            "shap_explainer_sha256": shap_sha,
            "status": "FROZEN (Production Serving)",
            "audit_date": "October 20, 2026",
            "role": "Real-time Transaction Inference & Statistical Scoring"
        },
        "secondary_model": {
            "model_name": "MuleGuard Isolation Forest Anomaly Detector",
            "model_file": "models/muleguard_isolation_forest.pkl",
            "algorithm": "Isolation Forest (scikit-learn 1.6.1)",
            "n_estimators": iso_cfg.get("n_estimators", 300),
            "max_samples": iso_cfg.get("max_samples", 256),
            "contamination": iso_cfg.get("contamination", "auto"),
            "sha256": prod_iso_sha,
            "status": "FROZEN (Auxiliary Unsupervised Scoring)",
            "score_semantics": "Scikit-learn decision_function [-0.5, +0.5]: negative scores denote isolated/outlier transactions; positive scores denote high-density normal flow"
        },
        "experimental_model": {
            "model_name": "Phase 2 Experimental LightGBM (HI-Small Benchmark)",
            "model_file": "evaluation/amlsim_evaluation/artifacts/experimental_lightgbm.pkl",
            "algorithm": "LightGBM GBDT (Leakage-Free Point-in-Time Pipeline)",
            "num_features": 26,
            "best_iteration": 4,
            "validation_calibrated_threshold": 0.97,
            "training_rows": 3731672,
            "validation_rows": 978073,
            "test_rows": 368600,
            "sha256": exp_lgb_sha,
            "status": "OFFLINE EXPERIMENTAL BENCHMARK",
            "audit_date": "October 20, 2026 (Audited by Independent Verifier)"
        },
        "performance_metrics": {
            "experimental_lightgbm": {
                "roc_auc": exp_overall.get("roc_auc", 0.892463),
                "pr_auc": exp_overall.get("pr_auc", 0.021447),
                "precision": exp_overall.get("precision", 0.022026),
                "recall": exp_overall.get("recall", 0.944125),
                "f1": exp_overall.get("f1", 0.043047),
                "specificity": exp_overall.get("specificity", 0.861134),
                "fpr": round(1.0 - exp_overall.get("specificity", 0.861134), 6),
                "mcc": exp_overall.get("mcc", 0.132527),
                "threshold": 0.97,
                "confusion_matrix": exp_overall.get("confusion_matrix", {
                    "tp": 1149,
                    "fp": 51017,
                    "tn": 316366,
                    "fn": 68
                })
            },
            "zero_shot_baseline": {
                "roc_auc": zero_overall.get("roc_auc", 0.292487),
                "pr_auc": zero_overall.get("pr_auc", 0.002792),
                "precision": zero_overall.get("precision", 0.003376),
                "recall": zero_overall.get("recall", 0.016434),
                "f1": zero_overall.get("f1", 0.005601),
                "specificity": zero_overall.get("specificity", 0.983930),
                "fpr": round(1.0 - zero_overall.get("specificity", 0.983930), 6),
                "mcc": zero_overall.get("mcc", 0.000166),
                "threshold": 0.98,
                "confusion_matrix": zero_overall.get("confusion_matrix", {
                    "tp": 20,
                    "fp": 5904,
                    "tn": 361479,
                    "fn": 1197
                })
            }
        },
        "features": feature_table,
        "feature_count": len(feature_table),
        "risk_fusion": {
            "weights": {
                "model": 0.50,
                "graph": 0.25,
                "behavior": 0.15,
                "rule": 0.10
            },
            "formula": "FusedScore = 0.50 * S_model + 0.25 * S_graph + 0.15 * S_behavior + 0.10 * S_rule",
            "operational_tiers": {
                "Critical": {
                    "range": ">= 0.85",
                    "action": "Immediate freeze & Tier 1 SAR escalation",
                    "sla": "< 2 hours"
                },
                "High": {
                    "range": "0.65 - 0.84",
                    "action": "Priority compliance investigation queue",
                    "sla": "< 24 hours"
                },
                "Medium": {
                    "range": "0.40 - 0.64",
                    "action": "Enhanced monitoring & behavioral alert queue",
                    "sla": "< 72 hours"
                },
                "Low": {
                    "range": "< 0.40",
                    "action": "Cleared / automated background monitoring",
                    "sla": "Standard audit trail"
                }
            },
            "score_semantics": {
                "supervised_risk_score": "Calibrated probability [0.0, 1.0]. Values >= 0.95 denote statistically anomalous transfer attributes.",
                "isolation_forest_score": "Unscaled tree isolation decision distance [-0.5, +0.5]. Negative values represent structural outliers.",
                "fused_priority_score": "Composite multi-source risk metric [0.0, 1.0] used for deterministic daily investigator triage.",
                "downstream_graph_separation": "Graph typologies (cycles, mule aggregation, smurfing pass-through) are computed via NetworkX and ingested into Risk Fusion. They are STRICTLY NOT part of the 26-feature LightGBM tabular vector."
            }
        },
        "alert_budgets": alert_budgets,
        "dataset_info": {
            "name": "IBM Transactions for AML (HI-Small_Trans.csv)",
            "total_transactions": 5078345,
            "illicit_transactions": 5177,
            "legitimate_transactions": 5073168,
            "illicit_prevalence_pct": 0.1019,
            "time_period": "September 1 - September 18, 2022",
            "num_currencies": 15,
            "currencies": [
                "US Dollar", "Euro", "UK Pound", "Canadian Dollar", "Swiss Franc",
                "Australian Dollar", "Japanese Yen", "Yuan", "Bitcoin", "Rupee",
                "Ruble", "Mexican Peso", "Saudi Riyal", "Brazilian Real", "Turkish Lira"
            ],
            "num_payment_formats": 7,
            "payment_formats": ["ACH", "Wire", "Credit Card", "Cheque", "Cash", "Reinvestment", "Cross-Border"],
            "dataset_separation": {
                "full_benchmark": "5,078,345 transactions (offline training and test evaluation split).",
                "showcase_subset": "1,000 transactions published to Supabase for desktop interactive benchmark exploration.",
                "synthetic_demo": "500 transactions, 102 accounts, 25 alerts for standard FinGuard live mock simulation."
            },
            "provenance_statement": "The full IBM AML dataset comprises 5,078,345 transactions. A 1,000-row model-prioritized subset was published to Supabase for demonstration purposes. Model evaluation metrics are strictly computed on the held-out 368,600-row test split, NOT on the showcase subset."
        },
        "explainability_and_limitations": {
            "shap_explainer": "TreeSHAP (TreeExplainer v0.46.0) pre-fitted on LightGBM tree ensemble",
            "top_gain_features": [
                {"feature": "currency_match", "gain_pct": 53.64, "description": "Cross-currency conversion anomaly (FX laundering)"},
                {"feature": "amount_paid", "gain_pct": 7.18, "description": "Debited transfer volume magnitude"},
                {"feature": "receiver_unique_senders", "gain_pct": 5.32, "description": "Counterparty fan-in concentration (mule funnel)"},
                {"feature": "from_bank", "gain_pct": 3.39, "description": "Originating institutional profile"},
                {"feature": "sender_transaction_count", "gain_pct": 1.69, "description": "Historical account transaction velocity"},
                {"feature": "seconds_since_previous", "gain_pct": 0.91, "description": "Rapid burst velocity between transactions"},
                {"feature": "sender_avg_amount", "gain_pct": 0.87, "description": "Departure from sender historical average amount"}
            ],
            "limitations": [
                {
                    "title": "Severe Class Imbalance (0.102%)",
                    "detail": "Only 1 in 981 transactions is illicit. While Recall reaches 94.4%, absolute Precision at 0.97 cutoff is 2.20%, yielding 51,017 false positives on the full test set. Capacity-bounded alert triage is mandatory."
                },
                {
                    "title": "Cold-Start Account Velocity Degradation",
                    "detail": "Accounts with zero historical transfer records have unpopulated aggregations (sender_tx_count_prior = 0). The model relies solely on single-transaction attributes and unsupervised anomaly score until history accumulates."
                },
                {
                    "title": "Synthetic-to-Real Domain Gap",
                    "detail": "AMLSim agent simulations capture known topological structuring and fan-in patterns, but may not reflect adversarial zero-day tactics such as novel decentralized crypto-bridges or mixed-currency structuring."
                },
                {
                    "title": "Batch Temporal Aggregation Boundaries",
                    "detail": "Point-in-time state is partitioned at 1-minute batch intervals. Ultra-high-frequency automated micro-structuring within the same clock minute requires streaming event-time complex event processing."
                },
                {
                    "title": "Human-in-the-Loop Regulatory Mandate",
                    "detail": "Model scores and priority tiers accelerate analyst review by up to 58.9% precision at top 1,000 capacity, but cannot autonomously generate or file Suspicious Activity Reports (SARs) without licensed human compliance adjudication."
                }
            ]
        }
    }
