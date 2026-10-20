"""
FinGuard AI — IBM AML Export Configuration
Defines verified parameters, safety boundaries, paths, and selection quotas
for the safe hybrid IBM AML dataset integration.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

@dataclass
class ExportConfig:
    # Dataset Paths & Hashes
    dataset_csv_path: str = os.path.join(ROOT_DIR, "data", "aml_dataset", "HI-Small_Trans.csv")
    expected_dataset_sha256: str = "b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040"
    
    # Model Artifact Paths & Hashes
    models_dir: str = os.path.join(ROOT_DIR, "models")
    lgb_model_path: str = os.path.join(models_dir, "muleguard_lightgbm.pkl")
    expected_lgb_sha256: str = "02c5f122e1ee729bd97bb08e8d004dae1b4b919416384c4d5c214598af702fa2"
    encoders_path: str = os.path.join(models_dir, "category_encoders.pkl")
    expected_encoders_sha256: str = "ff5d855fe24e3fddac6a136be0d8ed048e0b413486c9733b7bd5addcdc65839a"
    feature_columns_path: str = os.path.join(models_dir, "feature_columns.json")
    
    # Output Artifacts Directory
    output_artifacts_dir: str = os.path.join(os.path.dirname(__file__), "artifacts")
    
    # Execution & Processing Limits
    chunk_size: int = 100_000
    pilot_export_cap: int = 1_000
    top_alerts_quota: int = 500
    connected_counterparties_quota: int = 250
    baseline_samples_quota: int = 250
    
    # Model Inference Parameters
    operating_threshold: float = 0.97
    critical_threshold: float = 0.95
    high_threshold: float = 0.70
    medium_threshold: float = 0.40
    
    # Provenance
    pipeline_version: str = "1.0.0-hybrid"
    model_version: str = "LightGBM-4.5.0-FinGuard-AI"
    
    # Invariant Feature Names in Contract Order
    feature_columns: List[str] = field(default_factory=lambda: [
        "from_bank",
        "to_bank",
        "amount_received",
        "receiving_currency",
        "amount_paid",
        "payment_currency",
        "payment_format",
        "hour",
        "day_of_week",
        "amount_diff",
        "amount_ratio",
        "currency_match",
        "same_bank",
        "sender_transaction_count",
        "sender_total_amount",
        "sender_avg_amount",
        "sender_max_amount",
        "sender_unique_receivers",
        "sender_unique_banks",
        "receiver_transaction_count",
        "receiver_total_amount",
        "receiver_avg_amount",
        "receiver_max_amount",
        "receiver_unique_senders",
        "receiver_unique_banks",
        "seconds_since_previous"
    ])

DEFAULT_CONFIG = ExportConfig()
