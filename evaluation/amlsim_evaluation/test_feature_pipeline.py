"""
FinGuard AI — Automated Feature Pipeline Validation Suite (Phase 2)
Tests all 10 required invariants and executes hand-checkable unit tests on a synthetic fixture.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
import numpy as np
import pandas as pd
from feature_engine import (
    PointInTimeFeatureEngine,
    FEATURE_COLUMNS,
    CATEGORICAL_FEATURES,
    FIRST_TX_SENTINEL,
    RATIO_EPSILON
)

class TestPointInTimeFeaturePipeline(unittest.TestCase):
    def setUp(self):
        self.engine = PointInTimeFeatureEngine()

    def create_synthetic_fixture(self):
        """
        Creates a hand-crafted synthetic transaction history with multiple accounts,
        simultaneous (same-minute) transactions, repeated transactions, and direction switches.
        """
        records = [
            # Tx 0: ACC_A -> ACC_B at 10:00
            {
                "Timestamp": "2022/09/01 10:00",
                "From Bank": 10,
                "Account": "ACC_A",
                "To Bank": 20,
                "Account.1": "ACC_B",
                "Amount Received": 100.0,
                "Receiving Currency": "US Dollar",
                "Amount Paid": 100.0,
                "Payment Currency": "US Dollar",
                "Payment Format": "Wire",
                "Is Laundering": 0
            },
            # Tx 1: ACC_A -> ACC_C at 10:15 (15 min / 900s later)
            {
                "Timestamp": "2022/09/01 10:15",
                "From Bank": 10,
                "Account": "ACC_A",
                "To Bank": 30,
                "Account.1": "ACC_C",
                "Amount Received": 200.0,
                "Receiving Currency": "US Dollar",
                "Amount Paid": 200.0,
                "Payment Currency": "US Dollar",
                "Payment Format": "ACH",
                "Is Laundering": 0
            },
            # Tx 2: ACC_A -> ACC_B at 10:30 (Collision 1)
            {
                "Timestamp": "2022/09/01 10:30",
                "From Bank": 10,
                "Account": "ACC_A",
                "To Bank": 20,
                "Account.1": "ACC_B",
                "Amount Received": 300.0,
                "Receiving Currency": "US Dollar",
                "Amount Paid": 300.0,
                "Payment Currency": "US Dollar",
                "Payment Format": "Wire",
                "Is Laundering": 1
            },
            # Tx 3: ACC_A -> ACC_D at 10:30 (Collision 2, same minute as Tx 2)
            {
                "Timestamp": "2022/09/01 10:30",
                "From Bank": 10,
                "Account": "ACC_A",
                "To Bank": 40,
                "Account.1": "ACC_D",
                "Amount Received": 400.0,
                "Receiving Currency": "US Dollar",
                "Amount Paid": 400.0,
                "Payment Currency": "US Dollar",
                "Payment Format": "Cheque",
                "Is Laundering": 0
            },
            # Tx 4: ACC_B -> ACC_A at 11:00 (Direction reversal)
            {
                "Timestamp": "2022/09/01 11:00",
                "From Bank": 20,
                "Account": "ACC_B",
                "To Bank": 10,
                "Account.1": "ACC_A",
                "Amount Received": 50.0,
                "Receiving Currency": "Euro",
                "Amount Paid": 55.0,
                "Payment Currency": "US Dollar",
                "Payment Format": "Cash",
                "Is Laundering": 0
            },
            # Tx 5: ACC_A -> ACC_B at 11:30 (Aggregates check after collision)
            {
                "Timestamp": "2022/09/01 11:30",
                "From Bank": 10,
                "Account": "ACC_A",
                "To Bank": 20,
                "Account.1": "ACC_B",
                "Amount Received": 500.0,
                "Receiving Currency": "US Dollar",
                "Amount Paid": 500.0,
                "Payment Currency": "US Dollar",
                "Payment Format": "Wire",
                "Is Laundering": 0
            }
        ]
        return pd.DataFrame(records)

    def test_01_feature_count_and_names(self):
        """Check 1: Output contains exactly 26 features in the correct order."""
        fixture = self.create_synthetic_fixture()
        feat_df, _ = self.engine.process_dataframe(fixture)
        self.assertEqual(len(feat_df.columns), 26)
        self.assertListEqual(list(feat_df.columns), FEATURE_COLUMNS)

    def test_02_no_target_leakage(self):
        """Check 2: Target label and derivatives are absent from features."""
        fixture = self.create_synthetic_fixture()
        feat_df, _ = self.engine.process_dataframe(fixture)
        for col in ["Is Laundering", "is_laundering", "target", "label", "is_sar"]:
            self.assertNotIn(col, feat_df.columns)

    def test_03_no_nan_or_infinities(self):
        """Check 3: No NaN, None, or infinite values in feature matrix."""
        fixture = self.create_synthetic_fixture()
        feat_df, _ = self.engine.process_dataframe(fixture)
        self.assertEqual(feat_df.isnull().sum().sum(), 0)
        for col in feat_df.columns:
            vals = feat_df[col].values
            self.assertFalse(np.isinf(vals).any(), f"Infinite values detected in column {col}")

    def test_04_simultaneous_transaction_isolation(self):
        """
        Check 4: Same-minute transactions do NOT update one another's features.
        Tx 2 and Tx 3 both occur at 10:30. Tx 3 must see the exact same sender
        count and total amount as Tx 2 (state as of 10:15), NOT including Tx 2.
        """
        fixture = self.create_synthetic_fixture()
        feat_df, _ = self.engine.process_dataframe(fixture)

        # Tx 2 (ACC_A -> ACC_B at 10:30)
        tx2_count = feat_df.loc[2, "sender_transaction_count"]
        tx2_tot = feat_df.loc[2, "sender_total_amount"]
        tx2_max = feat_df.loc[2, "sender_max_amount"]
        tx2_sec = feat_df.loc[2, "seconds_since_previous"]

        # Tx 3 (ACC_A -> ACC_D at 10:30, same minute)
        tx3_count = feat_df.loc[3, "sender_transaction_count"]
        tx3_tot = feat_df.loc[3, "sender_total_amount"]
        tx3_max = feat_df.loc[3, "sender_max_amount"]
        tx3_sec = feat_df.loc[3, "seconds_since_previous"]

        # Assert isolation between Tx 2 and Tx 3
        self.assertEqual(tx2_count, 2, "Tx 2 should observe 2 prior transactions (Tx 0 and Tx 1)")
        self.assertEqual(tx3_count, 2, "Tx 3 should also observe 2 prior transactions, NOT 3")
        self.assertEqual(tx2_tot, 300.0, "Tx 2 should observe 100 + 200 = 300.0")
        self.assertEqual(tx3_tot, 300.0, "Tx 3 should also observe 300.0, NOT 600.0")
        self.assertEqual(tx2_max, 200.0)
        self.assertEqual(tx3_max, 200.0)
        self.assertEqual(tx2_sec, 900.0, "Tx 2 seconds since previous should be 15 min (900s)")
        self.assertEqual(tx3_sec, 900.0, "Tx 3 seconds since previous should also be 15 min (900s), NOT 0.0")

    def test_05_subsequent_aggregates_include_collision_batch(self):
        """
        Check 5: After timestamp 10:30 completes, subsequent transaction (Tx 5 at 11:30)
        correctly includes ALL transactions from the 10:30 batch.
        """
        fixture = self.create_synthetic_fixture()
        feat_df, _ = self.engine.process_dataframe(fixture)

        # Tx 5 (ACC_A -> ACC_B at 11:30)
        # Prior transactions by ACC_A: Tx 0 (100), Tx 1 (200), Tx 2 (300), Tx 3 (400)
        self.assertEqual(feat_df.loc[5, "sender_transaction_count"], 4)
        self.assertEqual(feat_df.loc[5, "sender_total_amount"], 1000.0)
        self.assertEqual(feat_df.loc[5, "sender_avg_amount"], 250.0)
        self.assertEqual(feat_df.loc[5, "sender_max_amount"], 400.0)
        self.assertEqual(feat_df.loc[5, "sender_unique_receivers"], 3) # ACC_B, ACC_C, ACC_D
        self.assertEqual(feat_df.loc[5, "sender_unique_banks"], 3) # Banks 20, 30, 40
        self.assertEqual(feat_df.loc[5, "seconds_since_previous"], 3600.0) # 10:30 to 11:30 is 1 hour

    def test_06_sender_receiver_directionality(self):
        """
        Check 6: Sender and receiver statistics maintain strict directionality.
        ACC_B is sender in Tx 4 (11:00). Prior to Tx 4, ACC_B was only a receiver.
        ACC_B's sender statistics in Tx 4 must be 0, and seconds_since_previous must be sentinel.
        """
        fixture = self.create_synthetic_fixture()
        feat_df, _ = self.engine.process_dataframe(fixture)

        # Tx 4: ACC_B -> ACC_A
        self.assertEqual(feat_df.loc[4, "sender_transaction_count"], 0)
        self.assertEqual(feat_df.loc[4, "sender_total_amount"], 0.0)
        self.assertEqual(feat_df.loc[4, "seconds_since_previous"], FIRST_TX_SENTINEL)

        # ACC_A is receiver in Tx 4. Prior to Tx 4, ACC_A was only a sender.
        self.assertEqual(feat_df.loc[4, "receiver_transaction_count"], 0)
        self.assertEqual(feat_df.loc[4, "receiver_total_amount"], 0.0)

    def test_07_deterministic_reproducibility(self):
        """Check 7: Multiple runs on the same data yield identical results."""
        fixture = self.create_synthetic_fixture()
        
        self.engine.reset_ledger()
        feat_df1, _ = self.engine.process_dataframe(fixture)
        
        self.engine.reset_ledger()
        feat_df2, _ = self.engine.process_dataframe(fixture)
        
        pd.testing.assert_frame_equal(feat_df1, feat_df2)

    def test_08_out_of_order_input_handling(self):
        """Check 8: Shuffled input yields identical features aligned to original transactions."""
        fixture = self.create_synthetic_fixture()
        fixture["tx_id"] = np.arange(len(fixture))
        
        self.engine.reset_ledger()
        feat_df_orig, meta_orig = self.engine.process_dataframe(fixture, is_sorted=False, preserve_order=True)
        feat_df_orig["tx_id"] = fixture["tx_id"].values
        
        # Shuffle rows
        shuffled = fixture.sample(frac=1.0, random_state=42).reset_index(drop=True)
        self.engine.reset_ledger()
        feat_df_shuffled, meta_shuffled = self.engine.process_dataframe(shuffled, is_sorted=False, preserve_order=True)
        feat_df_shuffled["tx_id"] = shuffled["tx_id"].values
        
        # Verify alignment: for any transaction in shuffled, its features match original
        for tid in range(len(fixture)):
            row_orig = feat_df_orig[feat_df_orig["tx_id"] == tid].iloc[0]
            row_shuf = feat_df_shuffled[feat_df_shuffled["tx_id"] == tid].iloc[0]
            for col in FEATURE_COLUMNS:
                self.assertAlmostEqual(
                    row_orig[col],
                    row_shuf[col],
                    places=5,
                    msg=f"Mismatch in {col} for tx_id {tid}"
                )

    def test_09_arithmetic_features_accuracy(self):
        """Check 9: Exact arithmetic formulas (amount_diff, amount_ratio, currency_match, same_bank)."""
        fixture = self.create_synthetic_fixture()
        feat_df, _ = self.engine.process_dataframe(fixture)

        # Tx 4: Rec Euro (50.0), Paid USD (55.0)
        self.assertAlmostEqual(feat_df.loc[4, "amount_diff"], 50.0 - 55.0)
        self.assertAlmostEqual(feat_df.loc[4, "amount_ratio"], 50.0 / (55.0 + RATIO_EPSILON), places=5)
        self.assertEqual(feat_df.loc[4, "currency_match"], 0)
        self.assertEqual(feat_df.loc[4, "same_bank"], 0)

        # Tx 0: Rec 100.0, Paid 100.0, both USD
        self.assertEqual(feat_df.loc[0, "amount_diff"], 0.0)
        self.assertAlmostEqual(feat_df.loc[0, "amount_ratio"], 100.0 / (100.0 + RATIO_EPSILON), places=5)
        self.assertEqual(feat_df.loc[0, "currency_match"], 1)

    def test_10_category_encoding_coverage(self):
        """Check 10: Categorical encoding matches category_encoders.pkl."""
        fixture = self.create_synthetic_fixture()
        feat_df, _ = self.engine.process_dataframe(fixture)

        # US Dollar is index 12 in category_encoders.pkl
        self.assertEqual(feat_df.loc[0, "receiving_currency"], 12)
        self.assertEqual(feat_df.loc[0, "payment_currency"], 12)
        # Wire is index 6 in category_encoders.pkl
        self.assertEqual(feat_df.loc[0, "payment_format"], 6)

if __name__ == "__main__":
    unittest.main()
