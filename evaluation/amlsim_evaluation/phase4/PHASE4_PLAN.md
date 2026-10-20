# FinGuard AI — Phase 4 Implementation Plan: Safe Integration, End-to-End Validation & Demo Readiness

**Project:** FinGuard AI — AI-Powered Financial Crime Detection and Risk Intelligence  
**Path:** `C:\Users\ayush\Desktop\Private\MuleGuard`  
**Phase:** 4 (Safe Application Integration & College Showcase Validation)  
**Date:** October 2026  
**Status:** Approved for Implementation  

---

## 1. Executive Summary & Objectives

The primary objective of Phase 4 is to safely integrate selected capabilities developed in Phase 3 (Alert Prioritization, Grounded Explanations, NetworkX Graph Typologies, and Investigator Case Dossiers) into the existing FinGuard AI application stack (FastAPI backend + PySide6 desktop GUI), perform end-to-end regression validation, and deliver a polished, foolproof demonstration workflow for college evaluations and stakeholder showcases.

### Core Objectives
1. **Zero-Disruption Integration:** Integrate Phase 3 intelligence into the FastAPI backend and PySide6 frontend without breaking existing features, database tables, or production models.
2. **Strict Production Safety & Isolation:**
   - Production models (`models/muleguard_lightgbm.pkl`, `models/category_encoders.pkl`, etc.) remain 100% frozen with verified SHA-256 hash invariance.
   - Database schemas in Supabase remain untouched; zero destructive queries or schema alterations.
   - Zero credential exposure (`.env` remains private and uncommitted).
3. **Honest Metric Framing:**
   - Clearly delineate benchmark simulation results (e.g., 94.41% recall or 99.70% alert volume reduction) from real-time production guarantees.
   - Present model-probability ranking as the primary baseline, with graph and fused indicators serving as corroborating investigative context.
4. **Resilient Demo Architecture:**
   - Implement dual-mode operational capability: live FastAPI backend connection with automatic fallback to pre-computed deterministic JSON fixtures if backend or external networks are unavailable.
5. **Comprehensive Verification & Reporting:**
   - Provide automated regression and end-to-end tests validating API routes, data contracts, and hash invariance.
   - Deliver `DEMO_RUNBOOK.md`, `DEMO_CHECKLIST.md`, and authoritative `PHASE4_REPORT.md`.

---

## 2. Architectural Blueprint

```
+-----------------------------------------------------------------------------------+
|                            PYSIDE6 DESKTOP APPLICATION                            |
|                                                                                   |
|  [Sidebar Navigation]                                                             |
|   |-- Overview: Dashboard (0)                                                     |
|   |-- Risk Monitoring: Active Alerts (1), Live Txs (2), Alert Prioritization (10)  |
|   |-- Investigation: Accounts (3), Txs (4), Network (5), Case Dossiers (11)       |
|   `-- Analytics: Fraud Analytics (6), Regional (7), Payment Methods (8)           |
+-----------------------------------------+-----------------------------------------+
                                          |
                      HTTP REST Calls     | (Fallback to Local Mock DB / Fixtures
                      via ApiClient       |  if backend is offline)
                                          v
+-----------------------------------------------------------------------------------+
|                              FASTAPI BACKEND SERVICE                              |
|                                                                                   |
|  Existing Endpoints:               Phase 4 Intelligence Endpoints:                |
|   - /health, /login                 - GET /api/v2/alerts/prioritized              |
|   - /dashboard, /accounts           - GET /api/v2/alerts/{id}/explanation         |
|   - /transactions, /alerts          - GET /api/v2/graph/typologies                |
|   - /network/{id}, /risk/{id}       - GET /api/v2/cases                           |
|   - /explanation/{id}, /predict     - GET /api/v2/cases/{case_id}                 |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          +--> Loads from Phase 3 Artifacts:
                                               - sample_alerts.json
                                               - phase3_results.json
                                               - artifacts/cases/*.json
```

---

## 3. Implementation Steps

### Step 1: Backend Router (`backend/phase4_router.py`)
Create a modular FastAPI `APIRouter` with prefix `/api/v2`:
- `GET /api/v2/alerts/prioritized?budget=500&tier=Critical`:
  - Returns prioritized alerts filtered by investigator operational budget (100 to 5000) and risk tier (Critical, High, Medium, Low).
  - Supplies both `model_risk_score` (primary rank) and `fused_risk_score` (graph + behavioral).
- `GET /api/v2/alerts/{transaction_id}/explanation`:
  - Returns grounded multi-source signal breakdown with explicit provenance tags (`MODEL`, `BEHAVIORAL`, `GRAPH`, `RULE`).
  - Zero fabricated SHAP coefficients; strictly grounded in measured data.
- `GET /api/v2/graph/typologies`:
  - Returns detected NetworkX laundering topologies: Fan-In Aggregation (Mule Funnel), Fan-Out Disbursement, Rapid Movement, High-Value Anomalies.
- `GET /api/v2/cases`:
  - Returns list of summarized investigative case dossiers.
- `GET /api/v2/cases/{case_id}`:
  - Returns complete case dossier including chronological activity timeline, connected accounts, and mandatory legal compliance disclaimer.

Mount this router seamlessly in `backend/main.py`.

### Step 2: PySide6 Desktop Frontend Integration (`frontend/app.py`)
1. **ApiClient Enhancements:**
   - Add client helper methods:
     - `get_prioritized_alerts(budget=500, tier="All")`
     - `get_grounded_explanation(tx_id)`
     - `get_graph_typologies()`
     - `get_investigator_cases()`
     - `get_case_detail(case_id)`
   - Implement robust offline fallback using bundled Phase 3 fixtures so the UI renders smoothly even without an active backend server.
2. **New Dedicated Views:**
   - **`AlertPrioritizationView` (Index 10):**
     - Budget selector dropdown (100, 250, 500, 1000, 2500, 5000).
     - Risk tier filter pills (All, Critical, High, Medium, Low).
     - Interactive table showing Rank, Transaction ID, Timestamp, Counterparties, Volume, Priority Tier badge, and Model Score.
     - Side drawer / detail card displaying grounded explanation with signal provenance badges.
   - **`CaseDossierView` (Index 11):**
     - Case selector table showing Case ID, Primary Account, Priority, Suspicious Volume, Alert Count, and Review Status.
     - Detailed dossier viewer displaying chronological timeline, involved accounts, detected typologies, and prominent AML compliance disclaimer.
3. **Sidebar Updates:**
   - Add `"Alert Prioritization"` under `RISK MONITORING` (Index 10).
   - Add `"Case Dossiers"` under `INVESTIGATION` (Index 11).

---

## 4. Safety Constraints & Verification Criteria

| Constraint | Enforcement Mechanism | Acceptance Threshold |
|---|---|---|
| **Model Invariance** | SHA-256 hash checks on all 5 model files | Hashes must match baseline exactly (zero bit flip) |
| **Database Safety** | Supabase query auditing | Zero `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER` queries executed on production tables during tests |
| **Credential Safety** | Code inspection & regex scans | Zero `.env` values logged, exposed, or committed |
| **Endpoint Integrity** | Automated HTTP status and schema validation | All `/api/v2/*` endpoints return HTTP 200 with required schema fields |
| **Regression Suite** | Phase 2 (10 tests) + Phase 3 (21 tests) | 31/31 existing tests must pass with 100% success |
| **Offline Resilience** | Unit test with mocked unreachable network | ApiClient returns cached fixtures without crashing UI |

---

## 5. Demonstration Runbook Flow

The showcase presentation will follow this clear 5-minute narrative:
1. **Overview (Dashboard):** Show enterprise-grade operational posture, total transaction volume, and risk distribution.
2. **Alert Prioritization:** Demonstrate how 99.70% alert volume reduction is achieved by focusing investigators on the Top 500 budget tier.
3. **Grounded Explainability:** Click an alert to inspect multi-signal provenance (`MODEL`, `BEHAVIORAL`, `GRAPH`), explaining *why* the transaction was flagged without generic hallucinations.
4. **Graph Intelligence & Typologies:** Explore detected mule funnels (fan-in) and layering chains across the transaction network.
5. **Investigative Dossiers:** Open a generated case file showing the chronological audit trail and legal triage disclaimer.
