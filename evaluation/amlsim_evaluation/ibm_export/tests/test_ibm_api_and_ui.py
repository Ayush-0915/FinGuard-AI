"""
FinGuard AI — IBM AML Benchmark API & UI Integration Tests (Phase D Gate 3)
Validates response schemas, pagination boundaries, database mock fallback,
strict label isolation, error handling, frontend ApiClient methods, and UI components.
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "backend"))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "frontend"))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

from main import app
from app import ApiClient


class TestIBMBenchmarkAPIAndUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.api = ApiClient()

    # -------------------------------------------------------------
    # 1. Endpoint Response Schemas
    # -------------------------------------------------------------
    def test_01_all_endpoint_response_schemas(self):
        """Verify all 5 endpoints return HTTP 200 with required schema fields."""
        # 1. /runs
        r_runs = self.client.get("/api/v2/ibm/runs")
        self.assertEqual(r_runs.status_code, 200)
        d_runs = r_runs.json()
        self.assertEqual(d_runs.get("status"), "success")
        self.assertIn("data_source", d_runs)
        self.assertIn("disclaimer", d_runs)
        self.assertGreater(d_runs.get("runs_count", 0), 0)
        first_run = d_runs["runs"][0]
        for field in ["run_id", "source_dataset", "source_sha256", "total_scanned_rows", "selected_records_count", "model_version"]:
            self.assertIn(field, first_run)

        # 2. /summary
        r_sum = self.client.get("/api/v2/ibm/summary")
        self.assertEqual(r_sum.status_code, 200)
        d_sum = r_sum.json()
        self.assertEqual(d_sum.get("status"), "success")
        self.assertEqual(d_sum.get("total_scanned_rows"), 5078345)
        self.assertEqual(d_sum.get("selected_records_count"), 1000)
        self.assertIn("tier_distribution", d_sum)

        # 3. /transactions
        r_tx = self.client.get("/api/v2/ibm/transactions?page=1&limit=25")
        self.assertEqual(r_tx.status_code, 200)
        d_tx = r_tx.json()
        self.assertEqual(d_tx.get("status"), "success")
        self.assertEqual(d_tx.get("limit"), 25)
        self.assertEqual(len(d_tx.get("transactions", [])), 25)
        first_tx = d_tx["transactions"][0]
        for field in ["transaction_id", "run_id", "timestamp", "sender_account", "receiver_account", "amount", "receiving_currency", "payment_format"]:
            self.assertIn(field, first_tx)

        # 4. /alerts
        r_al = self.client.get("/api/v2/ibm/alerts?budget=20&tier=Critical")
        self.assertEqual(r_al.status_code, 200)
        d_al = r_al.json()
        self.assertEqual(d_al.get("status"), "success")
        self.assertEqual(d_al.get("budget"), 20)
        self.assertEqual(d_al.get("tier_filter"), "Critical")
        self.assertEqual(len(d_al.get("alerts", [])), 20)
        first_al = d_al["alerts"][0]
        for field in ["transaction_id", "model_risk_score", "risk_rank", "risk_tier"]:
            self.assertIn(field, first_al)

        # 5. /transactions/{id}/evidence
        tx_id = first_al["transaction_id"]
        r_ev = self.client.get(f"/api/v2/ibm/transactions/{tx_id}/evidence")
        self.assertEqual(r_ev.status_code, 200)
        d_ev = r_ev.json()
        self.assertEqual(d_ev.get("status"), "success")
        self.assertEqual(d_ev.get("transaction_id"), tx_id)
        self.assertIn("contributing_signals", d_ev)
        self.assertIn("human_readable_summary", d_ev)

    # -------------------------------------------------------------
    # 2. Pagination & Parameter Validation Bounds
    # -------------------------------------------------------------
    def test_02_pagination_and_parameter_bounds(self):
        """Verify strict pagination limits and HTTP 422 on invalid parameters."""
        # Valid page 2
        r_p2 = self.client.get("/api/v2/ibm/transactions?page=2&limit=50")
        self.assertEqual(r_p2.status_code, 200)
        self.assertEqual(r_p2.json().get("page"), 2)

        # Invalid page 0 (must be >= 1)
        r_zero = self.client.get("/api/v2/ibm/transactions?page=0")
        self.assertEqual(r_zero.status_code, 422)

        # Invalid negative page
        r_neg = self.client.get("/api/v2/ibm/transactions?page=-5")
        self.assertEqual(r_neg.status_code, 422)

        # Limit exceeds 100 max
        r_lim = self.client.get("/api/v2/ibm/transactions?limit=150")
        self.assertEqual(r_lim.status_code, 422)

        # Budget exceeds 500 max
        r_bud = self.client.get("/api/v2/ibm/alerts?budget=1000")
        self.assertEqual(r_bud.status_code, 422)

        # Currency and payment_format filtering
        r_filt = self.client.get("/api/v2/ibm/transactions?currency=US%20Dollar&payment_format=ACH&limit=10")
        self.assertEqual(r_filt.status_code, 200)
        txs = r_filt.json().get("transactions", [])
        for t in txs:
            self.assertTrue(
                t.get("receiving_currency") == "US Dollar" or t.get("payment_currency") == "US Dollar"
            )
            self.assertEqual(t.get("payment_format"), "ACH")

    # -------------------------------------------------------------
    # 3. Missing Tables & Database Failure Graceful Fallback
    # -------------------------------------------------------------
    def test_03_missing_tables_and_graceful_fallback(self):
        """Verify that when database tables do not exist or fail, API gracefully falls back."""
        with patch("ibm_benchmark_router._supabase_client") as mock_sb:
            mock_sb.table.side_effect = Exception("PGRST205 table 'ibm_benchmark_transactions' not found")

            r = self.client.get("/api/v2/ibm/transactions?limit=10")
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertEqual(data.get("data_source"), "local_fixture_fallback")
            self.assertEqual(len(data.get("transactions", [])), 10)

    # -------------------------------------------------------------
    # 4. Offline Fixture Fallback & Source Indicators
    # -------------------------------------------------------------
    def test_04_offline_fixture_fallback_and_source_indicators(self):
        """Verify explicit data_source indicator and disclaimer when offline."""
        with patch("ibm_benchmark_router._supabase_client", None):
            for endpoint in ["/api/v2/ibm/runs", "/api/v2/ibm/summary", "/api/v2/ibm/transactions?limit=5", "/api/v2/ibm/alerts?budget=5"]:
                r = self.client.get(endpoint)
                self.assertEqual(r.status_code, 200)
                data = r.json()
                self.assertEqual(data.get("data_source"), "local_fixture_fallback")
                self.assertIn("disclaimer", data)
                self.assertIn("IBM Transactions for Anti-Money Laundering", data["disclaimer"])

    # -------------------------------------------------------------
    # 5. Strict Label Isolation in API Responses
    # -------------------------------------------------------------
    def test_05_strict_label_isolation(self):
        """Verify ground-truth laundering labels are completely absent from all API payloads."""
        r_tx = self.client.get("/api/v2/ibm/transactions?limit=100")
        r_al = self.client.get("/api/v2/ibm/alerts?budget=100")
        
        all_items = r_tx.json().get("transactions", []) + r_al.json().get("alerts", [])
        forbidden = ["is_laundering", "islaundering", "target", "label", "sar", "ground_truth"]
        
        for item in all_items:
            for k in item.keys():
                for f in forbidden:
                    self.assertNotIn(f, k.lower(), f"Forbidden label key '{k}' found in operational payload!")

    # -------------------------------------------------------------
    # 6. Database Mock Live Source Indicator
    # -------------------------------------------------------------
    def test_06_database_mock_live_source(self):
        """Verify that when database query succeeds, data_source indicates 'supabase_database'."""
        mock_result = MagicMock()
        mock_result.data = [
            {
                "transaction_id": "IBM_TX_9999999",
                "run_id": "RUN-TEST",
                "timestamp": "2022/09/01 12:00",
                "sender_account": "ACC_S",
                "receiver_account": "ACC_R",
                "amount": 5000.0,
                "receiving_currency": "US Dollar",
                "payment_currency": "US Dollar",
                "payment_format": "ACH",
                "from_bank": 1,
                "to_bank": 2
            }
        ]
        mock_result.count = 1

        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value.execute.return_value = mock_result

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value = mock_query

        with patch("ibm_benchmark_router._supabase_client", mock_sb):
            r = self.client.get("/api/v2/ibm/transactions?limit=1")
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertEqual(data.get("data_source"), "supabase_database")
            self.assertEqual(data.get("transactions")[0]["transaction_id"], "IBM_TX_9999999")

    # -------------------------------------------------------------
    # 7. 404 Error Handling for Missing IDs
    # -------------------------------------------------------------
    def test_07_api_not_found_handling(self):
        """Verify clean HTTP 404 responses for missing transaction IDs and run IDs."""
        r_ev = self.client.get("/api/v2/ibm/transactions/NON_EXISTENT_TX/evidence")
        self.assertEqual(r_ev.status_code, 404)
        self.assertIn("detail", r_ev.json())

        r_sum = self.client.get("/api/v2/ibm/summary?run_id=NON_EXISTENT_RUN")
        self.assertEqual(r_sum.status_code, 404)
        self.assertIn("detail", r_sum.json())

    # -------------------------------------------------------------
    # 8. Existing Routes Regression Safety
    # -------------------------------------------------------------
    def test_08_existing_routes_regression(self):
        """Verify that mounting the IBM Benchmark router did not break existing routes."""
        # /health
        r_h = self.client.get("/health")
        self.assertEqual(r_h.status_code, 200)

        # /api/v2/alerts/prioritized (Phase 4)
        r_p4 = self.client.get("/api/v2/alerts/prioritized?budget=10")
        self.assertEqual(r_p4.status_code, 200)

        # /api/v2/graph/typologies (Phase 4)
        r_gt = self.client.get("/api/v2/graph/typologies")
        self.assertEqual(r_gt.status_code, 200)

        # /api/v2/cases (Phase 4)
        r_cs = self.client.get("/api/v2/cases")
        self.assertEqual(r_cs.status_code, 200)

    # -------------------------------------------------------------
    # 9. Frontend ApiClient IBM Methods & Credential Security
    # -------------------------------------------------------------
    def test_09_frontend_apiclient_methods(self):
        """Verify that ApiClient methods return valid benchmark structures and contain zero secrets."""
        runs = self.api.get_ibm_runs()
        self.assertEqual(runs.get("status"), "success")
        self.assertGreater(runs.get("runs_count", 0), 0)

        summary = self.api.get_ibm_summary()
        self.assertEqual(summary.get("total_scanned_rows"), 5078345)
        self.assertEqual(summary.get("selected_records_count"), 1000)

        txs = self.api.get_ibm_transactions(page=1, limit=10)
        self.assertEqual(len(txs.get("transactions", [])), 10)

        alerts = self.api.get_ibm_alerts(budget=10, tier="Critical")
        self.assertEqual(len(alerts.get("alerts", [])), 10)

        ev = self.api.get_ibm_evidence(alerts.get("alerts")[0]["transaction_id"])
        self.assertIsNotNone(ev)
        self.assertIn("contributing_signals", ev)

        # Credential safety
        with open(os.path.join(FRONTEND_DIR, "app.py"), "r", encoding="utf-8") as f:
            frontend_code = f.read()
        self.assertNotIn("service_role", frontend_code)
        self.assertNotIn("SUPABASE_KEY", frontend_code)

    # -------------------------------------------------------------
    # 10. Desktop Benchmark Mode UI Components
    # -------------------------------------------------------------
    def test_10_desktop_benchmark_mode_components(self):
        """Verify that IBMBenchmarkView and MainWindow benchmark toggle initialize properly."""
        try:
            from PySide6.QtWidgets import QApplication
            app_inst = QApplication.instance()
            if not app_inst:
                app_inst = QApplication([])
            
            from app import IBMBenchmarkView, MainWindow
            
            # Check IBMBenchmarkView instantiation
            view = IBMBenchmarkView(self.api)
            self.assertEqual(view.badge_scanned.text(), "Scanned Population: 5,078,345")
            self.assertEqual(view.badge_cohort.text(), "Selected Benchmark Cohort: 1,000")
            self.assertEqual(view.tabs.count(), 3)
            self.assertEqual(view.tabs.tabText(0), "Prioritized Alerts & Triage")
            self.assertEqual(view.tabs.tabText(1), "Benchmark Transactions (Paginated)")
            self.assertEqual(view.tabs.tabText(2), "Dataset Provenance & Verification")

            # Check MainWindow benchmark toggle
            win = MainWindow(self.api)
            self.assertTrue(hasattr(win, "btn_benchmark_toggle"))
            self.assertTrue(hasattr(win, "page_ibm_benchmark"))
            self.assertEqual(win.content_stack.count(), 13) # Pages 0 to 12
        except Exception as e:
            # If running in a headless CI/CLI without X11 or display server
            if "qt.qpa.plugin" in str(e).lower() or "display" in str(e).lower():
                print(f"Skipping headless GUI render check: {e}")
            else:
                raise e


if __name__ == "__main__":
    unittest.main()
