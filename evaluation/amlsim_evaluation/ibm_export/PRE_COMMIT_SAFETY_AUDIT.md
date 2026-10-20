# FinGuard AI — Pre-Commit Safety & Staging Audit

**Project:** FinGuard AI — AI-Powered Financial Crime Detection and Risk Intelligence  
**Repository Root:** `C:\Users\ayush\Desktop\Private\MuleGuard`  
**Expected Remote:** `https://github.com/Ayush-0915/Private-Project.git`  
**Audit Date:** October 20, 2026  
**Auditor:** FinGuard AI Quality & Architecture Engineering  
**Mode:** READ-ONLY AUDIT (Zero repository modifications, zero deletions, zero commits, zero pushes)

---

## 1. Current Repository & Working Tree State

### A. Git Diagnostic Metadata
- **Current Branch:** `main`
- **HEAD Commit Hash:** `711ab102c16de403c6836b54a3574851e96370a3`
- **HEAD Commit Message:** `711ab10 Updatwd` (Author: Ayush Singh, Mon Oct 19 20:07:37 2026 +0530)
- **Configured Remote (`origin`):**
  - Fetch: `https://github.com/Ayush-0915/Private-Project.git`
  - Push: `https://github.com/Ayush-0915/Private-Project.git`
- **Synchronization:** Up to date with `origin/main` (0 ahead, 0 behind)

### B. Index & Working Tree Breakdown (`git status --short --branch`)
```text
## main...origin/main
 M .gitignore
 M backend/main.py
 M backend/seed.py
 M config.json
D  dist/app_split.z01
D  dist/app_split.z02
D  dist/app_split.zip
D  dist/main_split.z01
D  dist/main_split.z02
D  dist/main_split.zip
 M frontend/app.py
D  reports/Investigation_Report_ACC-10293.pdf
D  reports/test_report.pdf
?? CURRENT_STATUS.md
?? backend/ibm_benchmark_router.py
?? backend/migrations/
?? backend/phase4_router.py
?? evaluation/amlsim_evaluation/
```

- **Staged Index Removals (8 files, 258.47 MB bloat):**
  `dist/app_split.*` (3 files), `dist/main_split.*` (3 files), `reports/*.pdf` (2 files).
  *Local disk copies remain intact on disk.*
- **Unstaged Modified Tracked Files (5 files):**
  `.gitignore`, `backend/main.py`, `backend/seed.py`, `config.json`, `frontend/app.py`.
  *All existing user modifications preserved.*
- **Untracked Additions (79 files across 5 directories):**
  `CURRENT_STATUS.md`, `backend/ibm_benchmark_router.py`, `backend/migrations/` (2 files), `backend/phase4_router.py`, `evaluation/amlsim_evaluation/` (74 files).

---

## 2. Review of `.gitignore` and Rule Provenance

### A. Comparison with `HEAD:.gitignore`
The committed version of `.gitignore` at `HEAD` (`711ab10`) ended with:
```text
# OS files
.DS_Store
Thumbs.db
```

The current working tree diff against `HEAD` reveals:
```diff
diff --git a/.gitignore b/.gitignore
index 6b20461..97d7cd1 100644
--- a/.gitignore
+++ b/.gitignore
@@ -107,3 +107,11 @@ pip-selfcheck.json
 # OS files
 .DS_Store
 Thumbs.db
+
+# Dataset directory
+data/
+
+# Evaluation intermediate arrays and offline ground-truth quarantine
+*.npy
+evaluation/amlsim_evaluation/ibm_export/artifacts/evaluation_ground_truth.json
+reports/*.pdf
```

### B. Rule Provenance:
1. **`data/` Rule:** Originated as an uncommitted local working tree modification during Phase 1/Phase 2 dataset ingestion. It shields the ~40.5 GB IBM AML dataset in `data/aml_dataset/` (which contains individual CSV files up to 17 GB) from being tracked.
2. **`*.npy` Rule:** Added in our previous turn. Ignores 6 intermediate evaluation prediction arrays (~21.82 MB).
3. **`evaluation_ground_truth.json` Rule:** Added in our previous turn. Quarantines the 17.7 KB benchmark ground-truth labels.
4. **`reports/*.pdf` Rule:** Added in our previous turn. Ignores generated demonstration PDF reports.

### C. False Positive / Accidental Ignore Audit
Audited all 107 files across `backend/`, `frontend/`, `models/`, and `evaluation/`.
- **Total Ignored Files:** Exactly 7 files:
  - 6 `.npy` files (`evaluation/amlsim_evaluation/audit/*.npy`)
  - 1 `evaluation_ground_truth.json`
- **Result:** **0 false positives.** Zero required Python scripts, zero SQL migrations, zero unit tests, zero model artifacts, and zero benchmark fixtures are ignored.

---

## 3. Audit of Prospective Additions by Severity

### Severity Breakdown:

| Finding Category | Severity | Item Count | Status | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Exposed Secrets & Credentials** | **CRITICAL** | **0** | **PASSED** | Regex scan for JWT tokens, API keys, service roles, and private keys found 0 hardcoded secrets. `.env` is uncommitted and ignored. |
| **Files Exceeding 10 MB** | **HIGH** | **0** | **PASSED** | All 79 untracked files are well under 10 MB. |
| **Offline Ground Truth Quarantine** | **HIGH** | **0** | **PASSED** | `evaluation_ground_truth.json` is strictly ignored by `.gitignore`. |
| **Laundering Label Keyword Mentions** | **MEDIUM** | **13 files** | **VALIDATED** | The string `is_laundering` appears only in sanitation functions (`_sanitize_record`), test assertions (`self.assertNotIn`), dataset extraction logic, and audit reports. No data payloads contain labels. |
| **Benchmark Fixtures (Operational)** | **INFORMATIONAL** | **5 files** | **VERIFIED** | 1.72 MB total. Contain zero labels and zero secrets. Necessary for offline fallback. |

---

## 4. Deep Inspection of Proposed Benchmark Fixtures

Location: `evaluation/amlsim_evaluation/ibm_export/artifacts/`

| Fixture File | File Size | Record Count | Target Labels Found? | Credentials Found? | Demo Necessity & Reproducibility |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `export_manifest.json` | 3.6 KB | 1 record | **0 (None)** | **0 (None)** | Cryptographic SHA-256 provenance manifest. Highly essential. |
| `ibm_dataset_runs.json` | 0.9 KB | 1 run | **0 (None)** | **0 (None)** | Fallback run metadata for offline execution. |
| `ibm_benchmark_transactions.json` | 380.1 KB (0.37 MB) | 1,000 txs | **0 (None)** | **0 (None)** | Required for offline pagination fallback when Supabase is disconnected. |
| `ibm_benchmark_scores.json` | 280.1 KB (0.27 MB) | 1,000 scores | **0 (None)** | **0 (None)** | Required for prioritized alert triage demo fallback. |
| `ibm_benchmark_evidence.json` | 1,100.6 KB (1.07 MB) | 1,000 dossiers | **0 (None)** | **0 (None)** | Required for grounded explanation dialog demo fallback. |

**Summary:** The 5 benchmark fixtures total **1.72 MB**, contain **0 ground-truth labels**, **0 credentials**, and are **100% deterministically reproducible** from the original dataset via `run_pipeline.py`.

---

## 5. GitHub History Implications for Excluded Binaries

### A. Historical Presence
- Git history query (`git log --oneline -- "dist/*"`) shows the split binaries were introduced in commit `a1b9446 Initial commit`.
- There are only two commits in the entire repository history (`a1b9446` and `711ab10`).

### B. Effect of `git rm --cached`
- **Future Commits:** The staged deletion removes the 258.47 MB binaries from the Git tree of all future commits. Future commits will not track or duplicate these large binary chunks.
- **Shallow Clones:** Users cloning with shallow history (`git clone --depth 1`) will **not** download the 258 MB binary blobs.
- **Full Clones:** Users cloning with complete history (`git clone`) will still download the historical blobs from commit `a1b9446`, because Git retains all historical trees.
- **Safety Rule Compliance:** In strict accordance with the rule *"Do not reset, rebase, amend, or rewrite history"*, historical commits are left completely untouched. Purging blobs from past commits would require destructive history rewrites (`git filter-repo`), which is prohibited.

---

## 6. Exact Proposed Staging Plan

### Exact Files to Stage:
1. **Repository Configuration & Ignore Rules:**
   - `.gitignore`
   - `config.json`
2. **Application Backend & Seed Scripts:**
   - `backend/main.py`
   - `backend/seed.py`
   - `backend/ibm_benchmark_router.py`
   - `backend/phase4_router.py`
   - `backend/migrations/002_ibm_benchmark.sql`
   - `backend/migrations/003_fix_anomaly_score_constraint.sql`
3. **Application Desktop Frontend:**
   - `frontend/app.py`
4. **Project Status Documentation:**
   - `CURRENT_STATUS.md`
5. **Evaluation, Test Suite, and Benchmark Assets:**
   - All Python source and tests in `evaluation/amlsim_evaluation/`
   - All markdown engineering reports and runbooks in `evaluation/amlsim_evaluation/`
   - All sample alert/case fixtures and the 5 benchmark fixtures in `evaluation/amlsim_evaluation/ibm_export/artifacts/`

### Files to Exclude (Keep Untracked / Ignored):
- `dist/*` (6 files, 258.47 MB — Staged for removal from index)
- `reports/*.pdf` (2 files — Staged for removal from index)
- `evaluation/amlsim_evaluation/ibm_export/artifacts/evaluation_ground_truth.json` (Ignored)
- `evaluation/amlsim_evaluation/audit/*.npy` (6 files — Ignored)
- `data/` (Raw dataset directory — Ignored)
- `.env` (Ignored)

---

## 7. Safe Staging Commands (Ready for User Review)

When you are ready to stage these verified changes, the following commands execute the clean stage:

```powershell
# 1. Stage configuration and tracked modifications
git add .gitignore config.json backend/main.py backend/seed.py frontend/app.py

# 2. Stage new backend routers, migrations, and status doc
git add backend/ibm_benchmark_router.py backend/phase4_router.py backend/migrations/ CURRENT_STATUS.md

# 3. Stage evaluation code, test suites, reports, and benchmark fixtures
git add evaluation/amlsim_evaluation/

# 4. Confirm staging status (dist/ and ignored files will not be added)
git status --short
```

---

## 8. Audit Conclusion

The repository is clean, verified, and free of secrets, label leaks, and unneeded binary bloat. All prospective additions are production source code, regression tests, or reproducible benchmark fixtures.

**Awaiting user authorization before running any staging or commit commands.**
