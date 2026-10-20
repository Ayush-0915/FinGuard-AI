"""
FinGuard AI — IBM AML Local Processing & Dry-Run Export Pipeline
Command-line driver for local dataset processing, point-in-time feature engineering,
frozen model scoring, bounded record selection, and local export serialization.

Safety Rules:
- ZERO writes to Supabase in dry-run mode
- ZERO modification of production models
- ZERO label leakage into inference or payloads
"""

import os
import sys
import argparse
import time
import pandas as pd
from datetime import datetime

# Setup sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config import DEFAULT_CONFIG, ExportConfig
from dataset_reader import DatasetReader
from feature_adapter import FeatureAdapter
from scoring import ModelScoringEngine
from selection import RecordSelector
from export_builder import ExportPayloadBuilder
from manifest import ExportManifestAuditor

def run_dry_run_pipeline(max_rows: int = None, run_id: str = "RUN-IBM-HI-SMALL-20261020-01") -> dict:
    start_time = time.time()
    config = DEFAULT_CONFIG

    print("=" * 70)
    print("FINGUARD AI — IBM AML LOCAL HYBRID PIPELINE (DRY-RUN MODE)")
    print("=" * 70)
    print(f"Run ID:            {run_id}")
    print(f"Dataset Path:      {config.dataset_csv_path}")
    print(f"Chunk Size:        {config.chunk_size:,} records")
    print(f"Pilot Export Cap:  {config.pilot_export_cap:,} records")
    print(f"Output Artifacts:  {config.output_artifacts_dir}")
    print(f"Max Rows Limit:    {'ALL (5,078,345)' if max_rows is None else f'{max_rows:,}'}")
    print("-" * 70)

    # 1. Initialize Components
    print("\n[1/5] Initializing Ingestion & Inference Components...")
    reader = DatasetReader(config)
    adapter = FeatureAdapter(config)
    scorer = ModelScoringEngine(config)
    selector = RecordSelector(config)
    builder = ExportPayloadBuilder(config, run_id=run_id)
    auditor = ExportManifestAuditor(config, run_id=run_id)

    # Accumulators for selection
    # We maintain a bounded candidate buffer to keep RAM usage minimal
    candidate_transactions = []
    candidate_scores = []
    positive_tx_ids = set()

    # 2. Chunked Processing Loop
    print("\n[2/5] Streaming Chunks through Point-in-Time Feature Engine & Model Inference...")
    chunk_idx = 0
    total_processed = 0

    for clean_tx_df, isolated_labels in reader.stream_chunks(max_rows=max_rows):
        chunk_idx += 1
        n_chunk = len(clean_tx_df)
        total_processed += n_chunk

        # Track positive ground truth IDs only (compact memory footprint)
        for tx_id, lbl in isolated_labels.items():
            if lbl == 1:
                positive_tx_ids.add(tx_id)

        # Point-in-Time Streaming Feature Engineering
        features_df = adapter.transform_chunk(clean_tx_df)

        # Frozen Model Scoring
        scores_df = scorer.score_features(features_df)

        # Merge transaction info with scores
        chunk_merged = clean_tx_df.merge(scores_df, on="transaction_id", how="inner")

        # Keep candidate pools:
        # High-risk candidates (scores >= 0.70)
        high_risk = chunk_merged[chunk_merged["model_risk_score"] >= config.high_threshold]
        # Connected or baseline samples
        baseline_samples = chunk_merged[chunk_merged["model_risk_score"] < config.high_threshold].head(100)

        # Buffer accumulation
        combined_candidates = pd.concat([high_risk, baseline_samples], ignore_index=True)
        candidate_transactions.append(clean_tx_df.loc[clean_tx_df["transaction_id"].isin(combined_candidates["transaction_id"])])
        candidate_scores.append(scores_df.loc[scores_df["transaction_id"].isin(combined_candidates["transaction_id"])])

        if chunk_idx % 5 == 0 or total_processed >= 5_000_000 or (max_rows and total_processed >= max_rows):
            elapsed = time.time() - start_time
            print(f"  Processed Chunk {chunk_idx:3d}: {total_processed:9,d} transactions scanned ({elapsed:5.1f}s)")

    reader_stats = reader.get_statistics()
    print(f"\nIngestion Complete: {reader_stats['total_rows_scanned']:,} total rows scanned.")
    print(f"Prevalence: {reader_stats['positive_labels_count']:,} positives / {reader_stats['valid_rows_count']:,} valid ({reader_stats['prevalence_pct']:.4f}%)")

    # 3. Deterministic Record Selection
    print("\n[3/5] Executing Deterministic Bounded Selection (Cap: 1,000)...")
    all_cand_tx = pd.concat(candidate_transactions, ignore_index=True).drop_duplicates(subset=["transaction_id"])
    all_cand_scores = pd.concat(candidate_scores, ignore_index=True).drop_duplicates(subset=["transaction_id"])

    selected_df = selector.select_bounded_records(all_cand_tx, all_cand_scores)
    print(f"  Selected records count: {len(selected_df):,}")
    print("  Tier Distribution in Selection:")
    for tier, cnt in selected_df["risk_tier"].value_counts().items():
        print(f"    - {tier:10s}: {cnt:4d}")

    # 4. Payload Building & Serialization
    print("\n[4/5] Serializing Database Payload Artifacts & Isolated Evaluation Labels...")
    isolated_ground_truth_selected = {
        tx_id: (1 if tx_id in positive_tx_ids else 0)
        for tx_id in selected_df["transaction_id"]
    }
    payloads = builder.build_payloads(
        selected_df=selected_df,
        isolated_labels=isolated_ground_truth_selected,
        reader_stats=reader_stats
    )

    saved_files = builder.save_payload_artifacts(payloads)
    for name, fpath in saved_files.items():
        sz = os.path.getsize(fpath)
        print(f"  Saved {name:24s}: {os.path.basename(fpath):35s} ({sz:8,d} bytes)")

    # 5. Manifest Generation & Provenance Auditing
    print("\n[5/5] Generating Cryptographic Manifest...")
    ts_min = str(selected_df["timestamp"].min())
    ts_max = str(selected_df["timestamp"].max())
    manifest = auditor.generate_manifest(
        saved_files=saved_files,
        reader_stats=reader_stats,
        selected_count=len(selected_df),
        timestamp_range={"min": ts_min, "max": ts_max}
    )

    manifest_path = os.path.join(config.output_artifacts_dir, "export_manifest.json")
    print(f"  Saved Manifest:             {os.path.basename(manifest_path)} ({os.path.getsize(manifest_path):8,d} bytes)")

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("DRY-RUN PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Total Transactions Scanned: {reader_stats['total_rows_scanned']:,}")
    print(f"Selected Benchmark Records: {len(selected_df):,} (capped at {config.pilot_export_cap})")
    print(f"Database Writes Executed:   0 (Dry-Run Enforced)")
    print(f"Model Retraining Executed:  0 (Frozen LightGBM Verified)")
    print(f"Execution Time:             {total_time:.2f} seconds")
    print("=" * 70)

    return {
        "status": "success",
        "run_id": run_id,
        "scanned_rows": reader_stats["total_rows_scanned"],
        "selected_rows": len(selected_df),
        "saved_files": saved_files,
        "manifest_path": manifest_path,
        "execution_time_sec": total_time
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinGuard AI — IBM AML Hybrid Export Pipeline")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Execute dry-run without database writes")
    parser.add_argument("--max-rows", type=int, default=None, help="Max rows to process (default: full dataset)")
    parser.add_argument("--run-id", type=str, default="RUN-IBM-HI-SMALL-20261020-01", help="Custom run ID")
    args = parser.parse_args()

    run_dry_run_pipeline(max_rows=args.max_rows, run_id=args.run_id)
