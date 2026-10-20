# FinGuard AI — Phase 2 Independent Audit Reproduction Guide

This guide details the exact steps and commands required to reproduce the independent verification audit of Phase 2 on the local Windows environment.

## 1. Environment & Prerequisites

- **Operating System:** Windows 10 / 11
- **Python Virtual Environment:** `.venv` (Python 3.11)
- **Key Dependencies:**
  - `lightgbm == 4.5.0`
  - `pandas == 2.2.3`
  - `numpy == 2.1.3`
  - `scikit-learn == 1.6.1`
  - `joblib == 1.4.2`
- **Dataset File:** `data/aml_dataset/HI-Small_Trans.csv` (475,664,283 bytes, SHA-256: `b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040`)

---

## 2. Step-by-Step Reproduction Commands

Open PowerShell in the project root:
```powershell
cd C:\Users\ayush\Desktop\Private\MuleGuard
```

### Step 1: Execute Automated Feature Pipeline Unit Tests
Run the 10 invariant unit tests on the synthetic hand-crafted fixture:
```powershell
.venv\Scripts\python.exe evaluation\amlsim_evaluation\test_feature_pipeline.py
```
*Expected Output:*
```text
Ran 10 tests in ~0.05s
OK
```

### Step 2: Execute Independent Audit Runner
Run the full independent verification audit script:
```powershell
.venv\Scripts\python.exe evaluation\amlsim_evaluation\audit\run_independent_audit.py
```
*Execution details:*
- Computes SHA-256 hashes of all artifacts.
- Runs the Future-History Invariance Test.
- Streams all 5,078,345 records through `PointInTimeFeatureEngine`.
- Evaluates saved model binaries (`muleguard_lightgbm.pkl` and `experimental_lightgbm.pkl`).
- Verifies threshold tuning on the Validation set.
- Recomputes all test classification metrics and confusion matrices.
- Evaluates 6 distinct unseen-account subsets.
- Verifies the early stopping trajectory across 60 iterations.
- Analyzes financial volume recovery and top-k alert triage precision.
- Serializes raw prediction arrays (`val_probs_zero_shot.npy`, `test_probs_zero_shot.npy`, `val_probs_exp.npy`, `test_probs_exp.npy`, `y_val.npy`, `y_test.npy`) to `evaluation/amlsim_evaluation/audit/`.
- Total runtime: ~60–70 seconds.

---

## 3. Verification Artifacts & Output Paths

All audit outputs are written strictly within `evaluation/amlsim_evaluation/audit/`:
- **`PHASE2_INDEPENDENT_AUDIT.md`**: Comprehensive authoritative audit report.
- **`audit_results.json`**: Machine-readable recomputed metrics, statuses, and top-k distributions.
- **`audit_artifact_hashes.txt`**: SHA-256 checksums of all evaluated models, sources, and configs.
- **`*.npy`**: Serialized prediction and label arrays for permanent independent verification.
