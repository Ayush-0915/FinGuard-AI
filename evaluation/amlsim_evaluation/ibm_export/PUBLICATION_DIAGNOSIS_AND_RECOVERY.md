# FinGuard AI — IBM AML Benchmark Publication Diagnosis and Safe Recovery Plan

**Author:** FinGuard AI Engineering Team  
**Date:** October 20, 2026  
**Status:** Ready for User Review (Zero Live Cloud Writes Performed)  
**Target Migration Script:** `backend/migrations/003_fix_anomaly_score_constraint.sql`

---

## 1. Executive Summary & Root Cause Analysis

During Phase D Gate 2 (Live Supabase Publication), the publication process successfully created the benchmark run record and published all 1,000 benchmark transactions. However, ingestion halted at batch 1 of `ibm_benchmark_scores` with PostgreSQL error `23514` (Check Constraint Violation):

```text
PostgreSQL Error 23514: new row for relation "ibm_benchmark_scores" violates check constraint "ibm_benchmark_scores_anomaly_score_check"
Failing Transaction: IBM_TX_0208384
Failing anomaly_score: -0.0254
```

### Current Live Supabase State Verified:
- `accounts`: **102 rows** (Showcase baseline — Unchanged)
- `transactions`: **500 rows** (Showcase baseline — Unchanged)
- `alerts`: **25 rows** (Showcase baseline — Unchanged)
- `investigations`: **12 rows** (Showcase baseline — Unchanged)
- `ibm_dataset_runs`: **1 row** (`RUN-IBM-HI-SMALL-20261020-01`)
- `ibm_benchmark_transactions`: **1,000 rows** (100% Published)
- `ibm_benchmark_scores`: **0 rows** (Halted at batch 1)
- `ibm_benchmark_evidence`: **0 rows** (Not attempted)

---

## 2. Mathematical Semantics & Domain of Isolation Forest Anomaly Scores

### A. Theoretical Foundation
The production Isolation Forest model (`models/muleguard_isolation_forest.pkl`) was trained via `scikit-learn` using standard path-length anomaly scoring. In scikit-learn, the decision function is defined as:

$$\text{decision\_function}(x) = 2^{-\frac{E(h(x))}{c(n)}} - \text{offset\_}$$

where $c(n)$ is the average path length of unsuccessful searches in a Binary Search Tree, and the standard offset is $\text{offset\_} = -0.5$.

In `evaluation/amlsim_evaluation/ibm_export/scoring.py` (lines 71–77), the anomaly score is computed as:

$$\text{anomaly\_score} = -\text{decision\_function}(x)$$

- **Inliers / Normal Transactions:** When instances require deep trees to isolate ($E(h(x)) \gg c(n)$), the path-length term approaches $0$. The decision function is positive ($\approx +0.5$), which means $\text{anomaly\_score} = -\text{decision\_function}(x)$ is **strictly negative** (approaching $-0.5$).
- **Outliers / Anomalous Transactions:** When instances are easily isolated with few splits ($E(h(x)) \ll c(n)$), the path-length term approaches $1$. The decision function is negative ($\approx -0.5$), which means $\text{anomaly\_score}$ is **strictly positive** (approaching $+0.5$).

Therefore, the mathematically correct, unscaled domain of Isolation Forest anomaly scores is:

$$\text{anomaly\_score} \in [-0.5, +0.5] \subset [-1.0, +1.0]$$

### B. Benchmark Cohort Distribution (1,000 Records)
Analysis of the 1,000 exported benchmark records in `ibm_benchmark_scores.json`:
- **Minimum Anomaly Score:** `-0.1633`
- **Maximum Anomaly Score:** `+0.2159`
- **Mean Anomaly Score:** `-0.0272`
- **Median Anomaly Score:** `-0.0336`
- **Records with `anomaly_score < 0`:** **725 out of 1,000 (72.5%)**

The failing transaction, `IBM_TX_0208384`, has `anomaly_score = -0.0254`. This transaction is an expected inlier. The initial DDL check constraint in `002_ibm_benchmark.sql` inadvertently enforced:

```sql
CHECK (anomaly_score IS NULL OR (anomaly_score BETWEEN 0.0 AND 1.0))
```

This rejected all negative anomaly scores, blocking 72.5% of the benchmark cohort.

---

## 3. Why Clamping or Discarding is Unsound

1. **Clamping to Zero Distorts Distribution:**  
   Clamping negative anomaly scores to `0.0` would create an artificial delta spike at 0 for 725 transactions, erasing continuous distance metrics and degrading down-stream multi-signal risk fusion.
2. **Discarding Records Breaks Benchmark Integrity:**  
   Discarding negative records would eliminate 725 transactions from the 1,000-record benchmark, violating the 1:1:1 relational foreign key parity across transactions, scores, and evidence dossiers.
3. **Preserving Model Invariance:**  
   Production model artifacts (`models/muleguard_lightgbm.pkl` and `models/muleguard_isolation_forest.pkl`) must remain strictly invariant. Modifying the model or post-processing pipeline would compromise experimental validity and reproducibility.

**The smallest, mathematically sound fix is updating the database check constraint to allow values in `[-1.0, 1.0]`.**

---

## 4. Safe Publisher Resumption Architecture

[`evaluation/amlsim_evaluation/ibm_export/publisher.py`](file:///c:/Users/ayush/Desktop/Private/MuleGuard/evaluation/amlsim_evaluation/ibm_export/publisher.py) has been upgraded with intelligent state-detection and resumption capabilities:

1. **Run Check:**  
   Queries `ibm_dataset_runs` for `run_id = RUN-IBM-HI-SMALL-20261020-01`. Since it already exists, the publisher skips re-insertion.
2. **Transaction Check:**  
   Queries `ibm_benchmark_transactions` count. Since all 1,000 transactions are already present, the publisher logs:  
   `"ibm_benchmark_transactions: Already fully published (1000/1000 rows). Skipping re-upload."`  
   Zero duplicate writes or redundant API calls are made.
3. **Deterministic Upsert on Child Tables:**  
   For `ibm_benchmark_scores` and `ibm_benchmark_evidence`, records are upserted using composite keys:
   - Scores: `.upsert(batch, on_conflict="run_id,transaction_id")`
   - Evidence: `.upsert(batch, on_conflict="run_id,transaction_id")`
   This leverages the database unique constraints `uq_ibm_scores_run_tx` and `uq_ibm_evidence_run_tx`, preventing duplicate primary key generation or constraint conflicts.

---

## 5. SQL Migration Script (Ready for Supabase SQL Editor)

File: [`backend/migrations/003_fix_anomaly_score_constraint.sql`](file:///c:/Users/ayush/Desktop/Private/MuleGuard/backend/migrations/003_fix_anomaly_score_constraint.sql)

```sql
-- ==============================================================================
-- FinGuard AI — Migration 003: Fix Anomaly Score Constraint
-- ==============================================================================
-- Drops the overly restrictive [0.0, 1.0] constraint on anomaly_score and 
-- expands it to [-1.0, 1.0], matching the true mathematical domain of 
-- Isolation Forest (-decision_function).
-- ==============================================================================

ALTER TABLE ibm_benchmark_scores 
    DROP CONSTRAINT IF EXISTS chk_ibm_anomaly_score,
    DROP CONSTRAINT IF EXISTS ibm_benchmark_scores_anomaly_score_check;

ALTER TABLE ibm_benchmark_scores 
    ADD CONSTRAINT chk_ibm_anomaly_score 
    CHECK (anomaly_score IS NULL OR (anomaly_score BETWEEN -1.0 AND 1.0));
```

---

## 6. Verification and Regression Testing

All local regression suites have been executed and verified:
- **Unified Test Runner:** `evaluation/amlsim_evaluation/phase4/run_all_tests.py`
- **Result:** **61/61 Tests Passed (100%)**
- **Dry-Run Publisher:** `.venv\Scripts\python.exe evaluation/amlsim_evaluation/ibm_export/publisher.py` (Exit Code 0)
- **Model Invariance:**
  - `muleguard_lightgbm.pkl`: SHA-256 `02c5f122...` (Invariant)
  - `category_encoders.pkl`: SHA-256 `ff5d855f...` (Invariant)
- **Label Quarantine:** Verified offline (`evaluation_ground_truth.json` strictly excluded from all payloads).

---

## 7. Execution Instructions for User

Because cloud safety protocols forbid executing unapproved DDL directly against live Supabase:

1. **Step 1:** Open your **Supabase Dashboard** -> **SQL Editor**.
2. **Step 2:** Paste and execute the SQL from [`backend/migrations/003_fix_anomaly_score_constraint.sql`](file:///c:/Users/ayush/Desktop/Private/MuleGuard/backend/migrations/003_fix_anomaly_score_constraint.sql).
3. **Step 3:** Reply with **"Proceed with publication resume"**.
4. The agent will then execute the resumed publication via `publisher.py --live`, verifying that:
   - `ibm_dataset_runs` remains 1
   - `ibm_benchmark_transactions` remains 1,000 (re-upload skipped)
   - `ibm_benchmark_scores` reaches 1,000
   - `ibm_benchmark_evidence` reaches 1,000
   - Baseline showcase tables remain untouched (102, 500, 25, 12).
