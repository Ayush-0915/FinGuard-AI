"""
FinGuard AI — Unit Tests for AlertPrioritizer (Phase 3)
"""

import unittest
import numpy as np
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alert_prioritizer import AlertPrioritizer

class TestAlertPrioritizer(unittest.TestCase):
    def setUp(self):
        self.prioritizer = AlertPrioritizer(
            default_budgets=[2, 4, 6],
            tier_thresholds={"Critical": 0.99, "High": 0.95, "Medium": 0.80, "Low": 0.0}
        )

    def create_sample_fixture(self):
        return pd.DataFrame([
            {"transaction_id": "TX_1", "timestamp": "2022/09/01 10:00", "model_probability": 0.995, "is_laundering": 1},
            {"transaction_id": "TX_2", "timestamp": "2022/09/01 10:05", "model_probability": 0.960, "is_laundering": 1},
            {"transaction_id": "TX_3", "timestamp": "2022/09/01 10:10", "model_probability": 0.960, "is_laundering": 0}, # Tie with TX_2
            {"transaction_id": "TX_4", "timestamp": "2022/09/01 10:15", "model_probability": 0.820, "is_laundering": 0},
            {"transaction_id": "TX_5", "timestamp": "2022/09/01 10:20", "model_probability": 0.700, "is_laundering": 0},
            {"transaction_id": "TX_6", "timestamp": "2022/09/01 10:25", "model_probability": 0.500, "is_laundering": 0},
        ])

    def test_deterministic_ranking_and_tie_breaking(self):
        """Tests that identical scores tie-break stably by timestamp and transaction_id."""
        fixture = self.create_sample_fixture()
        ranked = self.prioritizer.rank_alerts(fixture)

        self.assertEqual(len(ranked), 6)
        self.assertEqual(ranked.loc[0, "transaction_id"], "TX_1")
        # TX_2 and TX_3 have same score (0.960), but TX_2 has earlier timestamp (10:05 < 10:10)
        self.assertEqual(ranked.loc[1, "transaction_id"], "TX_2")
        self.assertEqual(ranked.loc[2, "transaction_id"], "TX_3")
        self.assertEqual(list(ranked["risk_rank"].values), [1, 2, 3, 4, 5, 6])

    def test_risk_tier_assignments(self):
        """Tests proper categorization into Critical, High, Medium, Low."""
        fixture = self.create_sample_fixture()
        ranked = self.prioritizer.rank_alerts(fixture)

        self.assertEqual(ranked.loc[0, "risk_tier"], "Critical") # 0.995
        self.assertEqual(ranked.loc[1, "risk_tier"], "High")     # 0.960
        self.assertEqual(ranked.loc[2, "risk_tier"], "High")     # 0.960
        self.assertEqual(ranked.loc[3, "risk_tier"], "Medium")   # 0.820
        self.assertEqual(ranked.loc[4, "risk_tier"], "Low")      # 0.700
        self.assertEqual(ranked.loc[5, "risk_tier"], "Low")      # 0.500

    def test_duplicate_suppression(self):
        """Tests that duplicate transaction IDs are cleanly deduplicated."""
        fixture = self.create_sample_fixture()
        # Add duplicate of TX_1
        dup = pd.concat([fixture, fixture.iloc[[0]]], ignore_index=True)
        ranked = self.prioritizer.rank_alerts(dup, deduplicate=True)
        self.assertEqual(len(ranked), 6)
        self.assertEqual(len(ranked["transaction_id"].unique()), 6)

    def test_precision_recall_at_k(self):
        """Tests accurate mathematical computation of Precision@K and Recall@K."""
        fixture = self.create_sample_fixture()
        ranked = self.prioritizer.rank_alerts(fixture)
        y_true = fixture["is_laundering"].values # Total positives = 2 (TX_1, TX_2)

        metrics = self.prioritizer.evaluate_budget_metrics(
            ranked_df=ranked,
            y_true=y_true,
            total_eval_transactions=100
        )

        # Budget 2: Top 2 has TX_1 (pos) and TX_2 (pos) -> 2 TP out of 2 -> 100% Prec, 100% Recall
        m2 = metrics["budget_metrics"]["top_2"]
        self.assertEqual(m2["true_positives"], 2)
        self.assertEqual(m2["false_positives"], 0)
        self.assertAlmostEqual(m2["precision_at_k_pct"], 100.0)
        self.assertAlmostEqual(m2["recall_at_k_pct"], 100.0)

        # Budget 4: Top 4 has TX_1 (pos), TX_2 (pos), TX_3 (neg), TX_4 (neg) -> 2 TP out of 4 -> 50% Prec, 100% Recall
        m4 = metrics["budget_metrics"]["top_4"]
        self.assertEqual(m4["true_positives"], 2)
        self.assertEqual(m4["false_positives"], 2)
        self.assertAlmostEqual(m4["precision_at_k_pct"], 50.0)
        self.assertAlmostEqual(m4["recall_at_k_pct"], 100.0)

    def test_empty_dataset_handling(self):
        """Tests safe handling of empty inputs."""
        empty_df = pd.DataFrame(columns=["transaction_id", "timestamp", "model_probability"])
        ranked = self.prioritizer.rank_alerts(empty_df)
        self.assertEqual(len(ranked), 0)
        self.assertIn("risk_rank", ranked.columns)
        self.assertIn("risk_tier", ranked.columns)

if __name__ == "__main__":
    unittest.main()
