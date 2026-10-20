# FinGuard AI — GitHub Repository Cleanup Audit & Proposed Plan

**Project:** FinGuard AI — AI-Powered Financial Crime Detection and Risk Intelligence  
**Repository Root:** `C:\Users\ayush\Desktop\Private\MuleGuard`  
**Expected Remote:** `https://github.com/Ayush-0915/Private-Project.git`  
**Audit Date:** October 20, 2026  
**Auditor:** FinGuard AI Quality & Architecture Engineering  
**Mode:** READ-ONLY AUDIT (Zero repository modifications, zero deletions, zero commits, zero pushes)

---

## 1. Executive Baseline & Git Status

All audit commands were executed in the repository root.

### A. Git Diagnostics Record
- **Branch:** `main` (synchronized with `origin/main` at commit `711ab10`)
- **Remote Configuration:**
  ```text
  origin  https://github.com/Ayush-0915/Private-Project.git (fetch)
  origin  https://github.com/Ayush-0915/Private-Project.git (push)
  ```
- **Last Commit:** `711ab10 Updatwd`
- **Tracked Files Count:** **47 files**
- **Untracked Non-Ignored Files Count:** **85 files**
- **Tracked Modified Files (Unstaged):** **5 files**
  - `.gitignore` (+3 lines: `data/`)
  - `backend/main.py` (+16 lines: Phase 4 & IBM benchmark routers mounted)
  - `backend/seed.py` (+700 lines: idempotent non-destructive showcase data seeder)
  - `config.json` (+2 lines)
  - `frontend/app.py` (+1600 lines: Desktop Benchmark Mode view & ApiClient methods)
- **Staged Changes (`git diff --cached`):** **None (0 files)**

---

## 2. Repository Inventory & Categorization Table

| File / Directory Path | Current Git Status | Size / Footprint | Category | Reason for Exclusion or Retention | Recommended Action | Risk if Removed / Excluded |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| `dist/app_split.z01` | **Tracked** | 50.00 MB | Build Output | PyInstaller multi-part split binary. | **Exclude from Git** (`git rm --cached`) | **None.** Preserved locally on disk. Releases belong in GitHub Releases. |
| `dist/app_split.z02` | **Tracked** | 50.00 MB | Build Output | PyInstaller multi-part split binary. | **Exclude from Git** (`git rm --cached`) | **None.** Local copy preserved. |
| `dist/app_split.zip` | **Tracked** | 38.44 MB | Build Output | PyInstaller multi-part split binary. | **Exclude from Git** (`git rm --cached`) | **None.** Local copy preserved. |
| `dist/main_split.z01` | **Tracked** | 50.00 MB | Build Output | PyInstaller multi-part split binary. | **Exclude from Git** (`git rm --cached`) | **None.** Local copy preserved. |
| `dist/main_split.z02` | **Tracked** | 50.00 MB | Build Output | PyInstaller multi-part split binary. | **Exclude from Git** (`git rm --cached`) | **None.** Local copy preserved. |
| `dist/main_split.zip` | **Tracked** | 20.03 MB | Build Output | PyInstaller multi-part split binary. | **Exclude from Git** (`git rm --cached`) | **None.** Local copy preserved. |
| `reports/*.pdf` (2 files) | **Tracked** | ~52 KB | Test Output | Generated sample investigation PDFs. | **Exclude from Git** (`git rm --cached`) | **None.** Generated on demand by backend report generator. |
| `app.spec` | **Tracked** | 6.2 KB | Build Spec | PyInstaller build specification. | **Retain Tracked** | Ensures desktop packaging can be reproduced. |
| `models/*.pkl`, `*.json`, `*.txt` | **Tracked** | ~12.2 MB | Production Assets | Production LightGBM, Isolation Forest, SHAP models & configs. | **MUST RETAIN** | **CRITICAL:** Application backend fails startup if models are removed. |
| `data/aml_dataset/*` | **Ignored** | ~40.5 GB | Large Raw Dataset | Raw IBM AML CSV files (up to 17GB each). | **Remain Ignored** (covered by `data/`) | **CRITICAL:** Will exceed GitHub file limits (100MB) if tracked. |
| `.env` | **Ignored** | ~240 B | Secret Credentials | Live Supabase keys and local connection variables. | **Remain Ignored** (covered by `.env`) | **CRITICAL:** Leaks cloud database credentials if committed. |
| `.env.example` | **Tracked** | 480 B | Documentation | Environment variable template with placeholders. | **MUST RETAIN** | Documents required environment variables for onboarding. |
| `evaluation/.../evaluation_ground_truth.json` | **Untracked** | 17.7 KB | Sensitive Offline Labels | Contains ground-truth `Is Laundering` labels for 1,000 records. | **Exclude from Git** (add to `.gitignore`) | Preserves strict offline quarantine of benchmark ground truth. |
| `evaluation/.../audit/*.npy` (6 files) | **Untracked** | 21.82 MB | Raw Intermediate Arrays | Numpy prediction arrays from Phase 2 audit reproduction. | **Exclude from Git** (add `*.npy` to `.gitignore`) | **None.** Summary metrics already recorded in `audit_results.json`. |
| `backend/ibm_benchmark_router.py` | **Untracked** | 18.2 KB | Application Source | Phase D benchmark REST API endpoints (`/api/v2/ibm`). | **Track in Git** (`git add`) | **HIGH:** Backend benchmark endpoints missing if not committed. |
| `backend/phase4_router.py` | **Untracked** | 16.5 KB | Application Source | Phase 4 intelligence REST API endpoints (`/api/v2/alerts`). | **Track in Git** (`git add`) | **HIGH:** Prioritization and case endpoints missing if not committed. |
| `backend/migrations/*.sql` (2 files) | **Untracked** | ~8 KB | Database Migrations | DDL migrations 002 (benchmark tables) & 003 (anomaly check). | **Track in Git** (`git add`) | **HIGH:** Database schema reproducibility lost if omitted. |
| `evaluation/amlsim_evaluation/*.py` | **Untracked** | Source Code | Feature engine, pipeline tests, reproducibility scripts. | **Track in Git** (`git add`) | **HIGH:** Feature pipeline code and tests lost. |
| `evaluation/amlsim_evaluation/*.md` | **Untracked** | Documentation | Engineering audit reports, experiment plans, runbooks. | **Track in Git** (`git add`) | Research reproducibility documentation lost. |
| `evaluation/amlsim_evaluation/phase3/*` | **Untracked** | Source & Tests | Prioritizer, graph intelligence, risk fusion, case builder. | **Track in Git** (`git add`) | Phase 3 intelligence engine lost. |
| `evaluation/amlsim_evaluation/phase4/*` | **Untracked** | Source & Tests | Unified test runner (`run_all_tests.py`), integration tests. | **Track in Git** (`git add`) | Regression test suite lost. |
| `evaluation/amlsim_evaluation/ibm_export/*.py` | **Untracked** | Source Code | Publisher, scoring, selection, dataset reader, config. | **Track in Git** (`git add`) | Export and publication pipeline lost. |
| `evaluation/amlsim_evaluation/ibm_export/artifacts/*.json` (5 files) | **Untracked** | ~2.5 MB | Benchmark Fixtures | 1:1:1 benchmark transactions, scores, evidence, manifest. | **Track in Git** (`git add`) | Required for local fixture fallback when Supabase is offline. |

---

## 3. Detailed Finding Categories

### 1. Large Tracked Binary Build Bloat (`dist/`)
- Six multi-part split binaries (`dist/app_split.*`, `dist/main_split.*`) totaling **258.47 MB** are currently tracked by Git.
- While `dist/` is listed in `.gitignore` (line 13), these files were committed before the ignore rule was established. Git will continue tracking them until they are removed from the index.
- **Remediation:** Remove them from the index via `git rm --cached dist/*`. This purges 258 MB from future repository transfers while leaving the compiled binaries untouched on local disk.

### 2. Large Raw Datasets (`data/`)
- `data/aml_dataset/` contains 18 raw CSV and pattern files totaling over **40.5 GB** (including `HI-Large_Trans.csv` at 17.0 GB and `HI-Small_Trans.csv` at 475.6 MB).
- `.gitignore` (line 112: `data/`, line 30: `*.csv`) successfully ignores all of them.
- **Remediation:** No action required; ignore rules are working properly.

### 3. Offline Ground Truth Label Quarantine
- `evaluation/amlsim_evaluation/ibm_export/artifacts/evaluation_ground_truth.json` (17.7 KB) contains the raw `Is Laundering` labels for the 1,000 selected benchmark records.
- Throughout Phases B, C, and D, FinGuard AI established a strict architectural boundary ensuring operational API payloads, live Supabase tables, and client views never expose ground-truth labels.
- **Remediation:** Add `evaluation/amlsim_evaluation/ibm_export/artifacts/evaluation_ground_truth.json` to `.gitignore` to prevent ground truth from being published to the remote repository.

### 4. Intermediate Evaluation Numpy Arrays (`*.npy`)
- `evaluation/amlsim_evaluation/audit/` contains 6 raw prediction probability arrays (`val_probs_exp.npy`, `test_probs_exp.npy`, etc.) totaling **21.82 MB**.
- These are intermediate dump files from Phase 2 audit reproduction. The audited evaluation metrics, confusion matrices, and verification hashes are already captured in `audit_results.json` and `audit_artifact_hashes.txt`.
- **Remediation:** Add `*.npy` to `.gitignore`.

### 5. Secrets and Credential Exposure Audit
- Executed automated regex scanning across all 132 tracked and untracked repository files.
- **Supabase / JWT Tokens:** 0 found in source or untracked candidate files.
- **API Keys / Service Role Secrets:** 0 hardcoded keys found.
- **Private Key Headers:** 0 found.
- `.env` is confirmed untracked and covered by `.gitignore` (line 97).
- `.env.example` contains only harmless public template placeholders (`https://your-project-ref.supabase.co`).

---

## 4. Proposed Minimal `.gitignore` Updates

To enforce proper hygiene without ignoring critical evaluation code or reports, append the following minimal entries to `.gitignore`:

```diff
--- a/.gitignore
+++ b/.gitignore
@@ -110,3 +110,9 @@ Thumbs.db
 
 # Dataset directory
 data/
+
+# Evaluation intermediate arrays and offline ground-truth quarantine
+*.npy
+evaluation/amlsim_evaluation/ibm_export/artifacts/evaluation_ground_truth.json
+reports/*.pdf
```

> [!NOTE]
> `evaluation/` is **NEVER** ignored globally. All Python source code, unit tests, regression suites, runbooks, engineering reports, manifests, and offline benchmark fixtures remain fully tracked.

---

## 5. Exact Proposed Commands for User Review

The following non-destructive sequence is proposed for execution **only upon explicit user approval**:

### Step 1: Untrack Already-Committed Build Binaries & Sample Reports (Index Only)
```powershell
# Remove 258MB of PyInstaller split binaries from Git index (preserves local disk files)
git rm --cached dist/app_split.z01 dist/app_split.z02 dist/app_split.zip dist/main_split.z01 dist/main_split.z02 dist/main_split.zip

# Remove sample generated PDF reports from Git index (preserves local disk files)
git rm --cached reports/Investigation_Report_ACC-10293.pdf reports/test_report.pdf
```

### Step 2: Update `.gitignore` with Targeted Exclusions
```powershell
# Append targeted ignore rules for numpy arrays, offline ground truth, and reports
Add-Content -Path .gitignore -Value "`n# Evaluation intermediate arrays and offline ground-truth quarantine`n*.npy`nevaluation/amlsim_evaluation/ibm_export/artifacts/evaluation_ground_truth.json`nreports/*.pdf"
```

### Step 3: Stage Essential Application Code, Migrations, Tests, and Reports
```powershell
# Stage modified tracked files
git add .gitignore backend/main.py backend/seed.py config.json frontend/app.py

# Stage new application routers and database migrations
git add backend/ibm_benchmark_router.py backend/phase4_router.py backend/migrations/

# Stage documentation
git add CURRENT_STATUS.md

# Stage evaluation source, test suites, reports, and benchmark fixtures
git add evaluation/amlsim_evaluation/
```

### Step 4: Verification Check Before Commit
```powershell
# Verify that dist/, *.npy, and evaluation_ground_truth.json are NOT staged
git status --short
```

---

## 6. Audit Verdict and Next Steps

The repository is healthy, secure, and ready for cleanup. All candidate exclusions have been isolated without risking runtime functionality or reproducible evaluation assets.

**Awaiting user authorization before running any of the above commands.**
