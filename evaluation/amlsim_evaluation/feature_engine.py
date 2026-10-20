"""
FinGuard AI — Point-in-Time Streaming Feature Engine (Phase 2)
Isolated feature pipeline implementing timestamp-batch processing and leakage-free
temporal feature engineering for the IBM AML transaction dataset.

Strictly preserves:
- 26-feature exact names, order, types, and mathematical formulas
- Simultaneous-transaction batch semantics (transactions at timestamp T only observe state prior to T)
- Zero lookahead data leakage
- 100% categorical encoding fidelity matching category_encoders.pkl
"""

import os
import pickle
import pandas as pd
import numpy as np

# Exact feature names in invariant contract order
FEATURE_COLUMNS = [
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
]

CATEGORICAL_FEATURES = ["receiving_currency", "payment_currency", "payment_format"]

# Default sentinel for first transaction of an account (from notebook.ipynb Cell 24)
FIRST_TX_SENTINEL = 999999.0
RATIO_EPSILON = 1e-6

class PointInTimeFeatureEngine:
    def __init__(self, encoders_path=None):
        """
        Initializes the feature engine with categorical encoders.
        If encoders_path is None, loads from the production model directory in read-only mode.
        """
        if encoders_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            encoders_path = os.path.join(base_dir, "models", "category_encoders.pkl")
            
        with open(encoders_path, "rb") as f:
            self.encoders = pickle.load(f)
            
        self.receiving_currency_map = self.encoders["receiving_currency"]
        self.payment_currency_map = self.encoders["payment_currency"]
        self.payment_format_map = self.encoders["payment_format"]
        
        # State ledger
        self.reset_ledger()

    def reset_ledger(self):
        """
        Resets the internal running ledger state.
        """
        # sender_ledger: sender_account -> {
        #   'count': int,
        #   'total': float,
        #   'max': float,
        #   'receivers': set,
        #   'banks': set,
        #   'last_epoch_sec': int
        # }
        self.sender_ledger = {}
        
        # receiver_ledger: receiver_account -> {
        #   'count': int,
        #   'total': float,
        #   'max': float,
        #   'senders': set,
        #   'banks': set
        # }
        self.receiver_ledger = {}

    def process_dataframe(self, df: pd.DataFrame, is_sorted=False, preserve_order=True):
        """
        Processes a DataFrame of transactions through the point-in-time feature pipeline.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Transaction records. Must contain columns:
            'Timestamp', 'From Bank', 'Account', 'To Bank', 'Account.1',
            'Amount Received', 'Receiving Currency', 'Amount Paid', 'Payment Currency', 'Payment Format'
        is_sorted : bool
            If True, assumes df is already chronologically sorted by Timestamp.
            If False, sorts df chronologically.
        preserve_order : bool
            If True, returns features aligned to the original input row indices of df.
            If False, returns features in chronological order.
            
        Returns:
        --------
        features_df : pd.DataFrame
            DataFrame containing exactly the 26 contract features in exact order.
        metadata_df : pd.DataFrame
            Aligned DataFrame containing original row ID, Timestamp, labels (if present), and account IDs.
        """
        n_rows = len(df)
        if n_rows == 0:
            return pd.DataFrame(columns=FEATURE_COLUMNS), pd.DataFrame()

        # Work on a shallow copy with original index tracking
        work_df = df.copy()
        if "original_row_id" not in work_df.columns:
            work_df["original_row_id"] = np.arange(n_rows, dtype=np.int32)

        # Parse timestamps and convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(work_df["Timestamp"]):
            work_df["dt"] = pd.to_datetime(work_df["Timestamp"], format="%Y/%m/%d %H:%M", errors="coerce")
        else:
            work_df["dt"] = work_df["Timestamp"]

        # Sort chronologically by dt and original_row_id using stable sort
        if not is_sorted:
            work_df = work_df.sort_values(["dt", "original_row_id"], kind="mergesort").reset_index(drop=True)

        # Epoch seconds for ultra-fast arithmetic
        epoch_secs = work_df["dt"].astype("int64") // 10**9

        # Pre-allocate feature arrays
        f_from_bank = work_df["From Bank"].astype(np.int64).values
        f_to_bank = work_df["To Bank"].astype(np.int64).values
        f_amount_rec = work_df["Amount Received"].astype(np.float64).values
        f_amount_paid = work_df["Amount Paid"].astype(np.float64).values

        # Encoded categoricals
        f_rec_curr = np.array([self.receiving_currency_map.get(c, -1) for c in work_df["Receiving Currency"]], dtype=np.int64)
        f_pay_curr = np.array([self.payment_currency_map.get(c, -1) for c in work_df["Payment Currency"]], dtype=np.int64)
        f_pay_fmt = np.array([self.payment_format_map.get(c, -1) for c in work_df["Payment Format"]], dtype=np.int64)

        # Basic point-in-time arithmetic features
        f_hour = work_df["dt"].dt.hour.astype(np.int8).values
        f_day_of_week = work_df["dt"].dt.dayofweek.astype(np.int8).values
        f_amount_diff = (f_amount_rec - f_amount_paid).astype(np.float64)
        f_amount_ratio = (f_amount_rec / (f_amount_paid + RATIO_EPSILON)).astype(np.float64)
        f_currency_match = (f_rec_curr == f_pay_curr).astype(np.int8)
        f_same_bank = (f_from_bank == f_to_bank).astype(np.int8)

        # Arrays for behavioral aggregates (to be populated in timestamp-batch streaming loop)
        f_s_tx_count = np.zeros(n_rows, dtype=np.int64)
        f_s_tot_amt = np.zeros(n_rows, dtype=np.float64)
        f_s_avg_amt = np.zeros(n_rows, dtype=np.float64)
        f_s_max_amt = np.zeros(n_rows, dtype=np.float64)
        f_s_uniq_rec = np.zeros(n_rows, dtype=np.int64)
        f_s_uniq_bnk = np.zeros(n_rows, dtype=np.int64)

        f_r_tx_count = np.zeros(n_rows, dtype=np.int64)
        f_r_tot_amt = np.zeros(n_rows, dtype=np.float64)
        f_r_avg_amt = np.zeros(n_rows, dtype=np.float64)
        f_r_max_amt = np.zeros(n_rows, dtype=np.float64)
        f_r_uniq_snd = np.zeros(n_rows, dtype=np.int64)
        f_r_uniq_bnk = np.zeros(n_rows, dtype=np.int64)

        f_sec_prev = np.full(n_rows, FIRST_TX_SENTINEL, dtype=np.float64)

        # Sender & receiver account identifiers
        senders = work_df["Account"].astype(str).values
        receivers = work_df["Account.1"].astype(str).values
        epoch_vals = epoch_secs.values

        # Group indices by timestamp (Timestamp batches)
        # We can detect timestamp changes rapidly
        dt_values = work_df["dt"].values
        # Find transition indices where dt changes
        change_mask = np.empty(n_rows, dtype=bool)
        change_mask[0] = True
        change_mask[1:] = (dt_values[1:] != dt_values[:-1])
        batch_starts = np.flatnonzero(change_mask)
        batch_ends = np.append(batch_starts[1:], n_rows)

        s_ledger = self.sender_ledger
        r_ledger = self.receiver_ledger

        # Process timestamp batches
        for b_start, b_end in zip(batch_starts, batch_ends):
            # STEP 1: Compute features for all transactions in this timestamp batch
            # using strictly prior ledger state (state before this timestamp batch)
            for i in range(b_start, b_end):
                s = senders[i]
                r = receivers[i]
                t_sec = epoch_vals[i]

                # Sender historical aggregates
                s_state = s_ledger.get(s)
                if s_state is not None:
                    cnt = s_state[0]
                    tot = s_state[1]
                    f_s_tx_count[i] = cnt
                    f_s_tot_amt[i] = tot
                    f_s_avg_amt[i] = tot / cnt if cnt > 0 else 0.0
                    f_s_max_amt[i] = s_state[2]
                    f_s_uniq_rec[i] = len(s_state[3])
                    f_s_uniq_bnk[i] = len(s_state[4])
                    # Seconds since previous
                    last_sec = s_state[5]
                    if last_sec is not None:
                        diff_sec = float(t_sec - last_sec)
                        f_sec_prev[i] = diff_sec if diff_sec >= 0 else FIRST_TX_SENTINEL
                # Else: account is unseen as sender -> stays 0 / 999999.0

                # Receiver historical aggregates
                r_state = r_ledger.get(r)
                if r_state is not None:
                    cnt_r = r_state[0]
                    tot_r = r_state[1]
                    f_r_tx_count[i] = cnt_r
                    f_r_tot_amt[i] = tot_r
                    f_r_avg_amt[i] = tot_r / cnt_r if cnt_r > 0 else 0.0
                    f_r_max_amt[i] = r_state[2]
                    f_r_uniq_snd[i] = len(r_state[3])
                    f_r_uniq_bnk[i] = len(r_state[4])
                # Else: account is unseen as receiver -> stays 0

            # STEP 2: Update historical ledger state with all transactions in this timestamp batch
            for i in range(b_start, b_end):
                s = senders[i]
                r = receivers[i]
                paid = f_amount_paid[i]
                rec = f_amount_rec[i]
                dest_b = f_to_bank[i]
                orig_b = f_from_bank[i]
                t_sec = epoch_vals[i]

                # Update sender ledger
                s_state = s_ledger.get(s)
                if s_state is None:
                    # [count, total, max, receivers_set, banks_set, last_epoch_sec]
                    s_ledger[s] = [1, paid, paid, {r}, {dest_b}, t_sec]
                else:
                    s_state[0] += 1
                    s_state[1] += paid
                    if paid > s_state[2]:
                        s_state[2] = paid
                    s_state[3].add(r)
                    s_state[4].add(dest_b)
                    s_state[5] = t_sec

                # Update receiver ledger
                r_state = r_ledger.get(r)
                if r_state is None:
                    # [count, total, max, senders_set, banks_set]
                    r_ledger[r] = [1, rec, rec, {s}, {orig_b}]
                else:
                    r_state[0] += 1
                    r_state[1] += rec
                    if rec > r_state[2]:
                        r_state[2] = rec
                    r_state[3].add(s)
                    r_state[4].add(orig_b)

        # Assemble the 26 features DataFrame
        features_dict = {
            "from_bank": f_from_bank,
            "to_bank": f_to_bank,
            "amount_received": f_amount_rec,
            "receiving_currency": f_rec_curr,
            "amount_paid": f_amount_paid,
            "payment_currency": f_pay_curr,
            "payment_format": f_pay_fmt,
            "hour": f_hour,
            "day_of_week": f_day_of_week,
            "amount_diff": f_amount_diff,
            "amount_ratio": f_amount_ratio,
            "currency_match": f_currency_match,
            "same_bank": f_same_bank,
            "sender_transaction_count": f_s_tx_count,
            "sender_total_amount": f_s_tot_amt,
            "sender_avg_amount": f_s_avg_amt,
            "sender_max_amount": f_s_max_amt,
            "sender_unique_receivers": f_s_uniq_rec,
            "sender_unique_banks": f_s_uniq_bnk,
            "receiver_transaction_count": f_r_tx_count,
            "receiver_total_amount": f_r_tot_amt,
            "receiver_avg_amount": f_r_avg_amt,
            "receiver_max_amount": f_r_max_amt,
            "receiver_unique_senders": f_r_uniq_snd,
            "receiver_unique_banks": f_r_uniq_bnk,
            "seconds_since_previous": f_sec_prev,
        }

        features_df = pd.DataFrame(features_dict, columns=FEATURE_COLUMNS)

        # Metadata DataFrame
        meta_cols = ["original_row_id", "dt", "Timestamp", "Account", "Account.1"]
        if "Is Laundering" in work_df.columns:
            meta_cols.append("Is Laundering")
        metadata_df = work_df[meta_cols].copy()

        # If preserve_order is requested, restore the original input ordering
        if preserve_order and not is_sorted:
            # Reorder back to original_row_id
            order = np.argsort(metadata_df["original_row_id"].values)
            features_df = features_df.iloc[order].reset_index(drop=True)
            metadata_df = metadata_df.iloc[order].reset_index(drop=True)

        return features_df, metadata_df
