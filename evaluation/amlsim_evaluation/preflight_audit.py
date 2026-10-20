"""
FinGuard AI — IBM AML Dataset Pre-Flight Audit Script
Phase 1: Read-only dataset verification, statistical profiling, chronological split audit,
entity overlap analysis, and 26-feature contract verification.

Safe, read-only script. Does NOT train models, modify models, or write to database.
"""

import os
import sys
import json
import hashlib
import time
from datetime import datetime
from collections import Counter
import pickle
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "aml_dataset")
TARGET_CSV = os.path.join(DATA_DIR, "HI-Small_Trans.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUT_JSON = os.path.join(BASE_DIR, "evaluation", "amlsim_evaluation", "preflight_results.json")

def compute_hashes(filepath, chunk_size=65536):
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()

def inspect_directory():
    print("--- 1. Inspecting Dataset Directory ---")
    files_info = []
    for root, dirs, files in os.walk(DATA_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, BASE_DIR)
            stat = os.stat(full_path)
            files_info.append({
                "path": rel_path.replace("\\", "/"),
                "name": f,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
    files_info.sort(key=lambda x: x["path"])
    return files_info

def run_preflight():
    start_time = time.time()
    results = {}

    # 1. Directory Inventory
    files_info = inspect_directory()
    results["inventory"] = files_info
    print(f"Found {len(files_info)} dataset artifacts.")

    # Hashes for HI-Small files
    print("\nComputing checksums for HI-Small target files...")
    target_files = [
        "HI-Small_Trans.csv",
        "HI-Small_accounts.csv",
        "HI-Small_Patterns.txt"
    ]
    checksums = {}
    for tf in target_files:
        full_tf = os.path.join(DATA_DIR, tf)
        if os.path.exists(full_tf):
            print(f"  Hashing {tf}...")
            md5_val, sha256_val = compute_hashes(full_tf)
            checksums[tf] = {
                "md5": md5_val,
                "sha256": sha256_val,
                "size_bytes": os.path.getsize(full_tf)
            }
    results["checksums"] = checksums

    # 2. Inspect category encoders and feature contract
    print("\n--- 2. Inspecting Production Feature Contract & Encoders ---")
    with open(os.path.join(MODELS_DIR, "feature_columns.json"), "r") as f:
        feature_columns = json.load(f)
    with open(os.path.join(MODELS_DIR, "category_encoders.pkl"), "rb") as f:
        category_encoders = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "isolation_category_mappings.json"), "r") as f:
        isolation_mappings = json.load(f)
    
    results["production_contract"] = {
        "num_features": len(feature_columns),
        "features": feature_columns,
        "encoders": {k: list(v.keys()) for k, v in category_encoders.items()}
    }

    # 3. Statistical Profiling of HI-Small_Trans.csv
    print(f"\n--- 3. Profiling {TARGET_CSV} ---")
    if not os.path.exists(TARGET_CSV):
        raise FileNotFoundError(f"Target dataset {TARGET_CSV} does not exist.")

    # Read raw header
    with open(TARGET_CSV, "r", encoding="utf-8") as f:
        raw_header_line = f.readline().strip()
    raw_columns = raw_header_line.split(",")
    print(f"Raw header columns ({len(raw_columns)}): {raw_columns}")

    chunk_size = 500_000
    total_rows = 0
    null_counts = Counter()
    label_counts = Counter()
    
    unique_from_banks = set()
    unique_to_banks = set()
    unique_rec_currencies = set()
    unique_pay_currencies = set()
    unique_pay_formats = set()
    
    # Numerical aggregations for Amount Received and Amount Paid
    amt_rec_stats = {"count": 0, "sum": 0.0, "sq_sum": 0.0, "min": float("inf"), "max": float("-inf"), "zeros": 0, "negatives": 0}
    amt_paid_stats = {"count": 0, "sum": 0.0, "sq_sum": 0.0, "min": float("inf"), "max": float("-inf"), "zeros": 0, "negatives": 0}
    
    currency_matches = 0
    currency_mismatches = 0
    
    min_ts = None
    max_ts = None
    
    timestamp_counts = Counter()
    
    # Chronological Split Counts:
    # Train: ts < 2022-09-08 00:00:00
    # Val: 2022-09-08 00:00:00 <= ts < 2022-09-09 18:00:00
    # Test: ts >= 2022-09-09 18:00:00
    split_cut_val = "2022/09/08 00:00"
    split_cut_test = "2022/09/09 18:00"
    
    splits = {
        "train": {"rows": 0, "pos": 0, "neg": 0, "min_ts": None, "max_ts": None, "accounts": set(), "laundering_accounts": set()},
        "val":   {"rows": 0, "pos": 0, "neg": 0, "min_ts": None, "max_ts": None, "accounts": set(), "laundering_accounts": set()},
        "test":  {"rows": 0, "pos": 0, "neg": 0, "min_ts": None, "max_ts": None, "accounts": set(), "laundering_accounts": set()}
    }
    
    # Track duplicates across a sample or hash set
    # Using hash of key fields for duplicate check
    row_hash_set = set()
    num_exact_duplicates = 0
    key_hash_set = set()
    num_key_duplicates = 0

    chunk_idx = 0
    for chunk in pd.read_csv(TARGET_CSV, chunksize=chunk_size, dtype={
        "From Bank": str,
        "Account": str,
        "To Bank": str,
        "Account.1": str,
        "Receiving Currency": str,
        "Payment Currency": str,
        "Payment Format": str
    }):
        chunk_idx += 1
        num_chunk_rows = len(chunk)
        total_rows += num_chunk_rows
        print(f"  Processing chunk {chunk_idx}: {total_rows:,} rows processed...")

        # Nulls
        for col in chunk.columns:
            null_counts[col] += int(chunk[col].isnull().sum())

        # Timestamps
        c_min_ts = chunk["Timestamp"].min()
        c_max_ts = chunk["Timestamp"].max()
        if min_ts is None or c_min_ts < min_ts: min_ts = c_min_ts
        if max_ts is None or c_max_ts > max_ts: max_ts = c_max_ts

        # Collisions
        for ts, cnt in chunk["Timestamp"].value_counts().items():
            timestamp_counts[ts] += cnt

        # Labels
        for lbl, cnt in chunk["Is Laundering"].value_counts().items():
            label_counts[str(lbl)] += int(cnt)

        # Categoricals
        unique_from_banks.update(chunk["From Bank"].dropna().unique())
        unique_to_banks.update(chunk["To Bank"].dropna().unique())
        unique_rec_currencies.update(chunk["Receiving Currency"].dropna().unique())
        unique_pay_currencies.update(chunk["Payment Currency"].dropna().unique())
        unique_pay_formats.update(chunk["Payment Format"].dropna().unique())

        # Currency matching
        curr_eq = (chunk["Receiving Currency"] == chunk["Payment Currency"])
        currency_matches += int(curr_eq.sum())
        currency_mismatches += int((~curr_eq).sum())

        # Numericals - Amount Received
        rec_vals = chunk["Amount Received"].dropna().values
        amt_rec_stats["count"] += len(rec_vals)
        amt_rec_stats["sum"] += float(rec_vals.sum())
        amt_rec_stats["sq_sum"] += float((rec_vals ** 2).sum())
        amt_rec_stats["min"] = min(amt_rec_stats["min"], float(rec_vals.min()) if len(rec_vals) else amt_rec_stats["min"])
        amt_rec_stats["max"] = max(amt_rec_stats["max"], float(rec_vals.max()) if len(rec_vals) else amt_rec_stats["max"])
        amt_rec_stats["zeros"] += int((rec_vals == 0).sum())
        amt_rec_stats["negatives"] += int((rec_vals < 0).sum())

        # Numericals - Amount Paid
        paid_vals = chunk["Amount Paid"].dropna().values
        amt_paid_stats["count"] += len(paid_vals)
        amt_paid_stats["sum"] += float(paid_vals.sum())
        amt_paid_stats["sq_sum"] += float((paid_vals ** 2).sum())
        amt_paid_stats["min"] = min(amt_paid_stats["min"], float(paid_vals.min()) if len(paid_vals) else amt_paid_stats["min"])
        amt_paid_stats["max"] = max(amt_paid_stats["max"], float(paid_vals.max()) if len(paid_vals) else amt_paid_stats["max"])
        amt_paid_stats["zeros"] += int((paid_vals == 0).sum())
        amt_paid_stats["negatives"] += int((paid_vals < 0).sum())

        # Split assignment & Entity tracking
        # Format in CSV is YYYY/MM/DD HH:MM
        ts_series = chunk["Timestamp"]
        lbl_series = chunk["Is Laundering"]
        
        # Accounts (unique account ID or Bank+Account)
        senders = chunk["Account"].astype(str)
        receivers = chunk["Account.1"].astype(str)

        train_mask = (ts_series < split_cut_val)
        val_mask = ((ts_series >= split_cut_val) & (ts_series < split_cut_test))
        test_mask = (ts_series >= split_cut_test)

        for mask, name in [(train_mask, "train"), (val_mask, "val"), (test_mask, "test")]:
            sub = chunk[mask]
            if len(sub) == 0:
                continue
            splits[name]["rows"] += len(sub)
            sub_lbls = sub["Is Laundering"].value_counts()
            splits[name]["pos"] += int(sub_lbls.get(1, 0))
            splits[name]["neg"] += int(sub_lbls.get(0, 0))
            
            s_min = sub["Timestamp"].min()
            s_max = sub["Timestamp"].max()
            if splits[name]["min_ts"] is None or s_min < splits[name]["min_ts"]: splits[name]["min_ts"] = s_min
            if splits[name]["max_ts"] is None or s_max > splits[name]["max_ts"]: splits[name]["max_ts"] = s_max

            # Unique entities in this split
            sub_accs = set(sub["Account"].dropna().unique()).union(set(sub["Account.1"].dropna().unique()))
            splits[name]["accounts"].update(sub_accs)
            
            # Laundering entities
            sub_pos = sub[sub["Is Laundering"] == 1]
            if len(sub_pos) > 0:
                pos_accs = set(sub_pos["Account"].dropna().unique()).union(set(sub_pos["Account.1"].dropna().unique()))
                splits[name]["laundering_accounts"].update(pos_accs)

        # Duplicate checking via fast integer hashing
        # 1. Exact row duplicate:
        # We can check duplicates by subsetting keys: Timestamp, From Bank, Account, To Bank, Account.1, Amount Paid, Payment Format
        row_tuples = list(zip(chunk["Timestamp"], chunk["From Bank"], chunk["Account"], chunk["To Bank"], chunk["Account.1"], chunk["Amount Paid"], chunk["Payment Format"]))
        for rt in row_tuples:
            h = hash(rt)
            if h in row_hash_set:
                num_exact_duplicates += 1
            else:
                row_hash_set.add(h)
        
        # 2. Key collision (Timestamp, From Bank, Account, To Bank, Account.1)
        key_tuples = list(zip(chunk["Timestamp"], chunk["From Bank"], chunk["Account"], chunk["To Bank"], chunk["Account.1"]))
        for kt in key_tuples:
            kh = hash(kt)
            if kh in key_hash_set:
                num_key_duplicates += 1
            else:
                key_hash_set.add(kh)

    # Compute numerical mean and std
    rec_mean = amt_rec_stats["sum"] / amt_rec_stats["count"] if amt_rec_stats["count"] else 0
    rec_var = (amt_rec_stats["sq_sum"] / amt_rec_stats["count"]) - (rec_mean ** 2) if amt_rec_stats["count"] else 0
    rec_std = np.sqrt(max(0.0, rec_var))
    
    paid_mean = amt_paid_stats["sum"] / amt_paid_stats["count"] if amt_paid_stats["count"] else 0
    paid_var = (amt_paid_stats["sq_sum"] / amt_paid_stats["count"]) - (paid_mean ** 2) if amt_paid_stats["count"] else 0
    paid_std = np.sqrt(max(0.0, paid_var))

    # Timestamp collision analysis
    collision_counts = [cnt for cnt in timestamp_counts.values() if cnt > 1]
    collision_timestamps = len(collision_counts)
    max_batch_size = max(timestamp_counts.values()) if timestamp_counts else 0
    total_unique_timestamps = len(timestamp_counts)

    # Categorical verification against category_encoders.pkl
    known_rec_curr = set(category_encoders["receiving_currency"].keys())
    known_pay_curr = set(category_encoders["payment_currency"].keys())
    known_pay_fmt = set(category_encoders["payment_format"].keys())

    unseen_rec_curr = unique_rec_currencies - known_rec_curr
    unseen_pay_curr = unique_pay_currencies - known_pay_curr
    unseen_pay_fmt = unique_pay_formats - known_pay_fmt

    # Entity overlap calculations
    train_accs = splits["train"]["accounts"]
    val_accs = splits["val"]["accounts"]
    test_accs = splits["test"]["accounts"]
    
    all_unique_accounts = train_accs.union(val_accs).union(test_accs)
    
    train_val_overlap = len(train_accs.intersection(val_accs))
    train_test_overlap = len(train_accs.intersection(test_accs))
    val_test_overlap = len(val_accs.intersection(test_accs))
    all_three_overlap = len(train_accs.intersection(val_accs).intersection(test_accs))
    
    test_only_accounts = len(test_accs - train_accs - val_accs)
    train_only_accounts = len(train_accs - val_accs - test_accs)
    val_only_accounts = len(val_accs - train_accs - test_accs)
    
    # Laundering accounts overlap
    train_launderers = splits["train"]["laundering_accounts"]
    val_launderers = splits["val"]["laundering_accounts"]
    test_launderers = splits["test"]["laundering_accounts"]
    all_launderers = train_launderers.union(val_launderers).union(test_launderers)
    test_launderers_seen_in_train = len(test_launderers.intersection(train_launderers))
    test_launderers_seen_in_val = len(test_launderers.intersection(val_launderers))
    test_launderers_unseen = len(test_launderers - train_launderers - val_launderers)

    # Format results
    results["profiling"] = {
        "total_rows": total_rows,
        "raw_columns": raw_columns,
        "pandas_columns": ["Timestamp", "From Bank", "Account", "To Bank", "Account.1", "Amount Received", "Receiving Currency", "Amount Paid", "Payment Currency", "Payment Format", "Is Laundering"],
        "null_counts": dict(null_counts),
        "duplicates": {
            "exact_transaction_duplicates": num_exact_duplicates,
            "key_pair_timestamp_duplicates": num_key_duplicates
        },
        "timestamps": {
            "min_timestamp": min_ts,
            "max_timestamp": max_ts,
            "unique_timestamps": total_unique_timestamps,
            "collision_timestamps_count": collision_timestamps,
            "max_transactions_per_timestamp": max_batch_size,
            "sample_collision_batch_sizes": {
                "p50": float(np.percentile(collision_counts, 50)) if collision_counts else 0,
                "p90": float(np.percentile(collision_counts, 90)) if collision_counts else 0,
                "p99": float(np.percentile(collision_counts, 99)) if collision_counts else 0,
                "max": max_batch_size
            }
        },
        "target": {
            "negative_count": label_counts.get("0", 0),
            "positive_count": label_counts.get("1", 0),
            "negative_ratio_pct": round(label_counts.get("0", 0) / total_rows * 100, 4) if total_rows else 0,
            "positive_prevalence_pct": round(label_counts.get("1", 0) / total_rows * 100, 4) if total_rows else 0,
            "imbalance_ratio": f"1:{round(label_counts.get('0', 0) / label_counts.get('1', 1), 1)}" if label_counts.get('1', 0) else "N/A",
            "other_values": {k: v for k, v in label_counts.items() if k not in ["0", "1"]}
        },
        "categoricals": {
            "from_banks_count": len(unique_from_banks),
            "to_banks_count": len(unique_to_banks),
            "bank_overlap_count": len(unique_from_banks.intersection(unique_to_banks)),
            "receiving_currencies": sorted(list(unique_rec_currencies)),
            "payment_currencies": sorted(list(unique_pay_currencies)),
            "payment_formats": sorted(list(unique_pay_formats)),
            "encoder_compatibility": {
                "unseen_receiving_currencies": list(unseen_rec_curr),
                "unseen_payment_currencies": list(unseen_pay_curr),
                "unseen_payment_formats": list(unseen_pay_fmt),
                "all_currencies_matched": (len(unseen_rec_curr) == 0 and len(unseen_pay_curr) == 0),
                "all_formats_matched": (len(unseen_pay_fmt) == 0)
            }
        },
        "numericals": {
            "amount_received": {
                "min": amt_rec_stats["min"],
                "max": amt_rec_stats["max"],
                "mean": round(rec_mean, 2),
                "std": round(rec_std, 2),
                "zeros": amt_rec_stats["zeros"],
                "negatives": amt_rec_stats["negatives"]
            },
            "amount_paid": {
                "min": amt_paid_stats["min"],
                "max": amt_paid_stats["max"],
                "mean": round(paid_mean, 2),
                "std": round(paid_std, 2),
                "zeros": amt_paid_stats["zeros"],
                "negatives": amt_paid_stats["negatives"]
            },
            "currency_match_count": currency_matches,
            "currency_mismatch_count": currency_mismatches,
            "currency_match_pct": round(currency_matches / total_rows * 100, 2) if total_rows else 0
        }
    }

    # Format Splits
    results["splits"] = {
        "definitions": {
            "train": "Timestamp < 2022/09/08 00:00",
            "val": "2022/09/08 00:00 <= Timestamp < 2022/09/09 18:00",
            "test": "Timestamp >= 2022/09/09 18:00"
        },
        "partitions": {
            "train": {
                "rows": splits["train"]["rows"],
                "pct": round(splits["train"]["rows"] / total_rows * 100, 2),
                "pos": splits["train"]["pos"],
                "neg": splits["train"]["neg"],
                "prevalence_pct": round(splits["train"]["pos"] / splits["train"]["rows"] * 100, 4) if splits["train"]["rows"] else 0,
                "min_ts": splits["train"]["min_ts"],
                "max_ts": splits["train"]["max_ts"],
                "unique_accounts": len(splits["train"]["accounts"]),
                "laundering_accounts": len(splits["train"]["laundering_accounts"])
            },
            "val": {
                "rows": splits["val"]["rows"],
                "pct": round(splits["val"]["rows"] / total_rows * 100, 2),
                "pos": splits["val"]["pos"],
                "neg": splits["val"]["neg"],
                "prevalence_pct": round(splits["val"]["pos"] / splits["val"]["rows"] * 100, 4) if splits["val"]["rows"] else 0,
                "min_ts": splits["val"]["min_ts"],
                "max_ts": splits["val"]["max_ts"],
                "unique_accounts": len(splits["val"]["accounts"]),
                "laundering_accounts": len(splits["val"]["laundering_accounts"])
            },
            "test": {
                "rows": splits["test"]["rows"],
                "pct": round(splits["test"]["rows"] / total_rows * 100, 2),
                "pos": splits["test"]["pos"],
                "neg": splits["test"]["neg"],
                "prevalence_pct": round(splits["test"]["pos"] / splits["test"]["rows"] * 100, 4) if splits["test"]["rows"] else 0,
                "min_ts": splits["test"]["min_ts"],
                "max_ts": splits["test"]["max_ts"],
                "unique_accounts": len(splits["test"]["accounts"]),
                "laundering_accounts": len(splits["test"]["laundering_accounts"])
            }
        },
        "verification": {
            "sum_rows_matches_total": (splits["train"]["rows"] + splits["val"]["rows"] + splits["test"]["rows"] == total_rows),
            "sum_pos_matches_total": (splits["train"]["pos"] + splits["val"]["pos"] + splits["test"]["pos"] == label_counts.get("1", 0)),
            "test_positive_adequate": (splits["test"]["pos"] >= 500)
        }
    }

    # Entity Overlap
    results["entity_overlap"] = {
        "total_unique_accounts": len(all_unique_accounts),
        "train_only_accounts": train_only_accounts,
        "val_only_accounts": val_only_accounts,
        "test_only_accounts": test_only_accounts,
        "train_val_overlap": train_val_overlap,
        "train_test_overlap": train_test_overlap,
        "val_test_overlap": val_test_overlap,
        "all_three_overlap": all_three_overlap,
        "laundering_entities": {
            "total_laundering_accounts": len(all_launderers),
            "test_launderers_total": len(test_launderers),
            "test_launderers_seen_in_train": test_launderers_seen_in_train,
            "test_launderers_seen_in_val": test_launderers_seen_in_val,
            "test_launderers_unseen": test_launderers_unseen
        }
    }

    elapsed = time.time() - start_time
    results["audit_metadata"] = {
        "elapsed_seconds": round(elapsed, 2),
        "audit_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    print(f"\nAudit completed in {elapsed:.2f}s. Saving results to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    print("Done! Pre-flight audit results successfully generated.")

if __name__ == "__main__":
    run_preflight()
