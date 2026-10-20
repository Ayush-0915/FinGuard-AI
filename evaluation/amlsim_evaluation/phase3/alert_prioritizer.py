"""
FinGuard AI — Phase 3: Alert Prioritization Engine
Implements deterministic, budget-aware alert ranking, risk-tier binning,
duplicate alert suppression, and Precision@K / Recall@K evaluation metrics.

Strictly preserves:
- Deterministic ranking with secondary key tie-breaking
- Separation of model probability, risk rank, and rule score
- Configurable alert budgets (Top 100, 500, 1,000, 2,500, 5,000)
- Risk tier assignments: Critical, High, Medium, Low
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics import average_precision_score, precision_score, recall_score

class AlertPrioritizer:
    def __init__(
        self,
        default_budgets: Optional[List[int]] = None,
        tier_thresholds: Optional[Dict[str, float]] = None,
        min_score: float = 0.0,
        max_volume: Optional[int] = None
    ):
        """
        Initializes the Alert Prioritizer.

        Parameters:
        -----------
        default_budgets : list of int, optional
            List of top-K alert budgets (e.g., [100, 500, 1000, 2500, 5000]).
        tier_thresholds : dict of {str: float}, optional
            Threshold cutoffs for assigning risk tiers.
            Default:
              Critical: >= 0.99
              High:     >= 0.95
              Medium:   >= 0.80
              Low:      <  0.80
        min_score : float
            Minimum risk score to be considered for an alert.
        max_volume : int, optional
            Hard cap on maximum alerts to emit.
        """
        self.budgets = default_budgets or [100, 500, 1000, 2500, 5000]
        self.tier_thresholds = tier_thresholds or {
            "Critical": 0.99,
            "High": 0.95,
            "Medium": 0.80,
            "Low": 0.0
        }
        self.min_score = min_score
        self.max_volume = max_volume

    def assign_tier(self, score: float) -> str:
        """Assigns a discrete risk tier based on score."""
        if score >= self.tier_thresholds.get("Critical", 0.99):
            return "Critical"
        elif score >= self.tier_thresholds.get("High", 0.95):
            return "High"
        elif score >= self.tier_thresholds.get("Medium", 0.80):
            return "Medium"
        else:
            return "Low"

    def rank_alerts(
        self,
        records_df: pd.DataFrame,
        score_column: str = "model_probability",
        id_column: str = "transaction_id",
        time_column: str = "timestamp",
        deduplicate: bool = True
    ) -> pd.DataFrame:
        """
        Deterministically ranks transactions into prioritized alerts.
        
        Sorting rule:
          1. -score (descending)
          2. timestamp (ascending)
          3. transaction_id (ascending)
        
        This guarantees deterministic, stable tie-breaking across runs.
        """
        if len(records_df) == 0:
            cols = list(records_df.columns) + ["risk_rank", "risk_tier"]
            return pd.DataFrame(columns=cols)

        df = records_df.copy()

        # Deduplicate on transaction_id if requested
        if deduplicate and id_column in df.columns:
            df = df.drop_duplicates(subset=[id_column], keep="first")

        # Filter by minimum score
        if self.min_score > 0.0:
            df = df[df[score_column] >= self.min_score]

        if len(df) == 0:
            cols = list(df.columns) + ["risk_rank", "risk_tier"]
            return pd.DataFrame(columns=cols)

        # Build stable sorting keys
        # For ties, sort ascending by timestamp and id
        sort_cols = [score_column]
        ascending = [False]

        if time_column in df.columns:
            sort_cols.append(time_column)
            ascending.append(True)

        if id_column in df.columns:
            sort_cols.append(id_column)
            ascending.append(True)

        ranked_df = df.sort_values(by=sort_cols, ascending=ascending).reset_index(drop=True)

        # Assign 1-based risk rank
        ranked_df["risk_rank"] = np.arange(1, len(ranked_df) + 1, dtype=np.int32)

        # Assign risk tier
        ranked_df["risk_tier"] = [self.assign_tier(s) for s in ranked_df[score_column].values]

        # Apply maximum volume cap if specified
        if self.max_volume is not None and len(ranked_df) > self.max_volume:
            ranked_df = ranked_df.iloc[:self.max_volume].copy()

        return ranked_df

    def evaluate_budget_metrics(
        self,
        ranked_df: pd.DataFrame,
        y_true: np.ndarray,
        total_eval_transactions: int,
        score_column: str = "model_probability",
        label_column: str = "is_laundering"
    ) -> Dict[str, Any]:
        """
        Calculates Precision@K, Recall@K, tier distributions, and compliance metrics
        across all configured alert budgets.
        """
        results = {
            "total_evaluated_transactions": int(total_eval_transactions),
            "total_positive_ground_truth": int(y_true.sum()),
            "overall_prevalence_pct": float(y_true.mean() * 100),
            "budget_metrics": {},
            "tier_distribution": {}
        }

        # Overall tier distribution
        if "risk_tier" in ranked_df.columns:
            tier_counts = ranked_df["risk_tier"].value_counts().to_dict()
            results["tier_distribution"] = {k: int(v) for k, v in tier_counts.items()}

        labels = ranked_df[label_column].values if label_column in ranked_df.columns else y_true[:len(ranked_df)]
        total_pos = y_true.sum()

        for k in self.budgets:
            k_eff = min(k, len(ranked_df))
            if k_eff == 0:
                results["budget_metrics"][f"top_{k}"] = {
                    "budget_k": k,
                    "alerts_reviewed": 0,
                    "true_positives": 0,
                    "false_positives": 0,
                    "precision_at_k_pct": 0.0,
                    "recall_at_k_pct": 0.0,
                    "alerts_per_1000_tx": 0.0,
                    "tp_per_100_reviewed": 0.0
                }
                continue

            top_k_labels = labels[:k_eff]
            tp = int(top_k_labels.sum())
            fp = int(k_eff - tp)
            prec = float(tp / k_eff * 100)
            rec = float(tp / total_pos * 100) if total_pos > 0 else 0.0
            alerts_per_1000 = float(k_eff / total_eval_transactions * 1000)
            tp_per_100_reviewed = prec  # identical mathematically to precision %

            results["budget_metrics"][f"top_{k}"] = {
                "budget_k": k,
                "alerts_reviewed": k_eff,
                "true_positives": tp,
                "false_positives": fp,
                "precision_at_k_pct": round(prec, 2),
                "recall_at_k_pct": round(rec, 2),
                "alerts_per_1000_tx": round(alerts_per_1000, 2),
                "tp_per_100_reviewed": round(tp_per_100_reviewed, 2)
            }

        return results
