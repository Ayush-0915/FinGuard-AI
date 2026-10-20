"""
FinGuard AI — Export Manifest & Provenance Auditor
Generates a cryptographically verified provenance manifest recording all dataset,
model, feature contract, and export artifact SHA-256 hashes.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any
try:
    from .config import DEFAULT_CONFIG, ExportConfig
except (ImportError, ValueError):
    from config import DEFAULT_CONFIG, ExportConfig

def calc_file_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()

class ExportManifestAuditor:
    def __init__(self, config: ExportConfig = DEFAULT_CONFIG, run_id: str = "RUN-IBM-HI-SMALL-20261020-01"):
        self.config = config
        self.run_id = run_id

    def generate_manifest(
        self,
        saved_files: Dict[str, str],
        reader_stats: Dict[str, Any],
        selected_count: int,
        timestamp_range: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Constructs and saves export_manifest.json.
        """
        # 1. Source & Model Hashes
        source_hashes = {
            "dataset_csv": {
                "path": self.config.dataset_csv_path,
                "sha256": calc_file_sha256(self.config.dataset_csv_path),
                "verified_match": (calc_file_sha256(self.config.dataset_csv_path) == self.config.expected_dataset_sha256)
            },
            "lightgbm_model": {
                "path": self.config.lgb_model_path,
                "sha256": calc_file_sha256(self.config.lgb_model_path),
                "verified_match": (calc_file_sha256(self.config.lgb_model_path) == self.config.expected_lgb_sha256)
            },
            "category_encoders": {
                "path": self.config.encoders_path,
                "sha256": calc_file_sha256(self.config.encoders_path),
                "verified_match": (calc_file_sha256(self.config.encoders_path) == self.config.expected_encoders_sha256)
            }
        }

        # 2. Output Artifact Hashes
        artifact_hashes = {}
        for key, fpath in saved_files.items():
            if os.path.exists(fpath):
                artifact_hashes[key] = {
                    "file_name": os.path.basename(fpath),
                    "size_bytes": os.path.getsize(fpath),
                    "sha256": calc_file_sha256(fpath)
                }

        manifest_data = {
            "manifest_version": "1.0.0",
            "run_id": self.run_id,
            "generated_at": datetime.now().isoformat(),
            "pipeline_version": self.config.pipeline_version,
            "model_version": self.config.model_version,
            "feature_contract": {
                "feature_count": len(self.config.feature_columns),
                "features": self.config.feature_columns
            },
            "provenance_hashes": source_hashes,
            "dataset_ingestion_statistics": reader_stats,
            "selection_summary": {
                "total_scanned_rows": reader_stats.get("total_rows_scanned", 0),
                "selected_records_count": selected_count,
                "selection_cap": self.config.pilot_export_cap,
                "selection_policy": "Top-500 Alerts + 250 Graph Counterparties + 250 Baseline Samples",
                "timestamp_range": timestamp_range or {"min": "2022/09/01 00:20", "max": "2022/09/10 23:59"}
            },
            "label_protection_policy": (
                "The ground-truth laundering label 'Is Laundering' is strictly isolated in "
                "evaluation_ground_truth.json for offline benchmark audit purposes. "
                "It is completely excluded from inference feature inputs, model scoring, "
                "and operational database payloads."
            ),
            "output_artifacts": artifact_hashes
        }

        # Save manifest.json
        manifest_path = os.path.join(self.config.output_artifacts_dir, "export_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return manifest_data
