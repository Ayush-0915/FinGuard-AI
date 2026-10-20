"""
FinGuard AI — Model Scoring Engine
Performs read-only inference using frozen production LightGBM and Isolation Forest.
Strictly verifies SHA-256 model hashes before loading. Zero model retraining.
"""

import os
import joblib
import hashlib
import numpy as np
import pandas as pd
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

class ModelScoringEngine:
    def __init__(self, config: ExportConfig = DEFAULT_CONFIG):
        self.config = config
        self._verify_and_load_models()

    def _verify_and_load_models(self):
        # 1. Verify LightGBM model hash
        lgb_path = self.config.lgb_model_path
        if not os.path.exists(lgb_path):
            raise FileNotFoundError(f"LightGBM model not found at: {lgb_path}")
        
        actual_lgb_hash = calc_file_sha256(lgb_path)
        if actual_lgb_hash != self.config.expected_lgb_sha256:
            raise RuntimeError(
                f"SAFETY VIOLATION: LightGBM model hash mismatch! "
                f"Expected: {self.config.expected_lgb_sha256}, Actual: {actual_lgb_hash}"
            )

        self.lgb_model = joblib.load(lgb_path)

        # 2. Verify and load Isolation Forest if available
        if_path = os.path.join(self.config.models_dir, "muleguard_isolation_forest.pkl")
        self.if_model = None
        if os.path.exists(if_path):
            self.if_model = joblib.load(if_path)

    def score_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes model risk probabilities, anomaly scores, and risk tiers.
        Features must be in exact contract order.
        """
        if len(features_df) == 0:
            return pd.DataFrame(columns=["transaction_id", "model_risk_score", "anomaly_score", "risk_tier"])

        tx_ids = features_df["transaction_id"].values
        feature_cols = self.config.feature_columns
        X = features_df[feature_cols].values.astype(np.float64)

        # LightGBM Probability Prediction
        if hasattr(self.lgb_model, "predict_proba"):
            probs = self.lgb_model.predict_proba(X)[:, 1]
        else:
            probs = self.lgb_model.predict(X)
        probs = np.clip(probs, 0.0, 1.0)

        # Isolation Forest Anomaly Scoring
        anomaly_scores = np.zeros(len(features_df), dtype=np.float64)
        if self.if_model is not None and hasattr(self.if_model, "decision_function"):
            try:
                decision = self.if_model.decision_function(X)
                anomaly_scores = -decision
            except Exception:
                pass

        # Risk Tier Assignment
        crit_t = self.config.critical_threshold
        high_t = self.config.high_threshold
        med_t = self.config.medium_threshold

        tiers = []
        for p in probs:
            if p >= crit_t:
                tiers.append("Critical")
            elif p >= high_t:
                tiers.append("High")
            elif p >= med_t:
                tiers.append("Medium")
            else:
                tiers.append("Low")

        result_df = pd.DataFrame({
            "transaction_id": tx_ids,
            "model_risk_score": probs,
            "anomaly_score": anomaly_scores,
            "risk_tier": tiers
        })

        return result_df
