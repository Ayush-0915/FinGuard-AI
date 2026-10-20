# FinGuard AI — Architecture Audit & Hybrid IBM AML Integration Plan (Phase A)

**Document Status:** Official Architecture Audit & Pre-Migration Plan  
**Date:** October 20, 2026  
**Auditors:** Senior ML Engineer, Financial-Crime Analytics Architect, Supabase Specialist, Quality Engineer  
**Workspace Root:** `C:\Users\ayush\Desktop\Private\MuleGuard`  
**Git Remote:** `https://github.com/Ayush-0915/Private-Project.git`  
**Target Dataset:** `data/aml_dataset/HI-Small_Trans.csv` (IBM Transactions for AML)  

---

## 1. Executive Summary & Purpose

FinGuard AI (originally MuleGuard) currently operates a dual-layer fraud detection architecture:
1. **Showcase Synthetic Layer:** A seeded Supabase PostgreSQL database holding 102 accounts, 500 transactions, 50 risk predictions, 25 alerts, and 12 investigations, built for live interactive college demonstrations and dashboard navigation.
2. **Experimental Offline Layer:** An offline evaluation framework under `evaluation/amlsim_evaluation/` analyzing the IBM Transactions for AML benchmark (5,078,345 records) with point-in-time feature engineering, NetworkX graph typologies, grounded explanations, and multi-budget alert prioritization.

### Objective of the Hybrid Architecture
To bridge these layers without compromising either:
- **Local Heavy Computation:** Process all 5,078,345 transactions locally using chunked streaming, point-in-time feature engineering, and frozen model inference.
- **Bounded Cloud Publication:** Publish only a configurable, deterministic, investigator-friendly selection (pilot cap: **1,000 ranked transactions**) to Supabase.
- **Strict Data Isolation:** Guarantee 100% preservation of existing synthetic showcase data, zero schema modifications to legacy tables, zero production model drift, and zero secret leakage.
- **Seamless Application Access:** Expose the selected IBM benchmark transactions and grounded intelligence through clean `/api/v2/ibm/*` endpoints and an optional Benchmark Mode in the PySide6 desktop UI.

---

## 2. Git & Workspace State Audit

### 2.1 Git Branch & Remote Configuration
- **Current Branch:** `main`
- **Head Commit:** `711ab10 Updatwd`
- **Remote Origin:** `https://github.com/Ayush-0915/Private-Project.git`
- **Total Tracked Files:** 47 tracked files in Git tree.

### 2.2 Working Tree Status (`git status --short`)
```text
 M .gitignore
 M backend/main.py
 M backend/seed.py
 M config.json
 M frontend/app.py
?? CURRENT_STATUS.md
?? backend/phase4_router.py
?? evaluation/amlsim_evaluation/
```

### 2.3 Working Tree Diff Analysis
- **`.gitignore`:** Added `data/` to protect local datasets from accidental tracking.
- **`backend/main.py`:** Mounted Phase 4 Intelligence router (`/api/v2/`) with graceful import fallback.
- **`backend/seed.py`:** Updated synthetic showcase seed functions with deterministic seed (seed=42) and verified foreign keys.
- **`config.json`:** Configured standard API base URL (`http://127.0.0.1:8000`).
- **`frontend/app.py`:** Added `AlertPrioritizationView` (Index 10) and `CaseDossiersView` (Index 11), along with resilient `ApiClient` fallback methods.
- **Safety Directive:** All pre-existing working-tree changes will be preserved intact. No hard resets (`git reset --hard`) or destructive commands will be executed.

### 2.4 Ignore & Secrets Configuration
- **`.env.example`:** Verified present. Contains only placeholder environment variable names (`SUPABASE_URL`, `SUPABASE_KEY`, `FINGUARD_PORT`, `FINGUARD_REPORTS_DIR`). No secrets.
- **`.env`:** Verified present in root. Properly ignored by `.gitignore` (line 97). Must remain strictly uncommitted.
- **Dataset Ignore:** `.gitignore` includes `*.csv`, `*.parquet`, and `data/`. The 475 MB IBM CSV will never be staged or committed.

---

## 3. Production Model Artifacts & Cryptographic Hash Baseline

All production models and encoder contracts are located under `models/`. Their SHA-256 hashes were cryptographically verified in read-only mode:

| File Name | Description | Verified SHA-256 Checksum | Invariance Status |
| :--- | :--- | :--- | :---: |
| `models/muleguard_lightgbm.pkl` | Production LightGBM Classifier | `02c5f122e1ee729bd97bb08e8d004dae1b4b919416384c4d5c214598af702fa2` | **FROZEN** |
| `models/muleguard_lightgbm.txt` | LightGBM Text Tree Representation | `2bf774a5d4ca4716759fd5d3303db5926ab05b02770b5f52e596910504c9e121` | **FROZEN** |
| `models/muleguard_isolation_forest.pkl` | Isolation Forest Outlier Detector | `7c0fd7b168f4621de97d9164b0b9c83202921acbaecc028e3ae42bc00517a177` | **FROZEN** |
| `models/category_encoders.pkl` | Categorical Label Encoders | `ff5d855fe24e3fddac6a136be0d8ed048e0b413486c9733b7bd5addcdc65839a` | **FROZEN** |
| `models/feature_columns.json` | 26-Feature Contract Order Specification | `2aff95d9e42d389df853185d89ab0ed7384d4480f4905829a48093bc2ed768e8` | **FROZEN** |
| `models/shap_explainer.pkl` | TreeSHAP Explainer | `4dc175782787884260f89d31139b4cb51b75294a8f9f3c78d05545582c3c9077` | **FROZEN** |

> [!CAUTION]
> **Zero Retraining Mandate:** Production models MUST NOT be retrained, replaced, or modified. The IBM AML integration will execute inference purely using these frozen artifacts.

---

## 4. Live Supabase Database Schema & Isolation Audit

### 4.1 Connection Verification
Live read-only connection to Supabase PostgreSQL was confirmed via `backend/database.py` using Application Default Credentials loaded from local `.env`.

### 4.2 Current Table Inventory & Verified Row Counts
| Table Name | Primary Key | Verified Live Row Count | Role / Purpose |
| :--- | :--- | ---: | :--- |
| `accounts` | `account_id TEXT` | **102** | Synthetic Indian demographic showcase accounts |
| `transactions` | `transaction_id TEXT` | **500** | Synthetic demo financial transactions |
| `alerts` | `alert_id TEXT` | **25** | Seeded high-risk alerts |
| `risk_predictions` | `id BIGINT IDENTITY` | **55** | Historical inference predictions |
| `investigations` | `investigation_id TEXT` | **12** | Active compliance investigation dossiers |

### 4.3 Existing Foreign Key Constraints Analysis
From `backend/seed.py` lines 32–109:
- `transactions.sender_id` $\to$ `REFERENCES accounts(account_id) ON DELETE CASCADE`
- `transactions.receiver_id` $\to$ `REFERENCES accounts(account_id) ON DELETE CASCADE`
- `risk_predictions.account_id` $\to$ `REFERENCES accounts(account_id)`
- `risk_predictions.transaction_id` $\to$ `REFERENCES transactions(transaction_id)`
- `alerts.account_id` $\to$ `REFERENCES accounts(account_id)`
- `investigations.account_id` $\to$ `REFERENCES accounts(account_id)`

### 4.4 Critical Architectural Isolation Finding
1. **Foreign Key Blocker:** If IBM AML records were inserted directly into the existing `transactions` table, every foreign account ID (e.g. `80032DB60`) would cause an immediate Postgres foreign key constraint violation (`violates foreign key constraint "transactions_sender_id_fkey"`) unless dummy account records were inserted into `accounts`.
2. **Showcase Pollution Risk:** Inserting synthetic IBM entities into `accounts` would corrupt Indian regional metrics, pollute showcase account searches, and distort monthly charts.
3. **Architectural Decision:** IBM AML benchmark records **MUST BE ISOLATED** in dedicated benchmark tables (`ibm_benchmark_*`). Legacy tables will remain 100% untouched.

---

## 5. IBM AML Dataset Profile & Feature Contract Compatibility

### 5.1 Dataset File Verification
- **Path:** `data/aml_dataset/HI-Small_Trans.csv`
- **File Size:** `475,664,283` bytes (453.63 MB)
- **SHA-256:** `b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040`
- **Total Rows:** `5,078,345` transactions (plus 1 header row)
- **Columns:** 11 columns
- **Missing Values:** 0 across all columns (100% complete)
- **Exact Duplicates:** 9 rows (0.00018%)
- **Target Imbalance:** 5,177 positives (`Is Laundering = 1`), 5,073,168 negatives (`0`); prevalence = **0.1019%**

### 5.2 Field-to-Feature Mapping Contract

| IBM CSV Column | Raw Dtype | Pipeline Feature | Preprocessing / Mapping |
| :--- | :--- | :--- | :--- |
| `Timestamp` | `object` | `timestamp`, `hour`, `day_of_week` | Parsed to datetime; `dt.hour` (0-23), `dt.dayofweek` (0-6) |
| `From Bank` | `int64` | `from_bank` | Preserved as integer bank identifier |
| `Account` | `object` | `sender_account` | String account identifier (hex format e.g. `8000EBD30`) |
| `To Bank` | `int64` | `to_bank` | Preserved as integer bank identifier |
| `Account.1` | `object` | `receiver_account` | String account identifier (hex format e.g. `8000F5340`) |
| `Amount Received` | `float64` | `amount_received` | Monetary quantity credited |
| `Receiving Currency` | `object` | `receiving_currency` | Categorical encoding via `models/category_encoders.pkl` |
| `Amount Paid` | `float64` | `amount_paid` | Monetary quantity debited |
| `Payment Currency` | `object` | `payment_currency` | Categorical encoding via `models/category_encoders.pkl` |
| `Payment Format` | `object` | `payment_format` | Categorical encoding via `models/category_encoders.pkl` |
| `Is Laundering` | `int64` | *(Excluded)* | **GROUND TRUTH LABEL ONLY: STRICTLY EXCLUDED FROM INFERENCE** |

### 5.3 Point-in-Time Feature Engineering Contract
The 26 expected model features are constructed identically using `evaluation/amlsim_evaluation/feature_engine.py`:
- **Instantaneous (6):** `hour`, `day_of_week`, `amount_diff` ($Received - Paid$), `amount_ratio` ($Received / (Paid + 10^{-6})$), `currency_match` ($Receiving == Payment$), `same_bank` ($From == To$).
- **Sender Rolling State (6):** `sender_transaction_count`, `sender_total_amount`, `sender_avg_amount`, `sender_max_amount`, `sender_unique_receivers`, `sender_unique_banks`.
- **Receiver Rolling State (6):** `receiver_transaction_count`, `receiver_total_amount`, `receiver_avg_amount`, `receiver_max_amount`, `receiver_unique_senders`, `receiver_unique_banks`.
- **Temporal Velocity (1):** `seconds_since_previous` (seconds since sender's previous transaction, default 999,999.0 for new accounts).
- **Categoricals (3):** `receiving_currency`, `payment_currency`, `payment_format` (100% encoder coverage).
- **Bank Identifiers (2):** `from_bank`, `to_bank`.
- **Amount Base (2):** `amount_received`, `amount_paid`.

### 5.4 Leakage Boundary Verification
- Same-minute transactions in timestamp batch $T$ only observe ledger state prior to $T$.
- State ledger is updated only *after* the entire timestamp batch is evaluated.
- Verified in Phase 2 regression test: future history delta = $0.0000000000$.

---

## 6. Data Volume, Performance & Security Risks

### 6.1 Volume & Performance Risks
- **Supabase Quota Exhaustion:** The full dataset is 5,078,345 rows (475 MB). Direct cloud upload would breach the 500 MB free tier storage limit and trigger HTTP gateway timeouts.
- **API Latency Degradation:** Scanning the full CSV in FastAPI request handlers would introduce 5–10 second response times.
- **Memory Consumption:** Loading 5 million rows into a pandas DataFrame in RAM requires ~2.8 GB.

### 6.2 Volume Risk Mitigations
1. **Chunked Local Processing:** Process the dataset in streaming chunks of 100,000 rows. Memory stays $< 400$ MB.
2. **Pilot Export Cap:** Enforce a hard configuration cap of **1,000 selected transactions** for Supabase publication.
3. **Investigator-Centric Selection Policy:**
   - Top 500 Critical & High risk ranked candidate alerts ($P(\text{Mule}) \ge 0.70$).
   - 250 connected counterparty transactions needed to complete graph funnels and layering paths.
   - 250 diverse sample transactions across Medium/Low tiers to validate negative baseline triage.
4. **Pre-computed Database Indexes:** Create B-tree indexes on `run_id`, `risk_rank`, `risk_tier`, `sender_account`, and `receiver_account`. Query latency remains $< 30$ ms.

### 6.3 Security Risks & Mitigations
- **Credential Leakage:** `.env` contains Supabase service keys.
  - *Mitigation:* Zero credential logging. The PySide6 frontend client NEVER receives or stores service keys.
- **Arbitrary File Access:** Backend endpoints must not allow clients to specify arbitrary local file paths.
  - *Mitigation:* Strict Pydantic validators with path traversal prevention; exports are restricted to designated internal directories.
- **Regulatory / Ethical Misrepresentation:**
  - *Mitigation:* Display persistent compliance notices: *"IBM AML benchmark data is used for research and evaluation. Risk scores are investigatory triage signals, not proof of criminal activity. Ground-truth labels are evaluation metadata, not model predictions."*

---

## 7. Proposed Isolated Supabase Schema & Migration Plan

### 7.1 Proposed Schema DDL (`backend/migrations/002_ibm_benchmark.sql`)

```sql
-- ============================================================================
-- FinGuard AI — Isolated IBM AML Benchmark Schema Migration
-- Migration ID: 002_ibm_benchmark
-- Description: Isolated tables for IBM AML benchmark imports and evaluation.
-- Safety: Completely isolated from legacy accounts, transactions, and alerts.
-- ============================================================================

-- 1. Import Run Provenance Table
CREATE TABLE IF NOT EXISTS ibm_dataset_runs (
    run_id TEXT PRIMARY KEY,
    source_dataset TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    total_scanned_rows BIGINT NOT NULL,
    selected_records_count INTEGER NOT NULL,
    model_version TEXT NOT NULL,
    pipeline_version TEXT NOT NULL,
    selection_policy TEXT NOT NULL,
    export_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Selected Benchmark Transactions Table
CREATE TABLE IF NOT EXISTS ibm_benchmark_transactions (
    transaction_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES ibm_dataset_runs(run_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    sender_account TEXT NOT NULL,
    receiver_account TEXT NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    receiving_currency TEXT NOT NULL,
    payment_currency TEXT NOT NULL,
    payment_format TEXT NOT NULL,
    from_bank INTEGER NOT NULL,
    to_bank INTEGER NOT NULL,
    is_evaluation_positive BOOLEAN DEFAULT FALSE, -- Evaluation metadata only
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Model Scoring & Prioritization Table
CREATE TABLE IF NOT EXISTS ibm_benchmark_scores (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES ibm_dataset_runs(run_id) ON DELETE CASCADE,
    transaction_id TEXT NOT NULL REFERENCES ibm_benchmark_transactions(transaction_id) ON DELETE CASCADE,
    model_risk_score DOUBLE PRECISION NOT NULL,
    risk_rank INTEGER NOT NULL,
    risk_tier TEXT NOT NULL, -- 'Critical', 'High', 'Medium', 'Low'
    fused_score DOUBLE PRECISION,
    anomaly_score DOUBLE PRECISION,
    model_version TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Grounded Explainability & Evidence Table
CREATE TABLE IF NOT EXISTS ibm_benchmark_evidence (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES ibm_dataset_runs(run_id) ON DELETE CASCADE,
    transaction_id TEXT NOT NULL REFERENCES ibm_benchmark_transactions(transaction_id) ON DELETE CASCADE,
    human_readable_summary TEXT NOT NULL,
    contributing_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    graph_patterns JSONB NOT NULL DEFAULT '[]'::jsonb,
    provenance_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Performance Indexes
CREATE INDEX IF NOT EXISTS idx_ibm_tx_run_id ON ibm_benchmark_transactions(run_id);
CREATE INDEX IF NOT EXISTS idx_ibm_tx_sender ON ibm_benchmark_transactions(sender_account);
CREATE INDEX IF NOT EXISTS idx_ibm_tx_receiver ON ibm_benchmark_transactions(receiver_account);
CREATE INDEX IF NOT EXISTS idx_ibm_tx_timestamp ON ibm_benchmark_transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_ibm_scores_rank ON ibm_benchmark_scores(run_id, risk_rank);
CREATE INDEX IF NOT EXISTS idx_ibm_scores_tier ON ibm_benchmark_scores(risk_tier);
CREATE INDEX IF NOT EXISTS idx_ibm_evidence_tx ON ibm_benchmark_evidence(transaction_id);
```

### 7.2 Safety & Migration Execution Rules
1. **Zero Drop/Truncate:** The migration uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`.
2. **Review-First Approval:** This SQL migration will NOT be executed until explicitly approved by the user.
3. **Dry-Run Capability:** The import pipeline will run first in local `--dry-run` mode producing verified JSON fixtures before any database write is initiated.

---

## 8. Proposed Backend API Architecture

A dedicated, isolated API router will be added under `backend/ibm_benchmark_router.py` mounted at `/api/v2/ibm`:

```
+-----------------------------------------------------------------------------------+
|                        PROPOSED IBM BENCHMARK API ENDPOINTS                       |
+-----------------------------------------------------------------------------------+
| GET /api/v2/ibm/runs                                                              |
|   -> Returns list of available import runs with hashes, metadata, and counts      |
|                                                                                   |
| GET /api/v2/ibm/runs/{run_id}                                                     |
|   -> Returns full provenance manifest and execution statistics for specific run   |
|                                                                                   |
| GET /api/v2/ibm/transactions?run_id=...&page=1&limit=50&account_id=...           |
|   -> Paginated query over selected benchmark transactions                         |
|                                                                                   |
| GET /api/v2/ibm/alerts?run_id=...&budget=500&tier=Critical                        |
|   -> Returns capacity-prioritized benchmark alerts with scores and ranks          |
|                                                                                   |
| GET /api/v2/ibm/transactions/{transaction_id}/explanation                         |
|   -> Returns grounded multi-source evidence breakdown ([MODEL], [GRAPH], etc.)    |
|                                                                                   |
| GET /api/v2/ibm/summary?run_id=...                                                |
|   -> Returns high-level metrics (scanned rows, selected count, tier distribution) |
+-----------------------------------------------------------------------------------+
```

### API Design Principles
- Strict Pydantic query models (`run_id`, `budget`, `limit`, `offset`, `tier`).
- Hard limits (`limit <= 100`) to prevent large response memory spikes.
- Graceful error handling (`HTTP 404` for missing IDs, `HTTP 400` for invalid parameters).
- Complete preservation of all existing `/api/v2/*` and legacy routes.

---

## 9. Proposed PySide6 Desktop UI Integration

### 9.1 Benchmark Navigation Architecture
The desktop client will feature an explicit **IBM AML Benchmark View** (Index 12) accessible from the sidebar under a new section:

```
+----------------------------------------------------+
|  [Sidebar Navigation]                              |
|   |-- OVERVIEW: Dashboard (0)                      |
|   |-- RISK MONITORING: Active Alerts (1), ...      |
|   |-- INVESTIGATION: Accounts (3), Network (5)...  |
|   |-- ANALYTICS: Fraud Analytics (6)...            |
|   `-- BENCHMARK RESEARCH                           |
|       `-- IBM AML Benchmark (12)                   |
+----------------------------------------------------+
```

### 9.2 UI Features
1. **Dataset / Run Selector:** Dropdown displaying available verified runs (`RUN-IBM-HI-SMALL-20261020-01`).
2. **Triage Metrics Banner:** Scanned volume (5,078,345 rows), Selected Pilot (1,000 transactions), Priority Tiers count.
3. **Prioritized Benchmark Table:** Rank, Tx ID, Timestamp, Counterparties, Amount, Model Probability, Risk Tier badge.
4. **Side-by-Side Explanation Card:** Real-time grounded evidence breakdown with provenance tags (`MODEL`, `BEHAVIORAL`, `GRAPH`, `RULE`).
5. **Persistent Notice Banner:**
   > ⚖️ *IBM AML benchmark data is used for research and evaluation. Risk scores are investigatory triage signals, not proof of criminal activity. Ground-truth labels are evaluation metadata, not model predictions.*

---

## 10. Implementation Plan & File Manifest

### 10.1 New Files to Create

| File Path | Component | Description |
| :--- | :--- | :--- |
| `evaluation/amlsim_evaluation/ibm_export/config.py` | Pipeline Config | Chunk sizes, export limits (cap: 1,000), file paths, run ID generator |
| `evaluation/amlsim_evaluation/ibm_export/dataset_reader.py` | Chunked Ingestion | Bounded chunk reader with schema validation and error tracking |
| `evaluation/amlsim_evaluation/ibm_export/feature_adapter.py` | Feature Engine Adapter | Feeds chunks into point-in-time streaming feature engine |
| `evaluation/amlsim_evaluation/ibm_export/scoring.py` | Model Inference | Evaluates frozen LightGBM risk probability without model retraining |
| `evaluation/amlsim_evaluation/ibm_export/selection.py` | Record Selection | Deterministic Top-K alert ranking and counterparty funnel extraction |
| `evaluation/amlsim_evaluation/ibm_export/export_builder.py` | Export Serialization | Generates verified JSON manifest and database payload fixtures |
| `evaluation/amlsim_evaluation/ibm_export/manifest.py` | Provenance Auditing | Computes SHA-256 hashes, record counts, and run metadata |
| `evaluation/amlsim_evaluation/ibm_export/run_pipeline.py` | CLI Entrypoint | Command-line driver (`--dry-run`, `--export-only`, `--publish`) |
| `evaluation/amlsim_evaluation/ibm_export/tests/test_ibm_export.py` | Unit Test Suite | Comprehensive tests for reader, adapter, selection, and leakage |
| `backend/migrations/002_ibm_benchmark.sql` | SQL Migration | Isolated PostgreSQL table definitions for Supabase |
| `backend/ibm_benchmark_router.py` | FastAPI Router | Read-only `/api/v2/ibm/*` REST endpoints |
| `evaluation/amlsim_evaluation/ibm_export/IBM_INTEGRATION_RUNBOOK.md` | Operations Runbook | Step-by-step commands for pipeline, dry-run, and UI demo |
| `evaluation/amlsim_evaluation/REPOSITORY_CLEANUP_REPORT.md` | Git Cleanup Report | Detailed audit of repository files, large objects, and gitignore |

### 10.2 Existing Files to Modify (Minimally)
- `backend/main.py`: Include `ibm_benchmark_router` conditionally with graceful import.
- `frontend/app.py`: Add `IBMBenchmarkView` (Index 12) and ApiClient benchmark helper methods.
- `.gitignore`: Confirm `data/aml_dataset/` and export caches remain strictly ignored.

---

## 11. Rollback & Safety Strategy

1. **Instantaneous Database Rollback:**
   ```sql
   DROP TABLE IF EXISTS ibm_benchmark_evidence CASCADE;
   DROP TABLE IF EXISTS ibm_benchmark_scores CASCADE;
   DROP TABLE IF EXISTS ibm_benchmark_transactions CASCADE;
   DROP TABLE IF EXISTS ibm_dataset_runs CASCADE;
   ```
   Executing this single SQL block completely removes all benchmark tables without affecting legacy tables in any way.
2. **Zero Legacy Risk:**
   - Legacy tables (`accounts`, `transactions`, `alerts`, `risk_predictions`, `investigations`) are never referenced by foreign keys from new tables.
   - Legacy routes continue operating seamlessly.
3. **Production Model Safety:**
   - Pre- and post-execution SHA-256 hash assertions are integrated into all test scripts. Any hash deviation will immediately fail the suite.

---

## 12. Verification & Next Steps

At this milestone (completion of Phase A):
- The repository, database, dataset, and ML contracts have been completely audited in read-only mode.
- All findings, risks, proposed schemas, and file changes are documented.
- **NO files have been modified, NO database mutations have occurred, and NO schema changes have been executed.**

### Requested Review & Confirmation:
Please review this architecture plan. Upon your approval, we will proceed to:
- **Phase B:** Implement the isolated local processing pipeline (`evaluation/amlsim_evaluation/ibm_export/`) and run local tests in `--dry-run` mode.
- **Phase C:** Generate and validate the bounded 1,000-record export artifact and provenance manifest locally.
- **Phase D/E/F:** Present the export results for approval before applying the database migration or making any cloud writes.
