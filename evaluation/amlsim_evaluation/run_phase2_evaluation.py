"""
FinGuard AI — Phase 2 Evaluation & Model Training Runner
Executes:
1. Full dataset point-in-time feature extraction with simultaneous-batch semantics
2. Chronological partitioning (Train, Validation, Test)
3. Zero-shot diagnostic baseline evaluation with Validation-only threshold tuning
4. Clean experimental LightGBM training on Train partition with early stopping on Validation
5. Validation-only threshold tuning for experimental model
6. Test evaluation of both models on overall test set and unseen entity subsets
7. Complete metrics computation and export to phase2_results.json
"""

import os
import sys
import time
import json
import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    confusion_matrix,
    matthews_corrcoef
)

# Add local path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_engine import (
    PointInTimeFeatureEngine,
    FEATURE_COLUMNS,
    CATEGORICAL_FEATURES
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "data", "aml_dataset", "HI-Small_Trans.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
PROD_MODEL_PATH = os.path.join(MODELS_DIR, "muleguard_lightgbm.pkl")
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
RESULTS_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase2_results.json")

def find_best_threshold(y_true, y_probs, metric="f1"):
    """
    Finds the optimal threshold on validation data.
    Evaluates thresholds from 0.01 to 0.99 in steps of 0.01.
    """
    best_thresh = 0.5
    best_score = -1.0
    best_metrics = {}

    thresholds = np.linspace(0.01, 0.99, 99)
    for t in thresholds:
        y_pred = (y_probs >= t).astype(int)
        if metric == "f1":
            score = f1_score(y_true, y_pred, zero_division=0)
        elif metric == "mcc":
            score = matthews_corrcoef(y_true, y_pred)
        else:
            score = f1_score(y_true, y_pred, zero_division=0)

        if score > best_score:
            best_score = score
            best_thresh = t

    # Compute metrics at best threshold
    y_pred_best = (y_probs >= best_thresh).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred_best).ravel()
    best_metrics = {
        "threshold": float(best_thresh),
        "f1": float(f1_score(y_true, y_pred_best, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred_best, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred_best, zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred_best)),
        "specificity": float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,
        "mcc": float(matthews_corrcoef(y_true, y_pred_best)),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn)
    }
    return float(best_thresh), best_metrics

def evaluate_predictions(y_true, y_probs, threshold):
    """
    Computes all standard metrics given true labels, predicted probabilities, and a frozen threshold.
    """
    y_pred = (y_probs >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    roc_auc = float(roc_auc_score(y_true, y_probs)) if len(np.unique(y_true)) > 1 else 0.0
    pr_auc = float(average_precision_score(y_true, y_probs)) if len(np.unique(y_true)) > 1 else 0.0

    return {
        "threshold": float(threshold),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "specificity": float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "confusion_matrix": {
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn)
        },
        "total_samples": int(len(y_true)),
        "positive_samples": int(y_true.sum()),
        "prevalence_pct": float(y_true.mean() * 100)
    }

def run_phase2():
    start_total_time = time.time()
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    results = {}

    print("=================================================================")
    print(" FinGuard AI — Phase 2 Leakage-Free Pipeline & Model Evaluation  ")
    print("=================================================================")

    # 1. Load raw dataset
    print(f"\n[1/6] Loading raw dataset from {DATA_PATH}...")
    t0 = time.time()
    raw_df = pd.read_csv(DATA_PATH, dtype={
        "From Bank": "int64",
        "To Bank": "int64",
        "Account": "str",
        "Account.1": "str",
        "Amount Received": "float64",
        "Amount Paid": "float64",
        "Receiving Currency": "str",
        "Payment Currency": "str",
        "Payment Format": "str",
        "Is Laundering": "int8"
    })
    load_time = time.time() - t0
    print(f"Loaded {len(raw_df):,} rows in {load_time:.2f}s.")

    # 2. Extract features through PointInTimeFeatureEngine
    print("\n[2/6] Running Point-in-Time Feature Engine (timestamp-batch processing)...")
    t1 = time.time()
    engine = PointInTimeFeatureEngine()
    features_df, meta_df = engine.process_dataframe(raw_df, is_sorted=False, preserve_order=False)
    feat_time = time.time() - t1
    print(f"Feature engineering completed for {len(features_df):,} rows in {feat_time:.2f}s.")

    # Convert categorical columns to 'category' dtype for LightGBM
    for col in CATEGORICAL_FEATURES:
        features_df[col] = features_df[col].astype("category")

    # 3. Partition chronologically
    print("\n[3/6] Partitioning chronologically into Train, Validation, and Test...")
    c_val = pd.to_datetime("2022-09-08 00:00:00")
    c_test = pd.to_datetime("2022-09-09 18:00:00")

    dt_series = meta_df["dt"]
    train_mask = (dt_series < c_val)
    val_mask = ((dt_series >= c_val) & (dt_series < c_test))
    test_mask = (dt_series >= c_test)

    X_train = features_df[train_mask].reset_index(drop=True)
    y_train = meta_df.loc[train_mask, "Is Laundering"].values

    X_val = features_df[val_mask].reset_index(drop=True)
    y_val = meta_df.loc[val_mask, "Is Laundering"].values

    X_test = features_df[test_mask].reset_index(drop=True)
    y_test = meta_df.loc[test_mask, "Is Laundering"].values
    test_meta = meta_df[test_mask].reset_index(drop=True)

    # Identify unseen entity subsets in Test
    train_senders = set(meta_df.loc[train_mask, "Account"].unique())
    train_receivers = set(meta_df.loc[train_mask, "Account.1"].unique())

    test_sender_unseen_mask = ~test_meta["Account"].isin(train_senders)
    test_receiver_unseen_mask = ~test_meta["Account.1"].isin(train_receivers)
    test_any_unseen_mask = test_sender_unseen_mask | test_receiver_unseen_mask

    print(f"Train set:      {len(X_train):,} rows ({y_train.sum():,} pos, {y_train.mean()*100:.4f}% prev)")
    print(f"Validation set: {len(X_val):,} rows ({y_val.sum():,} pos, {y_val.mean()*100:.4f}% prev)")
    print(f"Test set:       {len(X_test):,} rows ({y_test.sum():,} pos, {y_test.mean()*100:.4f}% prev)")
    print(f"  - Sender-unseen test slice:   {test_sender_unseen_mask.sum():,} rows ({y_test[test_sender_unseen_mask].sum()} pos)")
    print(f"  - Receiver-unseen test slice: {test_receiver_unseen_mask.sum():,} rows ({y_test[test_receiver_unseen_mask].sum()} pos)")
    print(f"  - Any-unseen test slice:      {test_any_unseen_mask.sum():,} rows ({y_test[test_any_unseen_mask].sum()} pos)")

    results["partitions"] = {
        "train": {"rows": len(X_train), "pos": int(y_train.sum()), "neg": int(len(X_train) - y_train.sum()), "prev_pct": float(y_train.mean()*100)},
        "val":   {"rows": len(X_val),   "pos": int(y_val.sum()),   "neg": int(len(X_val) - y_val.sum()),   "prev_pct": float(y_val.mean()*100)},
        "test":  {"rows": len(X_test),  "pos": int(y_test.sum()),  "neg": int(len(X_test) - y_test.sum()),  "prev_pct": float(y_test.mean()*100)},
        "test_subsets": {
            "sender_unseen":   {"rows": int(test_sender_unseen_mask.sum()),   "pos": int(y_test[test_sender_unseen_mask].sum())},
            "receiver_unseen": {"rows": int(test_receiver_unseen_mask.sum()), "pos": int(y_test[test_receiver_unseen_mask].sum())},
            "any_unseen":      {"rows": int(test_any_unseen_mask.sum()),      "pos": int(y_test[test_any_unseen_mask].sum())}
        }
    }

    # 4. Zero-Shot Diagnostic Baseline Evaluation
    print("\n[4/6] Evaluating Zero-Shot Diagnostic Baseline (Production Model)...")
    prod_model = joblib.load(PROD_MODEL_PATH)

    print("  Predicting on Validation set...")
    val_probs_zero_shot = prod_model.predict(X_val)

    # Calibrate threshold on Validation set only
    val_best_thresh_zs, val_metrics_zs = find_best_threshold(y_val, val_probs_zero_shot, metric="f1")
    print(f"  Validation-calibrated optimal threshold: {val_best_thresh_zs:.4f} (Val F1: {val_metrics_zs['f1']:.4f}, Precision: {val_metrics_zs['precision']:.4f}, Recall: {val_metrics_zs['recall']:.4f})")

    # Evaluate frozen threshold on Test set
    print("  Evaluating frozen threshold on Test set...")
    test_probs_zero_shot = prod_model.predict(X_test)
    test_eval_zs = evaluate_predictions(y_test, test_probs_zero_shot, val_best_thresh_zs)

    # Evaluate on subsets
    test_eval_zs_sender_unseen = evaluate_predictions(y_test[test_sender_unseen_mask], test_probs_zero_shot[test_sender_unseen_mask], val_best_thresh_zs)
    test_eval_zs_receiver_unseen = evaluate_predictions(y_test[test_receiver_unseen_mask], test_probs_zero_shot[test_receiver_unseen_mask], val_best_thresh_zs)
    test_eval_zs_any_unseen = evaluate_predictions(y_test[test_any_unseen_mask], test_probs_zero_shot[test_any_unseen_mask], val_best_thresh_zs)

    print(f"  Zero-Shot Test PR-AUC:  {test_eval_zs['pr_auc']:.4f}")
    print(f"  Zero-Shot Test ROC-AUC: {test_eval_zs['roc_auc']:.4f}")
    print(f"  Zero-Shot Test F1:      {test_eval_zs['f1']:.4f} (Precision: {test_eval_zs['precision']:.4f}, Recall: {test_eval_zs['recall']:.4f})")
    print(f"  Zero-Shot Test False Positives: {test_eval_zs['confusion_matrix']['fp']:,}")

    results["zero_shot_baseline"] = {
        "status": "EVALUATED",
        "validation_calibrated_threshold": val_best_thresh_zs,
        "validation_metrics": val_metrics_zs,
        "test_overall": test_eval_zs,
        "test_sender_unseen": test_eval_zs_sender_unseen,
        "test_receiver_unseen": test_eval_zs_receiver_unseen,
        "test_any_unseen": test_eval_zs_any_unseen
    }

    # 5. Experimental Model Training
    print("\n[5/6] Training Experimental LightGBM on Clean Train Partition...")
    scale_pos_weight = float((len(y_train) - y_train.sum()) / y_train.sum())
    print(f"  Calculated scale_pos_weight: {scale_pos_weight:.2f}")

    params = {
        "objective": "binary",
        "metric": "average_precision",
        "learning_rate": 0.05,
        "num_leaves": 63,
        "max_depth": -1,
        "min_child_samples": 100,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "lambda_l1": 0.1,
        "lambda_l2": 1.0,
        "scale_pos_weight": scale_pos_weight,
        "verbosity": -1,
        "n_jobs": -1,
        "seed": 42
    }

    train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=CATEGORICAL_FEATURES, free_raw_data=False)
    val_data = lgb.Dataset(X_val, label=y_val, categorical_feature=CATEGORICAL_FEATURES, reference=train_data, free_raw_data=False)

    t_train_start = time.time()
    exp_model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, val_data],
        valid_names=["train", "validation"],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50, verbose=True),
            lgb.log_evaluation(period=50)
        ]
    )
    train_duration = time.time() - t_train_start
    print(f"Experimental model training complete in {train_duration:.2f}s (Best iteration: {exp_model.best_iteration})")

    # Save experimental artifacts
    exp_txt_path = os.path.join(ARTIFACTS_DIR, "experimental_lightgbm.txt")
    exp_pkl_path = os.path.join(ARTIFACTS_DIR, "experimental_lightgbm.pkl")
    exp_cfg_path = os.path.join(ARTIFACTS_DIR, "experimental_config.json")

    exp_model.save_model(exp_txt_path)
    joblib.dump(exp_model, exp_pkl_path)

    feature_importances_split = exp_model.feature_importance(importance_type="split")
    feature_importances_gain = exp_model.feature_importance(importance_type="gain")
    importance_dict = {
        col: {"split": int(s), "gain": float(g)}
        for col, s, g in zip(FEATURE_COLUMNS, feature_importances_split, feature_importances_gain)
    }

    with open(exp_cfg_path, "w") as f:
        json.dump({
            "model": "Experimental_LightGBM_LeakageFree",
            "best_iteration": int(exp_model.best_iteration),
            "num_features": 26,
            "scale_pos_weight": scale_pos_weight,
            "train_duration_seconds": round(train_duration, 2),
            "feature_importances": importance_dict
        }, f, indent=2)

    # 6. Evaluate Experimental Model
    print("\n[6/6] Evaluating Experimental Model on Validation and Held-Out Test Set...")
    val_probs_exp = exp_model.predict(X_val)

    # Calibrate threshold on Validation set only
    val_best_thresh_exp, val_metrics_exp = find_best_threshold(y_val, val_probs_exp, metric="f1")
    print(f"  Experimental Validation-calibrated optimal threshold: {val_best_thresh_exp:.4f} (Val F1: {val_metrics_exp['f1']:.4f}, Precision: {val_metrics_exp['precision']:.4f}, Recall: {val_metrics_exp['recall']:.4f})")

    # Evaluate frozen threshold on Test set
    test_probs_exp = exp_model.predict(X_test)
    test_eval_exp = evaluate_predictions(y_test, test_probs_exp, val_best_thresh_exp)

    # Evaluate on subsets
    test_eval_exp_sender_unseen = evaluate_predictions(y_test[test_sender_unseen_mask], test_probs_exp[test_sender_unseen_mask], val_best_thresh_exp)
    test_eval_exp_receiver_unseen = evaluate_predictions(y_test[test_receiver_unseen_mask], test_probs_exp[test_receiver_unseen_mask], val_best_thresh_exp)
    test_eval_exp_any_unseen = evaluate_predictions(y_test[test_any_unseen_mask], test_probs_exp[test_any_unseen_mask], val_best_thresh_exp)

    print(f"  Experimental Test PR-AUC:  {test_eval_exp['pr_auc']:.4f}")
    print(f"  Experimental Test ROC-AUC: {test_eval_exp['roc_auc']:.4f}")
    print(f"  Experimental Test F1:      {test_eval_exp['f1']:.4f} (Precision: {test_eval_exp['precision']:.4f}, Recall: {test_eval_exp['recall']:.4f})")
    print(f"  Experimental Test False Positives: {test_eval_exp['confusion_matrix']['fp']:,}")

    results["experimental_model"] = {
        "status": "TRAINED_AND_EVALUATED",
        "best_iteration": int(exp_model.best_iteration),
        "validation_calibrated_threshold": val_best_thresh_exp,
        "validation_metrics": val_metrics_exp,
        "test_overall": test_eval_exp,
        "test_sender_unseen": test_eval_exp_sender_unseen,
        "test_receiver_unseen": test_eval_exp_receiver_unseen,
        "test_any_unseen": test_eval_exp_any_unseen,
        "feature_importances": importance_dict
    }

    # Head-to-Head Comparison
    results["comparison"] = {
        "pr_auc": {
            "zero_shot_baseline": test_eval_zs["pr_auc"],
            "experimental_model": test_eval_exp["pr_auc"],
            "delta": round(test_eval_exp["pr_auc"] - test_eval_zs["pr_auc"], 4)
        },
        "roc_auc": {
            "zero_shot_baseline": test_eval_zs["roc_auc"],
            "experimental_model": test_eval_exp["roc_auc"],
            "delta": round(test_eval_exp["roc_auc"] - test_eval_zs["roc_auc"], 4)
        },
        "f1": {
            "zero_shot_baseline": test_eval_zs["f1"],
            "experimental_model": test_eval_exp["f1"],
            "delta": round(test_eval_exp["f1"] - test_eval_zs["f1"], 4)
        },
        "precision": {
            "zero_shot_baseline": test_eval_zs["precision"],
            "experimental_model": test_eval_exp["precision"],
            "delta": round(test_eval_exp["precision"] - test_eval_zs["precision"], 4)
        },
        "recall": {
            "zero_shot_baseline": test_eval_zs["recall"],
            "experimental_model": test_eval_exp["recall"],
            "delta": round(test_eval_exp["recall"] - test_eval_zs["recall"], 4)
        },
        "false_positives": {
            "zero_shot_baseline": test_eval_zs["confusion_matrix"]["fp"],
            "experimental_model": test_eval_exp["confusion_matrix"]["fp"],
            "delta": int(test_eval_exp["confusion_matrix"]["fp"] - test_eval_zs["confusion_matrix"]["fp"])
        }
    }

    total_duration = time.time() - start_total_time
    results["metadata"] = {
        "execution_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_duration_seconds": round(total_duration, 2),
        "data_loading_seconds": round(load_time, 2),
        "feature_engineering_seconds": round(feat_time, 2),
        "training_seconds": round(train_duration, 2)
    }

    with open(RESULTS_JSON_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nPhase 2 Evaluation successfully completed in {total_duration:.2f}s!")
    print(f"Results saved to {RESULTS_JSON_PATH}")

if __name__ == "__main__":
    run_phase2()
