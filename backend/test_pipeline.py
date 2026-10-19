import os
import joblib
import pandas as pd
import numpy as np
from feature_pipeline import FeaturePipeline

# Paths to models
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
LGB_MODEL_PATH = os.path.join(MODELS_DIR, "muleguard_lightgbm.pkl")
IF_MODEL_PATH = os.path.join(MODELS_DIR, "muleguard_isolation_forest.pkl")

def main():
    print("==================================================")
    # 1. Initialize Pipeline
    print("1. Initializing Feature Pipeline...")
    pipeline = FeaturePipeline()
    print("Features expected by LGB:", len(pipeline.features))
    print("Categorical features:", pipeline.cat_cols)
    
    # 2. Define target transaction (synthetic representation)
    print("\n2. Defining sample transaction...")
    target_tx = {
        "transaction_id": "TX-99999",
        "timestamp": "2026-08-22 14:30:00",
        "sender_account": "ACC-10293",
        "receiver_account": "ACC-4412",
        "from_bank": 117,
        "to_bank": 23,
        "amount_received": 75000.0,
        "amount_paid": 75000.0,
        "receiving_currency": "Euro",
        "payment_currency": "Euro",
        "payment_format": "Cheque"
    }
    
    # Define some historical transactions to build grouping statistics
    history_txs = [
        # ACC-10293 outgoing history
        {"transaction_id": "TX-10001", "timestamp": "2026-08-22 10:00:00", "sender_account": "ACC-10293", "receiver_account": "ACC-4412", "from_bank": 117, "to_bank": 23, "amount_received": 12000.0, "amount_paid": 12000.0, "receiving_currency": "Euro", "payment_currency": "Euro", "payment_format": "Cheque"},
        {"transaction_id": "TX-10002", "timestamp": "2026-08-22 12:00:00", "sender_account": "ACC-10293", "receiver_account": "ACC-8888", "from_bank": 117, "to_bank": 99, "amount_received": 25000.0, "amount_paid": 25000.0, "receiving_currency": "Euro", "payment_currency": "Euro", "payment_format": "Wire"},
        # ACC-4412 incoming history
        {"transaction_id": "TX-10003", "timestamp": "2026-08-22 11:00:00", "sender_account": "ACC-9999", "receiver_account": "ACC-4412", "from_bank": 10, "to_bank": 23, "amount_received": 5000.0, "amount_paid": 5000.0, "receiving_currency": "Euro", "payment_currency": "Euro", "payment_format": "Cheque"},
    ]
    
    # 3. Extract features
    print("\n3. Engineering features...")
    X_lgb, X_if = pipeline.build_features(target_tx, history_txs)
    
    print("\nEngineered LGB Row Shape:", X_lgb.shape)
    print("Engineered IF Row Shape:", X_if.shape)
    
    # 4. Load Models
    print(f"\n4. Loading pre-trained models from {MODELS_DIR}...")
    lgb_model = joblib.load(LGB_MODEL_PATH)
    if_model = joblib.load(IF_MODEL_PATH)
    print("Models loaded successfully!")
    
    # 5. Predict risk probability
    print("\n5. Running LightGBM Classifier inference...")
    # LGB expects 2D matrix. Use predict directly if predict_proba is not available
    if hasattr(lgb_model, "predict_proba"):
        p = lgb_model.predict_proba(X_lgb.values)[:, 1][0]
    else:
        p = lgb_model.predict(X_lgb.values)[0]
    risk_score = p * 100
    print(f"Risk Probability: {p:.8f}")
    print(f"Risk Score: {risk_score:.2f}/100")
    
    # 6. Predict anomalies
    print("\n6. Running Isolation Forest anomaly detection...")
    decision_score = if_model.decision_function(X_if.values)[0]
    anomaly_score = -decision_score
    print(f"Decision Score (IF): {decision_score:.8f}")
    print(f"Anomaly Score (IF): {anomaly_score:.8f}")
    
    # 7. Extract SHAP explanations using native LightGBM pred_contrib
    print("\n7. Extracting native SHAP values...")
    # Since lgb_model is a native Booster, use it directly
    shap_raw = lgb_model.predict(X_lgb.values, pred_contrib=True)
    shap_raw = np.asarray(shap_raw)
    
    shap_values = shap_raw[0, :-1]
    bias = shap_raw[0, -1]
    print(f"SHAP Values vector length: {len(shap_values)}")
    print(f"Base Bias: {bias:.6f}")
    
    # Get top contributing features
    top_indices = np.argsort(np.abs(shap_values))[::-1][:5]
    print("\nTop 5 Contributing Features:")
    for rank, idx in enumerate(top_indices, start=1):
        feature_name = pipeline.features[idx]
        val = X_lgb.iloc[0, idx]
        shap_val = shap_values[idx]
        direction = "INCREASES RISK" if shap_val > 0 else "DECREASES RISK"
        print(f" {rank}. {feature_name:<28} | value={val:<10} | SHAP={shap_val: .6f} ({direction})")
        
    print("\n==================================================")
    print("PIPELINE TEST PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    main()
