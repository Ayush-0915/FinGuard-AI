"""
FinGuard AI — Unit & Integration Tests for IBM AML Export Pipeline
Validates chunking, schema conformance, 26-feature compatibility, frozen model inference,
strict label isolation, deterministic selection capping, and manifest auditing.
"""

import os
import sys
import json
import unittest
import pandas as pd
import numpy as np

MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

from config import DEFAULT_CONFIG, ExportConfig
from dataset_reader import DatasetReader
from feature_adapter import FeatureAdapter
from scoring import ModelScoringEngine, calc_file_sha256
from selection import RecordSelector
from export_builder import ExportPayloadBuilder
from manifest import ExportManifestAuditor

class TestIBMExportPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = DEFAULT_CONFIG
        cls.reader = DatasetReader(cls.config)
        cls.adapter = FeatureAdapter(cls.config)
        cls.scorer = ModelScoringEngine(cls.config)
        cls.selector = RecordSelector(cls.config)
        cls.builder = ExportPayloadBuilder(cls.config, run_id="TEST-RUN-01")
        cls.auditor = ExportManifestAuditor(cls.config, run_id="TEST-RUN-01")

    # 1. Config & File Integrity
    def test_01_config_and_file_integrity(self):
        """Verify dataset and production model files exist and match baseline SHA-256."""
        self.assertTrue(os.path.exists(self.config.dataset_csv_path))
        self.assertTrue(os.path.exists(self.config.lgb_model_path))
        self.assertTrue(os.path.exists(self.config.encoders_path))

        actual_lgb_hash = calc_file_sha256(self.config.lgb_model_path)
        self.assertEqual(actual_lgb_hash, self.config.expected_lgb_sha256)

        actual_enc_hash = calc_file_sha256(self.config.encoders_path)
        self.assertEqual(actual_enc_hash, self.config.expected_encoders_sha256)

    # 2. Reader & Chunk Boundaries
    def test_02_reader_and_chunk_boundaries(self):
        """Verify chunked streaming reads data correctly without target label in clean DataFrame."""
        chunks = list(self.reader.stream_chunks(max_rows=500))
        self.assertGreater(len(chunks), 0)

        clean_df, isolated_labels = chunks[0]
        self.assertIsInstance(clean_df, pd.DataFrame)
        self.assertEqual(len(clean_df), 500)
        self.assertEqual(len(isolated_labels), 500)

        # Label Isolation check: target label must NOT be in clean_df
        self.assertNotIn("Is Laundering", clean_df.columns)
        self.assertNotIn("is_laundering", clean_df.columns)

        # Deterministic IDs check
        self.assertEqual(clean_df["transaction_id"].iloc[0], "IBM_TX_0000000")
        self.assertEqual(clean_df["transaction_id"].iloc[1], "IBM_TX_0000001")

    # 3. Feature Adapter Compatibility
    def test_03_feature_adapter_26_features(self):
        """Verify feature engine outputs exactly 26 contract features in exact order."""
        for clean_df, _ in self.reader.stream_chunks(max_rows=200):
            features_df = self.adapter.transform_chunk(clean_df)
            
            # Check 26 features present
            for col in self.config.feature_columns:
                self.assertIn(col, features_df.columns)

            # Check no NaN or infinite values
            X = features_df[self.config.feature_columns].values
            self.assertFalse(np.isnan(X).any(), "Found NaN in feature matrix!")
            self.assertFalse(np.isinf(X).any(), "Found Inf in feature matrix!")
            break

    # 4. Model Scoring Without Retraining
    def test_04_scoring_without_model_mutation(self):
        """Verify model scoring runs in read-only mode with frozen hashes."""
        pre_hash = calc_file_sha256(self.config.lgb_model_path)

        for clean_df, _ in self.reader.stream_chunks(max_rows=200):
            features_df = self.adapter.transform_chunk(clean_df)
            scores_df = self.scorer.score_features(features_df)

            self.assertIn("model_risk_score", scores_df.columns)
            self.assertIn("risk_tier", scores_df.columns)
            self.assertTrue((scores_df["model_risk_score"] >= 0.0).all())
            self.assertTrue((scores_df["model_risk_score"] <= 1.0).all())
            break

        post_hash = calc_file_sha256(self.config.lgb_model_path)
        self.assertEqual(pre_hash, post_hash, "SAFETY VIOLATION: Model artifact altered during scoring!")

    # 5. Label Isolation in Payloads
    def test_05_label_isolation_in_payloads(self):
        """Confirm ground-truth labels are NEVER in transaction or score payloads."""
        clean_df, labels = next(self.reader.stream_chunks(max_rows=100))
        features_df = self.adapter.transform_chunk(clean_df)
        scores_df = self.scorer.score_features(features_df)

        selected_df = self.selector.select_bounded_records(clean_df, scores_df)
        payloads = self.builder.build_payloads(selected_df, labels, self.reader.get_statistics())

        # Check transactions payload
        for tx in payloads["transactions"]:
            self.assertNotIn("is_laundering", tx)
            self.assertNotIn("Is Laundering", tx)
            self.assertNotIn("label", tx)

        # Check scores payload
        for sc in payloads["scores"]:
            self.assertNotIn("is_laundering", sc)
            self.assertNotIn("ground_truth", sc)

        # Evaluation ground truth must be in its separate dict
        self.assertIn("evaluation_ground_truth", payloads)
        self.assertEqual(len(payloads["evaluation_ground_truth"]), len(selected_df))

    # 6. Selection Cap & Determinism
    def test_06_selection_cap_and_determinism(self):
        """Verify selection caps at configured limit and is 100% deterministic."""
        clean_df, _ = next(self.reader.stream_chunks(max_rows=1500))
        features_df = self.adapter.transform_chunk(clean_df)
        scores_df = self.scorer.score_features(features_df)

        sel_1 = self.selector.select_bounded_records(clean_df, scores_df)
        sel_2 = self.selector.select_bounded_records(clean_df, scores_df)

        # Cap verification
        self.assertLessEqual(len(sel_1), self.config.pilot_export_cap)

        # Determinism verification
        self.assertTrue(sel_1["transaction_id"].equals(sel_2["transaction_id"]))
        self.assertTrue(sel_1["model_risk_score"].equals(sel_2["model_risk_score"]))

    # 7. Payload Schema Conformance
    def test_07_payload_schema_conformance(self):
        """Verify database payloads conform strictly to proposed SQL DDL columns."""
        clean_df, labels = next(self.reader.stream_chunks(max_rows=200))
        features_df = self.adapter.transform_chunk(clean_df)
        scores_df = self.scorer.score_features(features_df)
        selected_df = self.selector.select_bounded_records(clean_df, scores_df)

        payloads = self.builder.build_payloads(selected_df, labels, self.reader.get_statistics())

        # 1. ibm_dataset_runs
        run = payloads["runs"]
        for req_field in ["run_id", "source_dataset", "source_sha256", "total_scanned_rows", "selected_records_count", "model_version", "pipeline_version"]:
            self.assertIn(req_field, run)

        # 2. ibm_benchmark_transactions
        first_tx = payloads["transactions"][0]
        for req_field in ["transaction_id", "run_id", "timestamp", "sender_account", "receiver_account", "amount", "receiving_currency", "payment_currency", "payment_format"]:
            self.assertIn(req_field, first_tx)

        # 3. ibm_benchmark_scores
        first_sc = payloads["scores"][0]
        for req_field in ["transaction_id", "run_id", "model_risk_score", "risk_rank", "risk_tier", "model_version"]:
            self.assertIn(req_field, first_sc)

        # 4. ibm_benchmark_evidence
        first_ev = payloads["evidence"][0]
        for req_field in ["transaction_id", "run_id", "human_readable_summary", "contributing_signals", "graph_patterns", "provenance_breakdown"]:
            self.assertIn(req_field, first_ev)

    # 8. Manifest Generation
    def test_08_manifest_generation(self):
        """Verify manifest records hashes, counts, and label protection statement."""
        clean_df, labels = next(self.reader.stream_chunks(max_rows=100))
        features_df = self.adapter.transform_chunk(clean_df)
        scores_df = self.scorer.score_features(features_df)
        selected_df = self.selector.select_bounded_records(clean_df, scores_df)

        test_out_dir = os.path.join(self.config.output_artifacts_dir, "test_tmp")
        os.makedirs(test_out_dir, exist_ok=True)
        test_config = ExportConfig(output_artifacts_dir=test_out_dir)
        test_builder = ExportPayloadBuilder(test_config, run_id="TEST-RUN-01")
        test_auditor = ExportManifestAuditor(test_config, run_id="TEST-RUN-01")

        payloads = test_builder.build_payloads(selected_df, labels, self.reader.get_statistics())
        saved_files = test_builder.save_payload_artifacts(payloads, output_dir=test_out_dir)

        manifest = test_auditor.generate_manifest(saved_files, self.reader.get_statistics(), len(selected_df))

        self.assertIn("manifest_version", manifest)
        self.assertIn("provenance_hashes", manifest)
        self.assertIn("label_protection_policy", manifest)
        self.assertIn("output_artifacts", manifest)

        # Cleanup test_tmp
        for f in saved_files.values():
            if os.path.exists(f):
                os.remove(f)
        m_path = os.path.join(test_out_dir, "export_manifest.json")
        if os.path.exists(m_path):
            os.remove(m_path)
        if os.path.exists(test_out_dir):
            os.rmdir(test_out_dir)

    # 9. Idempotency of Export
    def test_09_idempotency_of_export(self):
        """Verify that running payload builder twice yields identical payloads and hashes."""
        clean_df, labels = next(self.reader.stream_chunks(max_rows=100))
        features_df = self.adapter.transform_chunk(clean_df)
        scores_df = self.scorer.score_features(features_df)
        selected_df = self.selector.select_bounded_records(clean_df, scores_df)

        payload_1 = self.builder.build_payloads(selected_df, labels, self.reader.get_statistics())
        payload_2 = self.builder.build_payloads(selected_df, labels, self.reader.get_statistics())

        # Assert JSON serialization equivalence
        self.assertEqual(json.dumps(payload_1["transactions"]), json.dumps(payload_2["transactions"]))
        self.assertEqual(json.dumps(payload_1["scores"]), json.dumps(payload_2["scores"]))

    # 10. Temporal Batch Invariance
    def test_10_temporal_batch_invariance(self):
        """Verify that transactions occurring at the same timestamp do not see each other's updates."""
        same_time_txs = pd.DataFrame({
            "transaction_id": ["TX_A", "TX_B"],
            "timestamp": ["2022/09/01 10:00", "2022/09/01 10:00"],
            "from_bank": [1, 1],
            "sender_account": ["ACC_SAME", "ACC_SAME"],
            "to_bank": [2, 3],
            "receiver_account": ["REC_1", "REC_2"],
            "amount_received": [100.0, 200.0],
            "receiving_currency": ["US Dollar", "US Dollar"],
            "amount_paid": [100.0, 200.0],
            "payment_currency": ["US Dollar", "US Dollar"],
            "payment_format": ["ACH", "ACH"]
        })

        self.adapter.reset()
        feat = self.adapter.transform_chunk(same_time_txs)
        # Both transactions at 10:00 should see sender_transaction_count == 0 (state before 10:00)
        self.assertEqual(feat["sender_transaction_count"].iloc[0], 0)
        self.assertEqual(feat["sender_transaction_count"].iloc[1], 0)


if __name__ == "__main__":
    unittest.main()
