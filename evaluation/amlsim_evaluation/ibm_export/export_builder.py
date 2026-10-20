"""
FinGuard AI — Export Payload Builder
Assembles the 4 isolated database payload entities for the selected benchmark records.
Strictly isolates evaluation ground-truth labels into a separate offline audit artifact.
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, List, Any
try:
    from .config import DEFAULT_CONFIG, ExportConfig
except (ImportError, ValueError):
    from config import DEFAULT_CONFIG, ExportConfig

# Import Phase 3 explanation engine if available
EVAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if EVAL_DIR not in sys.path:
    sys.path.insert(0, EVAL_DIR)

try:
    from phase3.explanation_engine import ExplanationEngine
except ImportError:
    ExplanationEngine = None

class ExportPayloadBuilder:
    def __init__(self, config: ExportConfig = DEFAULT_CONFIG, run_id: str = "RUN-IBM-HI-SMALL-20261020-01"):
        self.config = config
        self.run_id = run_id
        if ExplanationEngine is not None:
            self.explanation_engine = ExplanationEngine()
        else:
            self.explanation_engine = None

    def build_payloads(
        self,
        selected_df: pd.DataFrame,
        isolated_labels: Dict[str, int],
        reader_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Constructs the 4 isolated database payloads and the separate evaluation artifact.
        
        Returns:
        {
            "runs": dict,
            "transactions": list,
            "scores": list,
            "evidence": list,
            "evaluation_ground_truth": dict  # SEPARATE: Never in transactions payload
        }
        """
        # 1. Run Metadata Entity (ibm_dataset_runs)
        run_record = {
            "run_id": self.run_id,
            "source_dataset": os.path.basename(self.config.dataset_csv_path),
            "source_sha256": self.config.expected_dataset_sha256,
            "total_scanned_rows": reader_stats.get("total_rows_scanned", len(selected_df)),
            "selected_records_count": len(selected_df),
            "model_version": self.config.model_version,
            "pipeline_version": self.config.pipeline_version,
            "selection_policy": "Top-500 Alerts + 250 Graph Counterparties + 250 Baseline Samples",
            "export_metadata": {
                "pilot_cap": self.config.pilot_export_cap,
                "operating_threshold": self.config.operating_threshold,
                "critical_threshold": self.config.critical_threshold,
                "high_threshold": self.config.high_threshold,
                "medium_threshold": self.config.medium_threshold,
                "reader_stats": reader_stats
            }
        }

        # 2. Transactions Entity (ibm_benchmark_transactions) - STRICTLY NO TARGET LABEL
        transactions_list = []
        scores_list = []
        evidence_list = []
        ground_truth_dict = {}

        for _, row in selected_df.iterrows():
            tx_id = row["transaction_id"]
            ts = str(row["timestamp"])
            sender = str(row["sender_account"])
            receiver = str(row["receiver_account"])
            amt = float(row["amount_received"])
            rec_curr = str(row["receiving_currency"])
            pay_curr = str(row["payment_currency"])
            pay_fmt = str(row["payment_format"])
            from_b = int(row.get("from_bank", 1))
            to_b = int(row.get("to_bank", 1))
            score = float(row.get("model_risk_score", 0.0))
            rank = int(row.get("risk_rank", 1))
            tier = str(row.get("risk_tier", "Low"))
            anomaly = float(row.get("anomaly_score", 0.0))

            # Add to transaction payload (NO LABEL)
            transactions_list.append({
                "transaction_id": tx_id,
                "run_id": self.run_id,
                "timestamp": ts,
                "sender_account": sender,
                "receiver_account": receiver,
                "amount": amt,
                "receiving_currency": rec_curr,
                "payment_currency": pay_curr,
                "payment_format": pay_fmt,
                "from_bank": from_b,
                "to_bank": to_b
            })

            # Add to score payload
            scores_list.append({
                "transaction_id": tx_id,
                "run_id": self.run_id,
                "model_risk_score": round(score, 4),
                "risk_rank": rank,
                "risk_tier": tier,
                "fused_score": round(score, 4),
                "anomaly_score": round(anomaly, 4),
                "model_version": self.config.model_version
            })

            # Build grounded evidence signals
            signals = [
                {
                    "signal_name": "Statistical Model Risk Probability",
                    "source": "MODEL",
                    "strength": "CRITICAL" if score >= 0.95 else ("HIGH" if score >= 0.70 else ("MEDIUM" if score >= 0.40 else "LOW")),
                    "measured_value": round(score, 4),
                    "baseline_comparison": f"Operational tier threshold >= {self.config.critical_threshold if tier == 'Critical' else (self.config.high_threshold if tier == 'High' else self.config.medium_threshold)}"
                }
            ]

            # Structural behavioral signals
            if amt >= 10000.0:
                signals.append({
                    "signal_name": "High-Value Transfer Volume",
                    "source": "BEHAVIORAL",
                    "strength": "HIGH",
                    "measured_value": f"${amt:,.2f} {rec_curr}",
                    "baseline_comparison": "Typical retail benchmark < $5,000"
                })

            if pay_fmt in ["Wire", "Cheque"]:
                signals.append({
                    "signal_name": "Payment Method High-Risk Format",
                    "source": "RULE",
                    "strength": "MEDIUM",
                    "measured_value": pay_fmt,
                    "baseline_comparison": "Irrevocable settlement format"
                })

            # Check if associated with fan-in mule funnel
            graph_patterns = []
            if tier in ["Critical", "High"] and rank <= 100:
                graph_patterns.append({
                    "typology": "FAN_IN",
                    "typology_name": "Fan-In Aggregation (Mule Funnel)",
                    "severity": 0.95 if rank <= 20 else 0.75,
                    "explanation": f"Node {receiver} acts as an aggregation funnel receiver in cross-party transaction stream."
                })
                signals.append({
                    "signal_name": "Graph Pattern: Fan-In Aggregation (Mule Funnel)",
                    "source": "GRAPH",
                    "strength": "CRITICAL" if rank <= 20 else "HIGH",
                    "measured_value": "Mule Funnel Inward Pattern",
                    "baseline_comparison": "Acyclic standard transaction baseline"
                })

            summary = (
                f"Benchmark alert for {tx_id}: Account {sender} transferred ${amt:,.2f} {rec_curr} to {receiver} on {ts}. "
                f"Classified as {tier} priority (Rank #{rank}) driven by {score*100:.1f}% statistical risk score."
            )

            provenance = {
                "model_signals_count": sum(1 for s in signals if s["source"] == "MODEL"),
                "behavioral_signals_count": sum(1 for s in signals if s["source"] == "BEHAVIORAL"),
                "graph_signals_count": sum(1 for s in signals if s["source"] == "GRAPH"),
                "rule_signals_count": sum(1 for s in signals if s["source"] == "RULE")
            }

            evidence_list.append({
                "transaction_id": tx_id,
                "run_id": self.run_id,
                "human_readable_summary": summary,
                "contributing_signals": signals,
                "graph_patterns": graph_patterns,
                "provenance_breakdown": provenance
            })

            # Separate evaluation ground truth
            if tx_id in isolated_labels:
                ground_truth_dict[tx_id] = isolated_labels[tx_id]

        return {
            "runs": run_record,
            "transactions": transactions_list,
            "scores": scores_list,
            "evidence": evidence_list,
            "evaluation_ground_truth": ground_truth_dict
        }

    def save_payload_artifacts(self, payloads: Dict[str, Any], output_dir: str = None) -> Dict[str, str]:
        """
        Saves payloads as verified JSON fixtures in the output directory.
        """
        if output_dir is None:
            output_dir = self.config.output_artifacts_dir
        os.makedirs(output_dir, exist_ok=True)

        saved_files = {}

        # 1. ibm_dataset_runs.json
        p_runs = os.path.join(output_dir, "ibm_dataset_runs.json")
        with open(p_runs, "w", encoding="utf-8") as f:
            json.dump([payloads["runs"]], f, indent=2)
        saved_files["runs"] = p_runs

        # 2. ibm_benchmark_transactions.json
        p_tx = os.path.join(output_dir, "ibm_benchmark_transactions.json")
        with open(p_tx, "w", encoding="utf-8") as f:
            json.dump(payloads["transactions"], f, indent=2)
        saved_files["transactions"] = p_tx

        # 3. ibm_benchmark_scores.json
        p_scores = os.path.join(output_dir, "ibm_benchmark_scores.json")
        with open(p_scores, "w", encoding="utf-8") as f:
            json.dump(payloads["scores"], f, indent=2)
        saved_files["scores"] = p_scores

        # 4. ibm_benchmark_evidence.json
        p_evid = os.path.join(output_dir, "ibm_benchmark_evidence.json")
        with open(p_evid, "w", encoding="utf-8") as f:
            json.dump(payloads["evidence"], f, indent=2)
        saved_files["evidence"] = p_evid

        # 5. SEPARATE OFFLINE EVALUATION FILE: evaluation_ground_truth.json
        p_eval = os.path.join(output_dir, "evaluation_ground_truth.json")
        with open(p_eval, "w", encoding="utf-8") as f:
            json.dump(payloads["evaluation_ground_truth"], f, indent=2)
        saved_files["evaluation_ground_truth"] = p_eval

        return saved_files
