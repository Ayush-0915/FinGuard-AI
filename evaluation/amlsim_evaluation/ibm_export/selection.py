"""
FinGuard AI — Deterministic Benchmark Record Selector
Selects a bounded pilot of exactly 1,000 transactions without using ground-truth labels.
Comprises Top-Ranked Alerts, Connected Funnel Counterparties, and Baseline Triage Samples.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Set, Any
try:
    from .config import DEFAULT_CONFIG, ExportConfig
except (ImportError, ValueError):
    from config import DEFAULT_CONFIG, ExportConfig

class RecordSelector:
    def __init__(self, config: ExportConfig = DEFAULT_CONFIG):
        self.config = config
        self.pilot_cap = config.pilot_export_cap
        self.top_alerts_quota = config.top_alerts_quota
        self.connected_quota = config.connected_counterparties_quota
        self.baseline_quota = config.baseline_samples_quota

    def select_bounded_records(
        self,
        transactions_df: pd.DataFrame,
        scores_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Executes deterministic selection of transactions up to pilot_cap (1,000).
        STRICTLY ZERO USE OF GROUND-TRUTH LAUNDERING LABELS.
        
        Selection Policy:
        1. Top Candidate Alerts (up to 500) sorted by model_risk_score DESC, tie-break by timestamp ASC, transaction_id ASC.
        2. Connected Counterparty Funnel Transactions (up to 250) involving accounts in Top Alerts.
        3. Baseline Triage Samples (up to 250) across High, Medium, Low tiers.
        """
        if len(transactions_df) == 0:
            return pd.DataFrame()

        # Merge transactions with scores
        merged = transactions_df.merge(scores_df, on="transaction_id", how="inner")
        
        # Ensure deterministic sorting
        merged = merged.sort_values(
            by=["model_risk_score", "timestamp", "transaction_id"],
            ascending=[False, True, True]
        ).reset_index(drop=True)

        selected_ids: Set[str] = set()
        selected_rows: List[pd.Series] = []

        # -------------------------------------------------------------
        # TIER 1: Top Candidate Alerts (Quota: 500)
        # -------------------------------------------------------------
        top_candidates = merged.head(self.top_alerts_quota)
        for _, row in top_candidates.iterrows():
            tx_id = row["transaction_id"]
            if tx_id not in selected_ids:
                selected_ids.add(tx_id)
                selected_rows.append(row)

        # Collect accounts from top candidate alerts
        top_accounts = set(top_candidates["sender_account"]).union(set(top_candidates["receiver_account"]))

        # -------------------------------------------------------------
        # TIER 2: Connected Graph Funnel Counterparties (Quota: 250)
        # -------------------------------------------------------------
        remaining = merged[~merged["transaction_id"].isin(selected_ids)]
        
        is_connected = remaining["sender_account"].isin(top_accounts) | remaining["receiver_account"].isin(top_accounts)
        connected_df = remaining[is_connected].sort_values(
            by=["amount_paid", "model_risk_score", "transaction_id"],
            ascending=[False, False, True]
        ).head(self.connected_quota)

        for _, row in connected_df.iterrows():
            tx_id = row["transaction_id"]
            if tx_id not in selected_ids and len(selected_ids) < (self.top_alerts_quota + self.connected_quota):
                selected_ids.add(tx_id)
                selected_rows.append(row)

        # -------------------------------------------------------------
        # TIER 3: Baseline Triage Diversity Samples (Quota: 250)
        # -------------------------------------------------------------
        remaining = merged[~merged["transaction_id"].isin(selected_ids)]
        
        high_samples = remaining[remaining["risk_tier"] == "High"].head(100)
        med_samples = remaining[remaining["risk_tier"] == "Medium"].head(100)
        low_samples = remaining[remaining["risk_tier"] == "Low"].head(50)

        for sub_df in [high_samples, med_samples, low_samples]:
            for _, row in sub_df.iterrows():
                tx_id = row["transaction_id"]
                if tx_id not in selected_ids and len(selected_ids) < self.pilot_cap:
                    selected_ids.add(tx_id)
                    selected_rows.append(row)

        # -------------------------------------------------------------
        # Fill remainder up to pilot_cap if needed
        # -------------------------------------------------------------
        if len(selected_ids) < self.pilot_cap:
            remaining = merged[~merged["transaction_id"].isin(selected_ids)]
            fill_count = self.pilot_cap - len(selected_ids)
            filler = remaining.head(fill_count)
            for _, row in filler.iterrows():
                tx_id = row["transaction_id"]
                if tx_id not in selected_ids:
                    selected_ids.add(tx_id)
                    selected_rows.append(row)

        # Convert back to DataFrame
        final_df = pd.DataFrame(selected_rows)

        # Truncate strictly at pilot_cap
        final_df = final_df.iloc[:self.pilot_cap].copy()

        # Final deterministic ranking
        final_df = final_df.sort_values(
            by=["model_risk_score", "timestamp", "transaction_id"],
            ascending=[False, True, True]
        ).reset_index(drop=True)
        
        final_df["risk_rank"] = np.arange(1, len(final_df) + 1, dtype=int)

        return final_df
