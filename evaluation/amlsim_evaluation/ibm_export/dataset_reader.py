"""
FinGuard AI — IBM AML Dataset Chunked Streaming Reader
Safely reads and validates the IBM AML transaction dataset in bounded chunks.
Strictly isolates the ground-truth laundering label from the inference stream.
"""

import os
import pandas as pd
from typing import Generator, Tuple, Dict, Any
try:
    from .config import DEFAULT_CONFIG, ExportConfig
except (ImportError, ValueError):
    from config import DEFAULT_CONFIG, ExportConfig

EXPECTED_CSV_COLUMNS = [
    "Timestamp",
    "From Bank",
    "Account",
    "To Bank",
    "Account.1",
    "Amount Received",
    "Receiving Currency",
    "Amount Paid",
    "Payment Currency",
    "Payment Format",
    "Is Laundering"
]

class DatasetReader:
    def __init__(self, config: ExportConfig = DEFAULT_CONFIG):
        self.config = config
        self.csv_path = config.dataset_csv_path
        self.chunk_size = config.chunk_size
        
        # Reader metrics
        self.total_rows_scanned = 0
        self.valid_rows_count = 0
        self.invalid_rows_count = 0
        self.duplicate_rows_count = 0
        self.positive_labels_count = 0
        self.negative_labels_count = 0

    def stream_chunks(
        self,
        max_rows: int = None
    ) -> Generator[Tuple[pd.DataFrame, Dict[str, int]], None, None]:
        """
        Yields tuples of (clean_transactions_df, isolated_ground_truth_dict).
        
        - clean_transactions_df: DataFrame with standardized column names,
          deterministic transaction_id, and STRICTLY NO target label.
        - isolated_ground_truth_dict: Mapping of {transaction_id: int(label)}
          kept strictly separate for offline evaluation auditing only.
        """
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"IBM AML dataset CSV not found at: {self.csv_path}")

        global_row_idx = 0
        with pd.read_csv(
            self.csv_path,
            chunksize=self.chunk_size,
            dtype={
                "Timestamp": str,
                "From Bank": "int64",
                "Account": str,
                "To Bank": "int64",
                "Account.1": str,
                "Amount Received": "float64",
                "Receiving Currency": str,
                "Amount Paid": "float64",
                "Payment Currency": str,
                "Payment Format": str,
                "Is Laundering": "int64"
            }
        ) as reader:
            for chunk in reader:
                # 1. Header & Column Validation
                if list(chunk.columns) != EXPECTED_CSV_COLUMNS:
                    raise ValueError(
                        f"CSV column mismatch! Expected: {EXPECTED_CSV_COLUMNS}, Got: {list(chunk.columns)}"
                    )

                # Check max rows boundary if specified
                if max_rows is not None and global_row_idx >= max_rows:
                    break

                chunk_len = len(chunk)
                if max_rows is not None and (global_row_idx + chunk_len) > max_rows:
                    chunk = chunk.iloc[:(max_rows - global_row_idx)]
                    chunk_len = len(chunk)

                self.total_rows_scanned += chunk_len

                # 2. Duplicate Detection
                dups = chunk.duplicated().sum()
                self.duplicate_rows_count += int(dups)

                # 3. Missing Value Validation
                null_count = chunk.isnull().sum().sum()
                if null_count > 0:
                    self.invalid_rows_count += int(null_count)
                    # Drop rows with nulls if any exist
                    chunk = chunk.dropna()
                    chunk_len = len(chunk)

                self.valid_rows_count += chunk_len

                # 4. Generate Deterministic Transaction IDs
                tx_ids = [f"IBM_TX_{global_row_idx + i:07d}" for i in range(chunk_len)]
                global_row_idx += chunk_len

                # 5. Extract and ISOLATE the Ground-Truth Evaluation Label
                raw_labels = chunk["Is Laundering"].values
                isolated_labels = {}
                for tx_id, lbl in zip(tx_ids, raw_labels):
                    lbl_int = int(lbl)
                    isolated_labels[tx_id] = lbl_int
                    if lbl_int == 1:
                        self.positive_labels_count += 1
                    else:
                        self.negative_labels_count += 1

                # 6. Standardize Clean Transaction DataFrame (LABEL IS DROPPED)
                clean_df = pd.DataFrame({
                    "transaction_id": tx_ids,
                    "timestamp": chunk["Timestamp"].values,
                    "from_bank": chunk["From Bank"].values,
                    "sender_account": chunk["Account"].values,
                    "to_bank": chunk["To Bank"].values,
                    "receiver_account": chunk["Account.1"].values,
                    "amount_received": chunk["Amount Received"].values,
                    "receiving_currency": chunk["Receiving Currency"].values,
                    "amount_paid": chunk["Amount Paid"].values,
                    "payment_currency": chunk["Payment Currency"].values,
                    "payment_format": chunk["Payment Format"].values
                })

                # Assert label is completely absent from clean_df
                assert "Is Laundering" not in clean_df.columns
                assert "is_laundering" not in clean_df.columns
                assert "label" not in clean_df.columns

                yield clean_df, isolated_labels

    def get_statistics(self) -> Dict[str, Any]:
        """Returns comprehensive reader ingestion statistics."""
        return {
            "total_rows_scanned": self.total_rows_scanned,
            "valid_rows_count": self.valid_rows_count,
            "invalid_rows_count": self.invalid_rows_count,
            "duplicate_rows_count": self.duplicate_rows_count,
            "positive_labels_count": self.positive_labels_count,
            "negative_labels_count": self.negative_labels_count,
            "prevalence_pct": (
                (self.positive_labels_count / self.valid_rows_count * 100.0)
                if self.valid_rows_count > 0 else 0.0
            )
        }
