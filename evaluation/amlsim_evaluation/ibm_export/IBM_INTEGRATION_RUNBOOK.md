# FinGuard AI — IBM AML Safe Hybrid Integration Runbook

**Document:** Operational Runbook & Command Reference  
**Path:** `evaluation/amlsim_evaluation/ibm_export/IBM_INTEGRATION_RUNBOOK.md`  
**Pipeline Version:** 1.0.0-hybrid  
**Model Version:** LightGBM-4.5.0-muleguard (Frozen)  

---

## 1. Overview & Architecture

The FinGuard AI IBM AML Hybrid Pipeline processes the full 5,078,345-transaction dataset locally using bounded-memory streaming, executes point-in-time feature engineering and frozen LightGBM inference, and selects a deterministic pilot cap of **1,000 benchmark records** for isolated cloud publication and desktop review.

```
+-----------------------------------------------------------------------------------+
|                        LOCAL FULL-DATASET PROCESSING ENGINE                       |
|                                                                                   |
|  [data/aml_dataset/HI-Small_Trans.csv] (5,078,345 rows / 475 MB)                  |
|                           |                                                       |
|                           v                                                       |
|  [DatasetReader]  --> Streams in 100,000-row chunks; isolates 'Is Laundering'     |
|                           |                                                       |
|                           v                                                       |
|  [FeatureAdapter] --> 26 Point-in-Time features via running state ledger          |
|                           |                                                       |
|                           v                                                       |
|  [ScoringEngine]  --> Frozen LightGBM probability inference (Zero Retraining)     |
|                           |                                                       |
|                           v                                                       |
|  [RecordSelector] --> Deterministic Bounded Selection (Capped at 1,000 records)   |
|                           |                                                       |
|                           v                                                       |
|  [ExportBuilder]  --> 4 Isolated Payloads + Separate Offline Evaluation Labels    |
+-----------------------------------+-----------------------------------------------+
                                    |
            Dry-Run / Local Fixtures| (Zero Cloud Writes in Dry-Run)
                                    v
+-----------------------------------------------------------------------------------+
|               OUTPUT ARTIFACTS (evaluation/.../ibm_export/artifacts/)             |
|                                                                                   |
|  - ibm_dataset_runs.json           - ibm_benchmark_evidence.json                  |
|  - ibm_benchmark_transactions.json - evaluation_ground_truth.json (Isolated)      |
|  - ibm_benchmark_scores.json       - export_manifest.json (Hashes & Provenance)   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Command Reference

### Command 1: Run Local Pipeline in Dry-Run Mode (Full Dataset)
Processes all 5,078,345 records, scores transactions with frozen LightGBM, selects top 1,000 records, and saves verified JSON payloads. Executes **ZERO** database writes.

```powershell
.\.venv\Scripts\python.exe evaluation/amlsim_evaluation/ibm_export/run_pipeline.py --dry-run
```

To run a fast validation check on the first 100,000 records:
```powershell
.\.venv\Scripts\python.exe evaluation/amlsim_evaluation/ibm_export/run_pipeline.py --dry-run --max-rows 100000
```

---

### Command 2: Inspect the Export Manifest & Artifact Sizes
Inspects cryptographic hashes, scanned row counts, selection parameters, and label isolation verification:

```powershell
.\.venv\Scripts\python.exe -c "
import json
with open('evaluation/amlsim_evaluation/ibm_export/artifacts/export_manifest.json', 'r') as f:
    m = json.load(f)
print('Run ID:             ', m['run_id'])
print('Scanned Rows:       ', m['dataset_ingestion_statistics']['total_rows_scanned'])
print('Selected Records:   ', m['selection_summary']['selected_records_count'])
print('Model SHA-256 Match:', m['provenance_hashes']['lightgbm_model']['verified_match'])
print('Dataset SHA-256:    ', m['provenance_hashes']['dataset_csv']['sha256'])
print('Artifacts Saved:    ', list(m['output_artifacts'].keys()))
"
```

---

### Command 3: Run Unified Regression & Integration Tests
Runs the complete test suite (51 test cases) across Phase 2, Phase 3, Phase 4, and IBM Export:

```powershell
.\.venv\Scripts\python.exe evaluation/amlsim_evaluation/phase4/run_all_tests.py
```

To run only the isolated IBM Export tests:
```powershell
.\.venv\Scripts\python.exe evaluation/amlsim_evaluation/ibm_export/tests/test_ibm_export.py
```

---

### Command 4: Review Proposed SQL Schema Migration
Before any database migration is applied, review the isolated schema DDL:

```powershell
Get-Content backend/migrations/002_ibm_benchmark.sql
```

*Safety Rule:* Migration MUST be manually reviewed and approved before execution.

---

### Command 5: Apply Reviewed Schema Migration (Only When Authorized)
Applies the migration using Supabase CLI or PostgreSQL connection:

```powershell
# Method A: Via Supabase SQL Editor
# Copy backend/migrations/002_ibm_benchmark.sql into Supabase Dashboard -> SQL Editor -> Run

# Method B: Via CLI (if supabase CLI is configured)
# supabase db push
```

---

### Command 6: Import a Tiny Pilot Batch (10 Records for Verification)
Validates cloud write permissions and constraints with a tiny 10-record pilot before expanding:

```powershell
# Future implementation upon approval:
# .\.venv\Scripts\python.exe evaluation/amlsim_evaluation/ibm_export/publish_supabase.py --pilot-limit 10
```

---

### Command 7: Verify Database Results in Supabase
Verifies that benchmark tables are populated and that legacy tables are untouched:

```powershell
.\.venv\Scripts\python.exe -c "
from backend.database import client
for t in ['accounts', 'transactions', 'alerts', 'ibm_dataset_runs', 'ibm_benchmark_transactions', 'ibm_benchmark_scores', 'ibm_benchmark_evidence']:
    try:
        res = client.table(t).select('*', count='exact').limit(1).execute()
        print(f'{t:30s}: {res.count} rows')
    except Exception as e:
        print(f'{t:30s}: (Table not yet created or inaccessible)')
"
```

---

### Command 8: Start Backend & Desktop Application
Launches the FastAPI backend and PySide6 desktop interface:

```powershell
# Terminal 1: Backend
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Desktop GUI
.\.venv\Scripts\python.exe frontend/app.py
```

---

### Command 9: Instantaneous Rollback
If the IBM benchmark data or schema ever needs to be removed without affecting legacy showcase data:

```sql
-- Execute in Supabase SQL Editor:
DROP TABLE IF EXISTS ibm_benchmark_evidence CASCADE;
DROP TABLE IF EXISTS ibm_benchmark_scores CASCADE;
DROP TABLE IF EXISTS ibm_benchmark_transactions CASCADE;
DROP TABLE IF EXISTS ibm_dataset_runs CASCADE;
```
*Guaranteed Safety:* Legacy tables (`accounts`, `transactions`, `alerts`, `risk_predictions`, `investigations`) are completely independent and will remain 100% intact.

---

## 3. Environment Variable Specification

FinGuard AI requires the following environment variables (defined in `.env`):

| Variable Name | Required | Default / Example | Purpose |
| :--- | :---: | :--- | :--- |
| `SUPABASE_URL` | Yes | `https://your-project.supabase.co` | Supabase project endpoint |
| `SUPABASE_KEY` | Yes | *(Confidential)* | Server-side API key |
| `FINGUARD_PORT` | No | `8000` | Port for FastAPI backend service |
| `FINGUARD_REPORTS_DIR` | No | `reports/` | Local directory for PDF generation |

> [!WARNING]
> Never commit `.env` or log the value of `SUPABASE_KEY`. Always use `.env.example` for repository templates.
