"""
FinGuard AI — Unit Tests for GraphIntelligenceEngine (Phase 3)
"""

import unittest
import pandas as pd
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graph_intelligence import GraphIntelligenceEngine

class TestGraphIntelligenceEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GraphIntelligenceEngine(
            fan_in_threshold=3,
            fan_out_threshold=3,
            max_cycle_length=4,
            rapid_movement_window_hours=2.0,
            high_value_multiplier=3.0,
            concentration_threshold=0.85
        )

    def test_01_build_graph(self):
        """Tests node and edge creation in NetworkX graph."""
        df = pd.DataFrame([
            {"Account": "A", "Account.1": "B", "Amount Paid": 100.0, "Timestamp": "2022/09/01 10:00", "transaction_id": "T1"},
            {"Account": "B", "Account.1": "C", "Amount Paid": 200.0, "Timestamp": "2022/09/01 11:00", "transaction_id": "T2"}
        ])
        G = self.engine.build_graph(df)
        self.assertEqual(G.number_of_nodes(), 3)
        self.assertEqual(G.number_of_edges(), 2)
        self.assertTrue(G.has_edge("A", "B"))
        self.assertTrue(G.has_edge("B", "C"))

    def test_02_detect_fan_in(self):
        """Tests mule collection / fan-in where S1, S2, S3 transfer to R."""
        df = pd.DataFrame([
            {"Account": "S1", "Account.1": "R", "Amount Paid": 100.0, "Timestamp": "2022/09/01 10:00", "transaction_id": "T1"},
            {"Account": "S2", "Account.1": "R", "Amount Paid": 150.0, "Timestamp": "2022/09/01 10:05", "transaction_id": "T2"},
            {"Account": "S3", "Account.1": "R", "Amount Paid": 200.0, "Timestamp": "2022/09/01 10:10", "transaction_id": "T3"}
        ])
        G = self.engine.build_graph(df)
        patterns = self.engine.detect_fan_in(G)

        self.assertEqual(len(patterns), 1)
        p = patterns[0]
        self.assertEqual(p["target_account"], "R")
        self.assertEqual(p["statistics"]["unique_senders_count"], 3)
        self.assertEqual(p["statistics"]["total_amount_received"], 450.0)
        self.assertIn("T1", p["involved_transactions"])

    def test_03_detect_fan_out(self):
        """Tests smurfing / fan-out where S transfers to R1, R2, R3."""
        df = pd.DataFrame([
            {"Account": "S", "Account.1": "R1", "Amount Paid": 500.0, "Timestamp": "2022/09/01 10:00", "transaction_id": "T1"},
            {"Account": "S", "Account.1": "R2", "Amount Paid": 500.0, "Timestamp": "2022/09/01 10:02", "transaction_id": "T2"},
            {"Account": "S", "Account.1": "R3", "Amount Paid": 500.0, "Timestamp": "2022/09/01 10:04", "transaction_id": "T3"}
        ])
        G = self.engine.build_graph(df)
        patterns = self.engine.detect_fan_out(G)

        self.assertEqual(len(patterns), 1)
        p = patterns[0]
        self.assertEqual(p["target_account"], "S")
        self.assertEqual(p["statistics"]["unique_receivers_count"], 3)
        self.assertEqual(p["statistics"]["total_amount_sent"], 1500.0)

    def test_04_detect_circular_flow(self):
        """Tests 3-hop directed cycle: A -> B -> C -> A."""
        df = pd.DataFrame([
            {"Account": "A", "Account.1": "B", "Amount Paid": 1000.0, "Timestamp": "2022/09/01 10:00", "transaction_id": "T1"},
            {"Account": "B", "Account.1": "C", "Amount Paid": 980.0,  "Timestamp": "2022/09/01 10:30", "transaction_id": "T2"},
            {"Account": "C", "Account.1": "A", "Amount Paid": 950.0,  "Timestamp": "2022/09/01 11:00", "transaction_id": "T3"}
        ])
        G = self.engine.build_graph(df)
        patterns = self.engine.detect_circular_flow(G)

        self.assertEqual(len(patterns), 1)
        p = patterns[0]
        self.assertEqual(p["typology"], "CIRCULAR_FLOW")
        self.assertEqual(p["cycle_length"], 3)
        self.assertSetEqual(set(p["involved_accounts"]), {"A", "B", "C"})

    def test_05_detect_rapid_movement(self):
        """Tests rapid pass-through mule: B receives from A and sends to C within 45 min."""
        df = pd.DataFrame([
            {"Account": "A", "Account.1": "B", "Amount Paid": 5000.0, "Timestamp": "2022/09/01 10:00", "transaction_id": "T1"},
            {"Account": "B", "Account.1": "C", "Amount Paid": 4900.0, "Timestamp": "2022/09/01 10:45", "transaction_id": "T2"}
        ])
        G = self.engine.build_graph(df)
        patterns = self.engine.detect_rapid_movement(G)

        self.assertEqual(len(patterns), 1)
        p = patterns[0]
        self.assertEqual(p["typology"], "RAPID_MOVEMENT")
        self.assertEqual(p["intermediary_account"], "B")
        self.assertEqual(p["statistics"]["elapsed_minutes"], 45.0)
        self.assertAlmostEqual(p["statistics"]["pass_through_ratio"], 4900.0 / 5000.0, places=3)

    def test_06_counterparty_concentration(self):
        """Tests concentration where A sends 95% of its funds to single counterparty B."""
        df = pd.DataFrame([
            {"Account": "A", "Account.1": "B", "Amount Paid": 9500.0, "Timestamp": "2022/09/01 10:00", "transaction_id": "T1"},
            {"Account": "A", "Account.1": "C", "Amount Paid": 250.0,  "Timestamp": "2022/09/01 10:10", "transaction_id": "T2"},
            {"Account": "A", "Account.1": "D", "Amount Paid": 250.0,  "Timestamp": "2022/09/01 10:20", "transaction_id": "T3"}
        ])
        G = self.engine.build_graph(df)
        patterns = self.engine.detect_counterparty_concentration(G)

        self.assertEqual(len(patterns), 1)
        p = patterns[0]
        self.assertEqual(p["typology"], "COUNTERPARTY_CONCENTRATION")
        self.assertEqual(p["involved_accounts"], ["A", "B"])
        self.assertEqual(p["statistics"]["concentration_ratio_pct"], 95.0)

    def test_07_empty_graph(self):
        """Tests safe handling of empty dataset."""
        empty_df = pd.DataFrame(columns=["Account", "Account.1", "Amount Paid", "Timestamp", "transaction_id"])
        summary = self.engine.analyze_network(empty_df)
        self.assertEqual(summary["graph_summary"]["nodes_count"], 0)
        self.assertEqual(summary["graph_summary"]["total_patterns_detected"], 0)

if __name__ == "__main__":
    unittest.main()
