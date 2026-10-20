"""
FinGuard AI — Unit Tests for ExplanationEngine (Phase 3)
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from explanation_engine import ExplanationEngine

class TestExplanationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ExplanationEngine(high_amount_threshold=10000.0, rapid_velocity_sec=300.0)

    def test_01_full_explanation_generation(self):
        """Tests comprehensive narrative and provenance breakdown."""
        tx = {
            "transaction_id": "TX_TEST_001",
            "timestamp": "2022/09/01 14:30",
            "sender_account": "ACC_SENDER",
            "receiver_account": "ACC_RECEIVER",
            "amount": 25000.0,
            "currency": "US Dollar",
            "payment_format": "Wire",
            "model_probability": 0.992,
            "risk_rank": 5,
            "risk_tier": "Critical"
        }
        features = {
            "currency_match": 0,
            "seconds_since_previous": 45.0, # Rapid burst < 300s
            "receiver_unique_senders": 8,   # Funnel
            "sender_unique_receivers": 1
        }
        graph_patterns = [
            {
                "typology": "FAN_IN",
                "typology_name": "Fan-In Aggregation (Mule Funnel)",
                "severity_score": 0.90,
                "investigator_explanation": "Account ACC_RECEIVER collects from 8 distinct senders."
            }
        ]

        exp = self.engine.generate_explanation(
            transaction=tx,
            features=features,
            model_score=tx["model_probability"],
            risk_rank=tx["risk_rank"],
            risk_tier=tx["risk_tier"],
            graph_patterns=graph_patterns
        )

        self.assertEqual(exp["transaction_id"], "TX_TEST_001")
        self.assertEqual(exp["risk_tier"], "Critical")
        self.assertEqual(exp["risk_rank"], 5)
        self.assertIn("Critical priority (Rank #5)", exp["human_readable_summary"])
        self.assertIn("cross-border currency conversion", exp["human_readable_summary"])

        # Check signal provenance
        sources = {s["source"] for s in exp["contributing_signals"]}
        self.assertIn("MODEL", sources)
        self.assertIn("BEHAVIORAL", sources)
        self.assertIn("GRAPH", sources)
        self.assertIn("RULE", sources)

        # Check provenance counts
        counts = exp["provenance_breakdown"]
        self.assertEqual(counts["model_signals_count"], 1)
        self.assertEqual(counts["behavioral_signals_count"], 3) # currency, velocity, fan-in
        self.assertEqual(counts["graph_signals_count"], 1)
        self.assertEqual(counts["rule_signals_count"], 1) # amount >= 10k

    def test_02_minimal_inputs_handling(self):
        """Tests that explanation functions safely when features or graph signals are absent."""
        tx = {
            "transaction_id": "TX_MINIMAL",
            "timestamp": "2022/09/01 10:00",
            "sender_account": "A",
            "receiver_account": "B",
            "amount": 100.0,
            "currency": "Euro",
            "model_probability": 0.65
        }
        exp = self.engine.generate_explanation(transaction=tx)
        self.assertEqual(exp["transaction_id"], "TX_MINIMAL")
        self.assertEqual(exp["amount"], 100.0)
        self.assertIn("TX_MINIMAL", exp["human_readable_summary"])
        self.assertEqual(len(exp["graph_patterns"]), 0)

if __name__ == "__main__":
    unittest.main()
