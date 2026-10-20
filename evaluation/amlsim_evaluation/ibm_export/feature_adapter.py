"""
FinGuard AI — Point-in-Time Feature Engine Adapter
Connects streaming chunks to the leakage-free PointInTimeFeatureEngine.
Maintains running state ledger across sequential chunks with zero lookahead.
"""

import os
import sys
import pandas as pd
from typing import Tuple
try:
    from .config import DEFAULT_CONFIG, ExportConfig
except (ImportError, ValueError):
    from config import DEFAULT_CONFIG, ExportConfig

# Import verified PointInTimeFeatureEngine from evaluation/amlsim_evaluation
EVAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if EVAL_DIR not in sys.path:
    sys.path.insert(0, EVAL_DIR)

from feature_engine import PointInTimeFeatureEngine, FEATURE_COLUMNS

class FeatureAdapter:
    def __init__(self, config: ExportConfig = DEFAULT_CONFIG):
        self.config = config
        self.engine = PointInTimeFeatureEngine(encoders_path=config.encoders_path)

    def reset(self):
        """Resets the internal running ledger."""
        self.engine.reset_ledger()

    def transform_chunk(self, clean_tx_df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms a clean transaction chunk into the exact 26 point-in-time features.
        Preserves running ledger across sequential streaming chunks.
        
        Input: clean_tx_df (standardized columns, NO target label)
        Output: features_df (26 columns in exact contract order)
        """
        if len(clean_tx_df) == 0:
            return pd.DataFrame(columns=FEATURE_COLUMNS)

        # Map to raw format expected by PointInTimeFeatureEngine
        mapped_df = pd.DataFrame({
            "Timestamp": clean_tx_df["timestamp"].values,
            "From Bank": clean_tx_df["from_bank"].values,
            "Account": clean_tx_df["sender_account"].values,
            "To Bank": clean_tx_df["to_bank"].values,
            "Account.1": clean_tx_df["receiver_account"].values,
            "Amount Received": clean_tx_df["amount_received"].values,
            "Receiving Currency": clean_tx_df["receiving_currency"].values,
            "Amount Paid": clean_tx_df["amount_paid"].values,
            "Payment Currency": clean_tx_df["payment_currency"].values,
            "Payment Format": clean_tx_df["payment_format"].values
        })

        # Process through verified engine
        # preserve_order=True guarantees features match clean_tx_df row-for-row
        features_df, _ = self.engine.process_dataframe(
            mapped_df,
            is_sorted=False,
            preserve_order=True
        )

        # Attach transaction_id for alignment
        features_df["transaction_id"] = clean_tx_df["transaction_id"].values

        return features_df
