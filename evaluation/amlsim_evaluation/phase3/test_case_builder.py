"""
FinGuard AI — Unit Tests for CaseBuilder (Phase 3)
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from case_builder import CaseBuilder, DISCLAIMER_TEXT

class TestCaseBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = CaseBuilder(default_status="Open")

    def test_01_build_case_success(self):
        """Tests end-to-end case construction from multiple alerts."""
        alerts = [
            {
                "transaction_id": "TX_1",
                "timestamp": "2022/09/01 10:00",
                "sender_account": "ACC_MULE_1",
                "receiver_account": "ACC_TARGET",
                "amount": 5000.0,
                "currency": "US Dollar",
                "model_risk_score": 0.965,
                "risk_rank": 12,
                "risk_tier": "High"
            },
            {
                "transaction_id": "TX_2",
                "timestamp": "2022/09/01 10:30",
                "sender_account": "ACC_MULE_2",
                "receiver_account": "ACC_TARGET",
                "amount": 7500.0,
                "currency": "US Dollar",
                "model_risk_score": 0.994,
                "risk_rank": 3,
                "risk_tier": "Critical"
            }
        ]
        graph_patterns = [
            {
                "typology": "FAN_IN",
                "typology_name": "Fan-In Aggregation (Mule Funnel)",
                "severity_score": 0.92,
                "confidence_level": "HIGH",
                "investigator_explanation": "ACC_TARGET receives funneling transfers."
            }
        ]

        case = self.builder.build_case_from_alerts(
            primary_account="ACC_TARGET",
            alerts=alerts,
            graph_patterns=graph_patterns
        )

        self.assertIn("CASE-", case["case_id"])
        self.assertEqual(case["primary_account"], "ACC_TARGET")
        self.assertEqual(case["priority_tier"], "Critical") # Aggregates to highest tier
        self.assertEqual(case["best_alert_rank"], 3)
        self.assertEqual(case["total_suspicious_volume"], 12500.0)
        self.assertEqual(case["alert_count"], 2)
        self.assertEqual(len(case["related_accounts"]), 2)
        self.assertIn("ACC_MULE_1", case["related_accounts"])
        self.assertIn("ACC_MULE_2", case["related_accounts"])
        self.assertEqual(len(case["activity_timeline"]), 2)
        self.assertIn("Fan-In Aggregation", case["investigation_summary"])
        self.assertEqual(case["compliance_disclaimer"], DISCLAIMER_TEXT)

    def test_02_empty_alerts_error(self):
        """Tests that constructing a case with zero alerts raises ValueError."""
        with self.assertRaises(ValueError):
            self.builder.build_case_from_alerts(primary_account="EMPTY", alerts=[])

if __name__ == "__main__":
    unittest.main()
