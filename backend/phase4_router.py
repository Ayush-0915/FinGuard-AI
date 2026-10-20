"""
FinGuard AI — Phase 4 Intelligence API Router
Provides safe, read-only endpoints exposing Phase 3 Alert Prioritization,
Grounded Explanations, NetworkX Graph Typologies, and Investigator Cases.

Safety boundaries:
- 100% read-only: zero DB mutation or writes
- Zero modification to production models
- Resilient fallback to precomputed fixtures
"""

import os
import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

try:
    from backend.model_intelligence_service import get_model_intelligence_data
except ImportError:
    from model_intelligence_service import get_model_intelligence_data

router = APIRouter(prefix="/api/v2", tags=["Phase 4 Intelligence"])

# Determine artifacts base directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PHASE3_DIR = os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "phase3")
ARTIFACTS_DIR = os.path.join(PHASE3_DIR, "artifacts")
CASES_DIR = os.path.join(ARTIFACTS_DIR, "cases")
RESULTS_PATH = os.path.join(PHASE3_DIR, "phase3_results.json")
SAMPLE_ALERTS_PATH = os.path.join(ARTIFACTS_DIR, "sample_alerts.json")


def _load_json_file(file_path: str, default: Any = None) -> Any:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {file_path}: {e}")
    return default


def _get_all_alerts() -> List[Dict[str, Any]]:
    """Loads all precomputed alerts from sample_alerts.json or fallback."""
    alerts = _load_json_file(SAMPLE_ALERTS_PATH, [])
    if not alerts:
        # Fallback minimal alert fixture
        alerts = [
            {
                "transaction_id": "TX_4710695",
                "timestamp": "2022/09/09 18:00",
                "sender_account": "80034B960",
                "receiver_account": "80032DB60",
                "amount": 1205.34,
                "currency": "US Dollar",
                "payment_format": "ACH",
                "model_risk_score": 1.0,
                "risk_rank": 1,
                "risk_tier": "Critical",
                "contributing_signals": [
                    {
                        "signal_name": "Elevated Statistical Risk Score",
                        "source": "MODEL",
                        "strength": "CRITICAL",
                        "measured_value": 1.0,
                        "baseline_comparison": "Base population threshold >= 0.95"
                    },
                    {
                        "signal_name": "High Counterparty Fan-Out",
                        "source": "BEHAVIORAL",
                        "strength": "HIGH",
                        "measured_value": "7 unique receivers",
                        "baseline_comparison": "Typical sender < 3 receivers"
                    },
                    {
                        "signal_name": "Graph Pattern: Fan-In Aggregation (Mule Funnel)",
                        "source": "GRAPH",
                        "strength": "CRITICAL",
                        "measured_value": "Severity 1.0",
                        "baseline_comparison": "Acyclic benign flow"
                    }
                ],
                "graph_patterns": [
                    {
                        "typology": "FAN_IN",
                        "typology_name": "Fan-In Aggregation (Mule Funnel)",
                        "severity": 1.0,
                        "explanation": "Account 80032DB60 received funds from 60 distinct sender accounts."
                    }
                ],
                "human_readable_summary": "Alert for transaction TX_4710695: Account 80034B960 transferred $1,205.34 US Dollar to 80032DB60.",
                "provenance_breakdown": {
                    "model_signals_count": 1,
                    "behavioral_signals_count": 1,
                    "graph_signals_count": 1,
                    "rule_signals_count": 0
                }
            }
        ]
    return alerts


def _get_all_cases() -> List[Dict[str, Any]]:
    """Loads all structured case files from the cases directory."""
    cases = []
    if os.path.exists(CASES_DIR):
        for fname in sorted(os.listdir(CASES_DIR)):
            if fname.endswith(".json"):
                fpath = os.path.join(CASES_DIR, fname)
                case_data = _load_json_file(fpath)
                if case_data:
                    cases.append(case_data)
    if not cases:
        # Fallback case fixture
        cases = [
            {
                "case_id": "CASE-80032DB6-20220909",
                "review_status": "Open",
                "priority_tier": "Critical",
                "best_alert_rank": 1,
                "peak_risk_score": 1.0,
                "primary_account": "80032DB60",
                "total_suspicious_volume": 7769.72,
                "alert_count": 3,
                "connected_accounts_count": 3,
                "related_accounts": ["80034B7D0", "80034B960", "800392850"],
                "relevant_transaction_ids": ["TX_4710695", "TX_4710717", "TX_4710746"],
                "detected_graph_patterns": [
                    {
                        "typology": "Fan-In Aggregation (Mule Funnel)",
                        "severity": 0.7,
                        "confidence": "MEDIUM",
                        "explanation": None
                    }
                ],
                "activity_timeline": [
                    {
                        "step": 1,
                        "timestamp": "2022/09/09 18:00",
                        "transaction_id": "TX_4710695",
                        "sender": "80034B960",
                        "receiver": "80032DB60",
                        "amount": 1205.34,
                        "currency": "US Dollar",
                        "score": 1.0,
                        "summary": "Transfer into primary mule funnel."
                    }
                ],
                "investigation_summary": "Case CASE-80032DB6-20220909 opened for primary entity 80032DB60.",
                "compliance_disclaimer": "NOTICE: This case file represents an automated investigatory lead generated by FinGuard AI based on statistical anomaly detection and graph topology signals. It is designed to assist compliance analysts and does not constitute a confirmed financial crime, legal determination, or proof of illicit activity."
            }
        ]
    return cases


# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

@router.get("/alerts/prioritized")
def get_prioritized_alerts(
    budget: int = Query(500, description="Investigation capacity budget (100 to 5000)"),
    tier: str = Query("All", description="Risk tier filter: All, Critical, High, Medium, Low")
):
    """
    Returns prioritized alerts under the specified operational budget (K)
    and risk tier filter, with both statistical model probability and fused signals.
    """
    all_alerts = _get_all_alerts()

    # Apply risk tier filter
    if tier and tier.lower() != "all":
        filtered = [a for a in all_alerts if str(a.get("risk_tier", "")).lower() == tier.lower()]
    else:
        filtered = all_alerts

    # Apply capacity budget truncation
    budget_capped = filtered[:budget]

    # Calculate operational metrics
    tier_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for a in all_alerts:
        t = a.get("risk_tier", "Low")
        if t in tier_counts:
            tier_counts[t] += 1

    return {
        "status": "success",
        "budget_limit": budget,
        "tier_filter": tier,
        "total_available": len(all_alerts),
        "returned_count": len(budget_capped),
        "tier_distribution": tier_counts,
        "alerts": budget_capped
    }


@router.get("/alerts/{transaction_id}/explanation")
def get_alert_explanation(transaction_id: str):
    """
    Returns evidence-grounded multi-signal explanation for a specific transaction
    with explicit signal provenance (MODEL, BEHAVIORAL, GRAPH, RULE).
    """
    all_alerts = _get_all_alerts()
    for a in all_alerts:
        if a.get("transaction_id") == transaction_id:
            return {
                "status": "success",
                "transaction_id": transaction_id,
                "explanation": a
            }

    # If not found directly, check cases activity timeline
    all_cases = _get_all_cases()
    for c in all_cases:
        for step in c.get("activity_timeline", []):
            if step.get("transaction_id") == transaction_id:
                return {
                    "status": "success",
                    "transaction_id": transaction_id,
                    "explanation": {
                        "transaction_id": transaction_id,
                        "timestamp": step.get("timestamp"),
                        "sender_account": step.get("sender"),
                        "receiver_account": step.get("receiver"),
                        "amount": step.get("amount"),
                        "currency": step.get("currency"),
                        "model_risk_score": step.get("score", 1.0),
                        "risk_tier": c.get("priority_tier", "Critical"),
                        "human_readable_summary": step.get("summary", ""),
                        "contributing_signals": [
                            {
                                "signal_name": "Case Intelligence Lead",
                                "source": "MODEL",
                                "strength": "CRITICAL",
                                "measured_value": step.get("score", 1.0),
                                "baseline_comparison": "Prioritized entity transaction"
                            }
                        ],
                        "graph_patterns": c.get("detected_graph_patterns", [])
                    }
                }

    raise HTTPException(status_code=404, detail=f"Alert with Transaction ID '{transaction_id}' not found.")


@router.get("/graph/typologies")
def get_graph_typologies():
    """
    Returns detected financial crime graph typologies:
    - Fan-In Aggregation (Mule Funnel)
    - Fan-Out Disbursement
    - Rapid Movement / Structuring
    - High-Value Anomalies
    """
    results_data = _load_json_file(RESULTS_PATH, {})
    graph_data = results_data.get("graph_intelligence", {})

    summary = graph_data.get("graph_summary", {
        "nodes_count": 5679,
        "edges_count": 5000,
        "total_patterns_detected": 161,
        "pattern_breakdown": {
            "fan_in": 43,
            "fan_out": 15,
            "circular_flow": 0,
            "rapid_movement": 12,
            "high_value_anomalies": 90,
            "concentration": 1
        }
    })

    patterns = graph_data.get("sample_patterns", [])
    if not patterns:
        patterns = [
            {
                "typology": "FAN_IN",
                "typology_name": "Fan-In Aggregation (Mule Funnel)",
                "target_account": "80032DB60",
                "involved_accounts_count": 61,
                "involved_transactions_count": 60,
                "total_amount_received": 161293.24,
                "severity_score": 1.0,
                "confidence_level": "HIGH",
                "investigator_explanation": "Account 80032DB60 received funds from 60 distinct senders totaling $161,293.24."
            }
        ]

    return {
        "status": "success",
        "graph_summary": summary,
        "sample_patterns": patterns
    }


@router.get("/cases")
def get_cases(
    status: Optional[str] = Query("All", description="Filter by review status: All, Open, Under Review, Closed"),
    tier: Optional[str] = Query("All", description="Filter by priority tier: All, Critical, High, Medium, Low")
):
    """
    Returns all structured investigator case dossiers.
    """
    cases = _get_all_cases()

    if status and status.lower() != "all":
        cases = [c for c in cases if str(c.get("review_status", "")).lower() == status.lower()]
    if tier and tier.lower() != "all":
        cases = [c for c in cases if str(c.get("priority_tier", "")).lower() == tier.lower()]

    return {
        "status": "success",
        "total_cases": len(cases),
        "cases": cases
    }


@router.get("/cases/{case_id}")
def get_case_detail(case_id: str):
    """
    Returns full investigative case dossier for a specific case ID,
    including timeline, connected accounts, and compliance disclaimer.
    """
    cases = _get_all_cases()
    for c in cases:
        if c.get("case_id") == case_id:
            return {
                "status": "success",
                "case": c
            }

    raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")


@router.get("/model/intelligence")
def get_model_intelligence():
    """
    Returns verified model intelligence metadata, architecture specs,
    offline performance benchmarks, 26-feature importance ranking,
    risk fusion formulas, and alert-budget capacity tradeoffs.
    """
    try:
        data = get_model_intelligence_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate model intelligence: {e}")
