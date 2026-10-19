import os
import joblib
import json
import pandas as pd
import numpy as np

# Path configurations
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
CONFIG_PATH = os.path.join(MODELS_DIR, "feature_config.pkl")
ENCODER_PATH = os.path.join(MODELS_DIR, "category_encoders.pkl")
IF_CAT_MAPS_PATH = os.path.join(MODELS_DIR, "isolation_category_mappings.json")

class FeaturePipeline:
    def __init__(self):
        # Load pre-trained configuration and encoding maps
        self.config = joblib.load(CONFIG_PATH)
        self.lgb_encoders = joblib.load(ENCODER_PATH)
        
        with open(IF_CAT_MAPS_PATH, "r") as f:
            self.if_encoders = json.load(f)
            
        self.features = self.config["features"]
        self.cat_cols = self.config["categorical_features"]

    def build_features(self, target_tx: dict, history_txs: list) -> (pd.DataFrame, pd.DataFrame):
        """
        Builds the 26 features for target_tx based on history_txs (including the target transaction).
        Returns a tuple:
        - df_lgb: DataFrame ready for LightGBM prediction.
        - df_if: DataFrame ready for Isolation Forest anomaly detection.
        """
        # 1. Combine target transaction with history
        all_txs = history_txs.copy()
        
        # Verify if target_tx is already in the history to avoid duplicate counts
        tx_ids = [tx.get("transaction_id") for tx in all_txs]
        if target_tx.get("transaction_id") not in tx_ids:
            all_txs.append(target_tx)
            
        df = pd.DataFrame(all_txs)
        
        # 2. Date/Time conversions and sorting
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values(["sender_account", "timestamp"]).reset_index(drop=True)
        
        # 3. Calculate basic features
        df["hour"] = df["timestamp"].dt.hour.astype(np.int8)
        df["day_of_week"] = df["timestamp"].dt.dayofweek.astype(np.int8)
        df["amount_diff"] = df["amount_received"] - df["amount_paid"]
        df["amount_ratio"] = df["amount_received"] / (df["amount_paid"] + 1e-6)
        df["currency_match"] = (df["receiving_currency"] == df["payment_currency"]).astype(np.int8)
        df["same_bank"] = (df["from_bank"] == df["to_bank"]).astype(np.int8)
        
        # 4. Sender Behavioral Aggregations
        sender_grp = df.groupby("sender_account").agg(
            sender_transaction_count=("sender_account", "size"),
            sender_total_amount=("amount_paid", "sum"),
            sender_avg_amount=("amount_paid", "mean"),
            sender_max_amount=("amount_paid", "max"),
            sender_unique_receivers=("receiver_account", "nunique"),
            sender_unique_banks=("to_bank", "nunique")
        ).reset_index()
        
        # 5. Receiver Behavioral Aggregations
        receiver_grp = df.groupby("receiver_account").agg(
            receiver_transaction_count=("receiver_account", "size"),
            receiver_total_amount=("amount_received", "sum"),
            receiver_avg_amount=("amount_received", "mean"),
            receiver_max_amount=("amount_received", "max"),
            receiver_unique_senders=("sender_account", "nunique"),
            receiver_unique_banks=("from_bank", "nunique")
        ).reset_index()
        
        # Merge aggregates back to dataframe
        # First drop conflicting columns if they exist in raw data
        drop_cols = [c for c in sender_grp.columns if c != "sender_account" and c in df.columns]
        if drop_cols:
            df = df.drop(columns=drop_cols)
            
        drop_cols_rec = [c for c in receiver_grp.columns if c != "receiver_account" and c in df.columns]
        if drop_cols_rec:
            df = df.drop(columns=drop_cols_rec)
            
        df = df.merge(sender_grp, on="sender_account", how="left")
        df = df.merge(receiver_grp, on="receiver_account", how="left")
        
        # 6. Time delta velocity
        df["seconds_since_previous"] = df.groupby("sender_account")["timestamp"].diff().dt.total_seconds()
        df["seconds_since_previous"] = df["seconds_since_previous"].fillna(999999)
        
        # Extract target transaction row
        target_row = df[df["transaction_id"] == target_tx["transaction_id"]].copy()
        if target_row.empty:
            # Fallback just in case
            target_row = df.tail(1).copy()
            
        # 7. Apply distinct encodings
        target_lgb = target_row[self.features].copy()
        target_if = target_row[self.features].copy()
        
        # LightGBM encoding
        for col in self.cat_cols:
            mapping = self.lgb_encoders[col]
            target_lgb[col] = target_lgb[col].map(mapping).fillna(-1).astype(np.int64)
            
        # Isolation Forest encoding
        for col in self.cat_cols:
            mapping = self.if_encoders[col]
            target_if[col] = target_if[col].map(mapping).fillna(-1).astype(np.int64)
            
        # Force numeric types
        for col in self.features:
            target_lgb[col] = pd.to_numeric(target_lgb[col], errors="coerce").astype(float)
            target_if[col] = pd.to_numeric(target_if[col], errors="coerce").astype(float)
            
        return target_lgb, target_if
