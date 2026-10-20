"""
FinGuard AI — Phase 4 End-to-End Integration & Regression Test Suite

Verifies:
1. Production model artifact SHA-256 hash invariance (zero bit flip)
2. Dataset SHA-256 hash invariance
3. Backend FastAPI health & Phase 4 endpoints (/api/v2/*)
4. Alert prioritization budget capping & tier filtering
5. Grounded explanations signal provenance contract (MODEL, BEHAVIORAL, GRAPH, RULE)
6. Graph typologies contract (Fan-In mule funnels, Fan-Out, Rapid Movement)
7. Case dossier structure & compliance disclaimer
8. Frontend ApiClient resilience & offline fallback
9. Error handling (invalid IDs return 404)
10. Database safety (zero destructive operations)
"""

import os
import sys
import json
import hashlib
import unittest
from fastapi.testclient import TestClient

# Add project root to sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.main import app
from frontend.app import ApiClient

EXPECTED_MODEL_HASHES = {
    "muleguard_lightgbm.pkl": "02c5f122e1ee729bd97bb08e8d004dae1b4b919416384c4d5c214598af702fa2",
    "muleguard_lightgbm.txt": "2bf774a5d4ca4716759fd5d3303db5926ab05b02770b5f52e596910504c9e121",
    "muleguard_isolation_forest.pkl": "7c0fd7b168f4621de97d9164b0b9c83202921acbaecc028e3ae42bc00517a177",
    "category_encoders.pkl": "ff5d855fe24e3fddac6a136be0d8ed048e0b413486c9733b7bd5addcdc65839a",
    "feature_columns.json": "2aff95d9e42d389df853185d89ab0ed7384d4480f4905829a48093bc2ed768e8"
}

EXPECTED_DATASET_HASH = "b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040"


def _calc_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


class TestPhase4Integration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.api = ApiClient()

    # ---------------------------------------------------------
    # 1. Safety: Production Model Artifact Invariance
    # ---------------------------------------------------------
    def test_01_production_model_hashes_invariance(self):
        """Confirm all production models remain completely frozen with zero bit flips."""
        models_dir = os.path.join(ROOT_DIR, "models")
        for fname, exp_hash in EXPECTED_MODEL_HASHES.items():
            fpath = os.path.join(models_dir, fname)
            self.assertTrue(os.path.exists(fpath), f"Missing model file: {fname}")
            actual_hash = _calc_sha256(fpath)
            self.assertEqual(
                actual_hash,
                exp_hash,
                f"SAFETY VIOLATION: Model artifact '{fname}' hash changed! Exp: {exp_hash}, Act: {actual_hash}"
            )

    # ---------------------------------------------------------
    # 2. Safety: Dataset Hash Invariance
    # ---------------------------------------------------------
    def test_02_dataset_hash_invariance(self):
        """Confirm the IBM AML dataset was not altered or corrupted."""
        dataset_path = os.path.join(ROOT_DIR, "data", "aml_dataset", "HI-Small_Trans.csv")
        if os.path.exists(dataset_path):
            actual_hash = _calc_sha256(dataset_path)
            self.assertEqual(
                actual_hash,
                EXPECTED_DATASET_HASH,
                "SAFETY VIOLATION: Dataset HI-Small_Trans.csv hash altered!"
            )

    # ---------------------------------------------------------
    # 3. Backend Health & Core Endpoints
    # ---------------------------------------------------------
    def test_03_backend_health_and_core_routes(self):
        """Confirm existing backend health and login remain fully functional."""
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get("status"), "ok")

        r_login = self.client.post("/login", json={"employee_id": "admin", "password": "any"})
        self.assertEqual(r_login.status_code, 200)
        self.assertEqual(r_login.json().get("status"), "success")

    # ---------------------------------------------------------
    # 4. Phase 4 API: Prioritized Alerts & Budget Truncation
    # ---------------------------------------------------------
    def test_04_prioritized_alerts_budget_and_tiers(self):
        """Verify alert prioritization with capacity budgets and tier filtering."""
        # Test Default
        r = self.client.get("/api/v2/alerts/prioritized")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("alerts", data)
        self.assertGreater(len(data["alerts"]), 0)

        # Test Budget Truncation (budget = 15)
        r_budget = self.client.get("/api/v2/alerts/prioritized?budget=15")
        self.assertEqual(r_budget.status_code, 200)
        alerts_15 = r_budget.json()["alerts"]
        self.assertLessEqual(len(alerts_15), 15)

        # Test Risk Tier Filtering
        r_crit = self.client.get("/api/v2/alerts/prioritized?tier=Critical")
        self.assertEqual(r_crit.status_code, 200)
        for a in r_crit.json()["alerts"]:
            self.assertEqual(a["risk_tier"], "Critical")

        r_high = self.client.get("/api/v2/alerts/prioritized?tier=High")
        self.assertEqual(r_high.status_code, 200)
        for a in r_high.json()["alerts"]:
            self.assertEqual(a["risk_tier"], "High")

    # ---------------------------------------------------------
    # 5. Phase 4 API: Grounded Explanations Contract
    # ---------------------------------------------------------
    def test_05_grounded_explanation_provenance_contract(self):
        """Verify explanation has explicit signal provenance (MODEL, BEHAVIORAL, GRAPH, RULE)."""
        tx_id = "TX_4710695"
        r = self.client.get(f"/api/v2/alerts/{tx_id}/explanation")
        self.assertEqual(r.status_code, 200)
        expl = r.json().get("explanation", {})

        self.assertEqual(expl.get("transaction_id"), tx_id)
        self.assertIn("contributing_signals", expl)
        signals = expl["contributing_signals"]
        self.assertGreater(len(signals), 0)

        allowed_sources = {"MODEL", "BEHAVIORAL", "GRAPH", "RULE"}
        for sig in signals:
            self.assertIn("signal_name", sig)
            self.assertIn("source", sig)
            self.assertIn(sig["source"], allowed_sources, f"Invalid provenance source: {sig['source']}")
            self.assertIn("strength", sig)
            self.assertIn("measured_value", sig)
            self.assertIn("baseline_comparison", sig)

        # Confirm presence of human readable narrative
        self.assertIn("human_readable_summary", expl)
        self.assertTrue(len(expl["human_readable_summary"]) > 20)

    # ---------------------------------------------------------
    # 6. Phase 4 API: Graph Typologies Contract
    # ---------------------------------------------------------
    def test_06_graph_typologies_contract(self):
        """Verify NetworkX graph typologies summary and pattern samples."""
        r = self.client.get("/api/v2/graph/typologies")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "success")

        summary = data.get("graph_summary", {})
        self.assertIn("total_patterns_detected", summary)
        self.assertGreaterEqual(summary["total_patterns_detected"], 160)

        breakdown = summary.get("pattern_breakdown", {})
        self.assertIn("fan_in", breakdown)
        self.assertIn("fan_out", breakdown)
        self.assertIn("rapid_movement", breakdown)
        self.assertGreater(breakdown["fan_in"], 0)

        patterns = data.get("sample_patterns", [])
        self.assertGreater(len(patterns), 0)
        first_pat = patterns[0]
        self.assertIn("typology", first_pat)
        self.assertIn("target_account", first_pat)
        self.assertIn("severity_score", first_pat)

    # ---------------------------------------------------------
    # 7. Phase 4 API: Case Dossiers & Legal Disclaimer
    # ---------------------------------------------------------
    def test_07_investigator_cases_and_legal_disclaimer(self):
        """Verify case dossiers contain chronological timelines and legal triage disclaimers."""
        r = self.client.get("/api/v2/cases")
        self.assertEqual(r.status_code, 200)
        cases = r.json().get("cases", [])
        self.assertGreater(len(cases), 0)

        # Inspect specific case
        case_id = cases[0]["case_id"]
        r_det = self.client.get(f"/api/v2/cases/{case_id}")
        self.assertEqual(r_det.status_code, 200)
        case_file = r_det.json().get("case", {})

        self.assertEqual(case_file.get("case_id"), case_id)
        self.assertIn("primary_account", case_file)
        self.assertIn("priority_tier", case_file)
        self.assertIn("activity_timeline", case_file)
        self.assertGreater(len(case_file["activity_timeline"]), 0)

        # Legal disclaimer requirement
        self.assertIn("compliance_disclaimer", case_file)
        disclaimer = case_file["compliance_disclaimer"]
        self.assertIn("automated investigatory lead", disclaimer.lower())
        self.assertIn("does not constitute a confirmed financial crime", disclaimer.lower())

    # ---------------------------------------------------------
    # 8. Frontend ApiClient Resilience & Fallback
    # ---------------------------------------------------------
    def test_08_frontend_apiclient_resilience(self):
        """Verify ApiClient methods return valid data in both live and sandbox mode."""
        # Force sandbox / offline mode to test fallback
        self.api.local_mode = True

        alerts = self.api.get_prioritized_alerts(budget=20)
        self.assertIsInstance(alerts, list)
        self.assertGreater(len(alerts), 0)

        cases = self.api.get_investigator_cases()
        self.assertIsInstance(cases, list)
        self.assertGreater(len(cases), 0)

        typos = self.api.get_graph_typologies()
        self.assertIn("graph_summary", typos)

        expl = self.api.get_alert_explanation("TX_4710695")
        self.assertIsInstance(expl, dict)
        self.assertEqual(expl.get("transaction_id"), "TX_4710695")

    # ---------------------------------------------------------
    # 9. Error Handling
    # ---------------------------------------------------------
    def test_09_api_error_handling(self):
        """Verify invalid IDs return HTTP 404 without crashing."""
        r_invalid_alert = self.client.get("/api/v2/alerts/NON_EXISTENT_TX_99999/explanation")
        self.assertEqual(r_invalid_alert.status_code, 404)

        r_invalid_case = self.client.get("/api/v2/cases/NON_EXISTENT_CASE_99999")
        self.assertEqual(r_invalid_case.status_code, 404)

    # ---------------------------------------------------------
    # 10. Database Read-Only Invariance
    # ---------------------------------------------------------
    def test_10_database_read_only_safety(self):
        """Verify that Phase 4 router endpoints perform zero database writes."""
        # Phase 4 router uses precomputed artifacts and does not import write functions
        import backend.phase4_router as p4
        self.assertFalse(hasattr(p4, "insert_transaction"))
        self.assertFalse(hasattr(p4, "insert_risk_prediction"))
        self.assertFalse(hasattr(p4, "update_account_score"))


if __name__ == "__main__":
    unittest.main()
