"""
Unified Regression Test Runner for FinGuard AI
Executes all unit and integration tests across Phase 2, Phase 3, and Phase 4.
"""

import sys
import os
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

test_files = [
    # Phase 2
    os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "test_feature_pipeline.py"),
    # Phase 3
    os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "phase3", "test_alert_prioritizer.py"),
    os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "phase3", "test_graph_intelligence.py"),
    os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "phase3", "test_explanation_engine.py"),
    os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "phase3", "test_risk_fusion.py"),
    os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "phase3", "test_case_builder.py"),
    # Phase 4
    os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "phase4", "test_phase4_integration.py"),
    # IBM Export Hybrid Pipeline
    os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "ibm_export", "tests", "test_ibm_export.py"),
    # IBM API & UI Integration (Phase D Gate 3)
    os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "ibm_export", "tests", "test_ibm_api_and_ui.py"),
    # Model Intelligence & Performance Dashboard
    os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "phase4", "test_model_intelligence.py")
]

suite = unittest.TestSuite()
loader = unittest.TestLoader()

for fpath in test_files:
    if os.path.exists(fpath):
        dirname = os.path.dirname(fpath)
        mod_name = os.path.splitext(os.path.basename(fpath))[0]
        if dirname not in sys.path:
            sys.path.insert(0, dirname)
        try:
            mod = __import__(mod_name)
            tests = loader.loadTestsFromModule(mod)
            suite.addTests(tests)
        except Exception as e:
            print(f"Error loading {fpath}: {e}")

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

print("\n" + "=" * 60)
print(f"FINGUARD AI REGRESSION SUITE EXECUTION SUMMARY")
print("=" * 60)
print(f"Total Test Cases Run: {result.testsRun}")
print(f"Pass Count          : {result.testsRun - len(result.failures) - len(result.errors)}")
print(f"Failure Count       : {len(result.failures)}")
print(f"Error Count         : {len(result.errors)}")
print(f"Overall Result      : {'SUCCESS (100% Passed)' if result.wasSuccessful() else 'FAILED'}")
print("=" * 60)

if not result.wasSuccessful():
    sys.exit(1)
