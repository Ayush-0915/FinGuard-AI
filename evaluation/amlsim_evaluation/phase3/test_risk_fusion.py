"""
FinGuard AI — Unit Tests for RiskFusionEngine (Phase 3)
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from risk_fusion import RiskFusionEngine

class TestRiskFusionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RiskFusionEngine(weights={"model": 0.5, "graph": 0.25, "behavior": 0.15, "rule": 0.10})

    def test_01_weight_normalization(self):
        """Tests that weights properly normalize to 1.0."""
        e = RiskFusionEngine(weights={"model": 2.0, "graph": 1.0, "behavior": 1.0, "rule": 0.0})
        self.assertAlmostEqual(sum(e.weights.values()), 1.0)
        self.assertAlmostEqual(e.weights["model"], 0.50)
        self.assertAlmostEqual(e.weights["graph"], 0.25)

    def test_02_behavioral_score_computation(self):
        """Tests score calculation from rapid velocity and counterparty fan-in."""
        features = {
            "seconds_since_previous": 45.0, # Rapid burst (< 60s) -> +0.40
            "receiver_unique_senders": 12,  # High fan-in (>= 10)   -> +0.35
            "sender_unique_receivers": 1    # Low fan-out
        }
        b_score = self.engine.compute_behavioral_score(features)
        self.assertAlmostEqual(b_score, 0.75, places=2)

    def test_03_rule_score_computation(self):
        """Tests rule scoring for high amounts, currency mismatch, and payment format."""
        tx = {
            "amount": 75000.0, # >= 50k -> +0.50
            "payment_format": "Wire" # Wire -> +0.15
        }
        features = {
            "currency_match": 0, # Mismatch -> +0.30
            "same_bank": 1
        }
        r_score = self.engine.compute_rule_score(tx, features)
        self.assertAlmostEqual(r_score, 0.95, places=2)

    def test_04_graph_score_combination(self):
        """Tests diminishing returns combination of graph pattern severities."""
        patterns = [
            {"typology": "FAN_IN", "severity_score": 0.80},
            {"typology": "CIRCULAR_FLOW", "severity_score": 0.85}
        ]
        g_score = self.engine.compute_graph_score(patterns)
        # 1 - (1 - 0.80)*(1 - 0.85) = 1 - 0.20*0.15 = 1 - 0.03 = 0.97
        self.assertAlmostEqual(g_score, 0.97, places=2)

    def test_05_dynamic_renormalization_missing_graph(self):
        """Tests that missing graph patterns renormalize remaining weights dynamically."""
        tx = {"amount": 500.0}
        features = {"seconds_since_previous": 999999.0}
        
        # When graph_patterns is None, graph weight is excluded
        res = self.engine.fuse_risk(
            model_prob=0.90,
            transaction=tx,
            features=features,
            graph_patterns=None
        )

        self.assertNotIn("graph", res["active_weights"])
        self.assertAlmostEqual(sum(res["active_weights"].values()), 1.0)
        # raw probability and fused score remain distinct
        self.assertEqual(res["raw_model_probability"], 0.90)
        self.assertTrue(0.0 <= res["fused_priority_score"] <= 1.0)

if __name__ == "__main__":
    unittest.main()
