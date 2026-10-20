"""
FinGuard AI — IBM AML Benchmark API Router
Provides safe, read-only endpoints exposing IBM AML Benchmark data
from Supabase benchmark tables with resilient local fixture fallback.

Safety & Governance Boundaries:
- 100% Read-Only: Zero database writes or schema modifications.
- Strict Label Isolation: Ground-truth laundering labels are NEVER exposed.
- Non-Existent Table Handling: Gracefully falls back to local fixtures if migration is pending.
- Explicit Provenance & Disclaimers: Distinguishes Supabase live data from local fixtures.
"""

import os
import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v2/ibm", tags=["IBM AML Benchmark"])

BENCHMARK_DISCLAIMER = (
    "This data originates from the IBM Transactions for Anti-Money Laundering (AML) benchmark dataset "
    "for AI/ML algorithm evaluation and capacity triage research. It does NOT represent verified real-world "
    "criminal activity or actual regulatory Suspicious Activity Report (SAR) filings."
)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARTIFACTS_DIR = os.path.join(ROOT_DIR, "evaluation", "amlsim_evaluation", "ibm_export", "artifacts")

FIXTURE_RUNS_PATH = os.path.join(ARTIFACTS_DIR, "ibm_dataset_runs.json")
FIXTURE_TRANSACTIONS_PATH = os.path.join(ARTIFACTS_DIR, "ibm_benchmark_transactions.json")
FIXTURE_SCORES_PATH = os.path.join(ARTIFACTS_DIR, "ibm_benchmark_scores.json")
FIXTURE_EVIDENCE_PATH = os.path.join(ARTIFACTS_DIR, "ibm_benchmark_evidence.json")

# In-memory cache for local fixtures
_FIXTURE_CACHE: Dict[str, Any] = {}

# Supabase Client Attempt
_supabase_client = None
try:
    try:
        from database import client as db_client
    except ImportError:
        from backend.database import client as db_client
    _supabase_client = db_client
except Exception as e:
    _supabase_client = None


def _load_fixture(file_path: str, default: Any = None) -> Any:
    """Loads and caches local JSON fixture safely."""
    if file_path in _FIXTURE_CACHE:
        return _FIXTURE_CACHE[file_path]
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _FIXTURE_CACHE[file_path] = data
                return data
        except Exception as err:
            print(f"Warning: Failed to parse fixture {os.path.basename(file_path)}: {err}")
    return default


def _sanitize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Removes any target label or sensitive keys to guarantee strict isolation."""
    forbidden = {"is_laundering", "islaundering", "target", "label", "sar", "ground_truth"}
    return {k: v for k, v in record.items() if k.lower() not in forbidden}


# ------------------------------------------------------------------------------
# Pydantic Response Models
# ------------------------------------------------------------------------------

class BenchmarkRunItem(BaseModel):
    run_id: str
    source_dataset: str
    source_sha256: str
    total_scanned_rows: int
    selected_records_count: int
    model_version: str
    pipeline_version: str
    selection_policy: str
    export_metadata: Optional[Dict[str, Any]] = None


class BenchmarkRunsResponse(BaseModel):
    status: str
    data_source: str
    disclaimer: str
    runs_count: int
    runs: List[BenchmarkRunItem]


class BenchmarkSummaryResponse(BaseModel):
    status: str
    data_source: str
    disclaimer: str
    run_id: str
    source_dataset: str
    source_sha256: str
    total_scanned_rows: int
    selected_records_count: int
    model_version: str
    pipeline_version: str
    selection_policy: str
    tier_distribution: Dict[str, int]
    timestamp_range: Dict[str, str]


class BenchmarkTransactionItem(BaseModel):
    transaction_id: str
    run_id: str
    timestamp: str
    sender_account: str
    receiver_account: str
    amount: float
    receiving_currency: str
    payment_currency: str
    payment_format: str
    from_bank: int
    to_bank: int


class BenchmarkTransactionsResponse(BaseModel):
    status: str
    data_source: str
    disclaimer: str
    page: int
    limit: int
    total_records: int
    returned_count: int
    transactions: List[BenchmarkTransactionItem]


class BenchmarkAlertItem(BaseModel):
    transaction_id: str
    run_id: str
    timestamp: str
    sender_account: str
    receiver_account: str
    amount: float
    receiving_currency: str
    payment_format: str
    model_risk_score: float
    risk_rank: int
    risk_tier: str
    fused_score: float
    anomaly_score: float
    model_version: str


class BenchmarkAlertsResponse(BaseModel):
    status: str
    data_source: str
    disclaimer: str
    budget: int
    tier_filter: str
    total_available: int
    returned_count: int
    alerts: List[BenchmarkAlertItem]


class BenchmarkEvidenceResponse(BaseModel):
    status: str
    data_source: str
    disclaimer: str
    transaction_id: str
    run_id: str
    human_readable_summary: str
    contributing_signals: List[Dict[str, Any]]
    graph_patterns: List[Dict[str, Any]]
    provenance_breakdown: Dict[str, Any]


# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------

@router.get("/runs", response_model=BenchmarkRunsResponse)
def get_benchmark_runs():
    """
    Returns available IBM AML benchmark import runs with execution metadata and cryptographic hashes.
    Safe read-only query against Supabase `ibm_dataset_runs` with local fixture fallback.
    """
    runs_data = []
    data_source = "supabase_database"

    if _supabase_client:
        try:
            res = _supabase_client.table("ibm_dataset_runs").select("*").execute()
            if res.data:
                runs_data = res.data
        except Exception:
            data_source = "local_fixture_fallback"
    else:
        data_source = "local_fixture_fallback"

    if not runs_data:
        data_source = "local_fixture_fallback"
        fixture = _load_fixture(FIXTURE_RUNS_PATH, {})
        if fixture:
            runs_data = [fixture] if isinstance(fixture, dict) else fixture

    sanitized_runs = [_sanitize_record(r) for r in runs_data]

    return {
        "status": "success",
        "data_source": data_source,
        "disclaimer": BENCHMARK_DISCLAIMER,
        "runs_count": len(sanitized_runs),
        "runs": sanitized_runs
    }


@router.get("/summary", response_model=BenchmarkSummaryResponse)
def get_benchmark_summary(
    run_id: Optional[str] = Query(None, description="Benchmark run identifier")
):
    """
    Returns high-level summary metrics: total scanned rows (5.078M), selected cohort (1,000),
    tier distribution, and source dataset provenance.
    """
    runs_resp = get_benchmark_runs()
    runs = runs_resp["runs"]
    if not runs:
        raise HTTPException(status_code=404, detail="No benchmark runs available.")

    selected_run = runs[0]
    if run_id:
        matched = [r for r in runs if r.get("run_id") == run_id]
        if not matched:
            raise HTTPException(status_code=404, detail=f"Benchmark Run '{run_id}' not found.")
        selected_run = matched[0]

    # Compute tier distribution from scores
    scores = _load_fixture(FIXTURE_SCORES_PATH, [])
    tier_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for sc in scores:
        t = sc.get("risk_tier", "Low")
        if t in tier_counts:
            tier_counts[t] += 1

    # Extract timestamps from transactions fixture
    txs = _load_fixture(FIXTURE_TRANSACTIONS_PATH, [])
    ts_min = txs[0].get("timestamp", "2022/09/01 00:00") if txs else "2022/09/01 00:00"
    ts_max = txs[-1].get("timestamp", "2022/09/11 09:24") if txs else "2022/09/11 09:24"

    return {
        "status": "success",
        "data_source": runs_resp["data_source"],
        "disclaimer": BENCHMARK_DISCLAIMER,
        "run_id": selected_run["run_id"],
        "source_dataset": selected_run["source_dataset"],
        "source_sha256": selected_run["source_sha256"],
        "total_scanned_rows": selected_run["total_scanned_rows"],
        "selected_records_count": selected_run["selected_records_count"],
        "model_version": selected_run["model_version"],
        "pipeline_version": selected_run["pipeline_version"],
        "selection_policy": selected_run["selection_policy"],
        "tier_distribution": tier_counts,
        "timestamp_range": {"min": ts_min, "max": ts_max}
    }


@router.get("/transactions", response_model=BenchmarkTransactionsResponse)
def get_benchmark_transactions(
    run_id: Optional[str] = Query(None, description="Benchmark run identifier"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    account_id: Optional[str] = Query(None, description="Filter by sender or receiver account"),
    currency: Optional[str] = Query(None, description="Filter by receiving or payment currency"),
    payment_format: Optional[str] = Query(None, description="Filter by payment format (ACH, Wire, etc.)")
):
    """
    Returns paginated benchmark transactions. Bounded to max 100 records per page.
    Queries Supabase `ibm_benchmark_transactions` with resilient local fixture fallback.
    STRICTLY EXCLUDES TARGET LABELS.
    """
    data_source = "supabase_database"
    transactions = []
    total_count = 0

    if _supabase_client:
        try:
            offset = (page - 1) * limit
            query = _supabase_client.table("ibm_benchmark_transactions").select("*", count="exact")
            if run_id:
                query = query.eq("run_id", run_id)
            if account_id:
                query = query.or_(f"sender_account.eq.{account_id},receiver_account.eq.{account_id}")
            if currency:
                query = query.or_(f"receiving_currency.eq.{currency},payment_currency.eq.{currency}")
            if payment_format:
                query = query.eq("payment_format", payment_format)

            res = query.order("timestamp", desc=False).range(offset, offset + limit - 1).execute()
            if res.data:
                transactions = res.data
                total_count = res.count or len(transactions)
        except Exception:
            data_source = "local_fixture_fallback"
    else:
        data_source = "local_fixture_fallback"

    # Fallback to local fixture if Supabase has not been migrated or returned empty
    if not transactions and data_source == "local_fixture_fallback":
        all_txs = _load_fixture(FIXTURE_TRANSACTIONS_PATH, [])
        filtered = all_txs

        if run_id:
            filtered = [t for t in filtered if t.get("run_id") == run_id]
        if account_id:
            filtered = [
                t for t in filtered 
                if t.get("sender_account") == account_id or t.get("receiver_account") == account_id
            ]
        if currency:
            c_low = currency.lower()
            filtered = [
                t for t in filtered
                if t.get("receiving_currency", "").lower() == c_low or t.get("payment_currency", "").lower() == c_low
            ]
        if payment_format:
            pf_low = payment_format.lower()
            filtered = [t for t in filtered if t.get("payment_format", "").lower() == pf_low]

        total_count = len(filtered)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        transactions = filtered[start_idx:end_idx]

    sanitized = [_sanitize_record(t) for t in transactions]

    return {
        "status": "success",
        "data_source": data_source,
        "disclaimer": BENCHMARK_DISCLAIMER,
        "page": page,
        "limit": limit,
        "total_records": total_count,
        "returned_count": len(sanitized),
        "transactions": sanitized
    }


@router.get("/alerts", response_model=BenchmarkAlertsResponse)
def get_benchmark_alerts(
    run_id: Optional[str] = Query(None, description="Benchmark run identifier"),
    budget: int = Query(50, ge=1, le=500, description="Investigation capacity budget (1 to 500)"),
    tier: str = Query("All", description="Risk tier filter: All, Critical, High, Medium, Low")
):
    """
    Returns prioritized benchmark alerts ranked deterministically by risk score.
    Combines transaction metadata with model scores. Bounded by capacity budget.
    """
    data_source = "supabase_database"
    alerts = []
    total_available = 0

    if _supabase_client:
        try:
            query = _supabase_client.table("ibm_benchmark_scores").select(
                "*, ibm_benchmark_transactions(timestamp, sender_account, receiver_account, amount, receiving_currency, payment_format)"
            )
            if run_id:
                query = query.eq("run_id", run_id)
            if tier and tier.lower() != "all":
                query = query.eq("risk_tier", tier.capitalize())

            res = query.order("risk_rank", desc=False).limit(budget).execute()
            if res.data:
                for row in res.data:
                    tx_info = row.get("ibm_benchmark_transactions") or {}
                    alerts.append({
                        "transaction_id": row.get("transaction_id"),
                        "run_id": row.get("run_id"),
                        "timestamp": tx_info.get("timestamp", ""),
                        "sender_account": tx_info.get("sender_account", ""),
                        "receiver_account": tx_info.get("receiver_account", ""),
                        "amount": tx_info.get("amount", 0.0),
                        "receiving_currency": tx_info.get("receiving_currency", "US Dollar"),
                        "payment_format": tx_info.get("payment_format", "ACH"),
                        "model_risk_score": row.get("model_risk_score", 0.0),
                        "risk_rank": row.get("risk_rank", 1),
                        "risk_tier": row.get("risk_tier", "Low"),
                        "fused_score": row.get("fused_score", row.get("model_risk_score", 0.0)),
                        "anomaly_score": row.get("anomaly_score", 0.0),
                        "model_version": row.get("model_version", "LightGBM-4.5.0-muleguard")
                    })
                total_available = len(alerts)
        except Exception:
            data_source = "local_fixture_fallback"
    else:
        data_source = "local_fixture_fallback"

    # Fallback to local fixtures if database returned empty or offline
    if not alerts:
        data_source = "local_fixture_fallback"
        txs = {t["transaction_id"]: t for t in _load_fixture(FIXTURE_TRANSACTIONS_PATH, [])}
        scores = _load_fixture(FIXTURE_SCORES_PATH, [])

        filtered_scores = scores
        if run_id:
            filtered_scores = [s for s in filtered_scores if s.get("run_id") == run_id]
        if tier and tier.lower() != "all":
            filtered_scores = [s for s in filtered_scores if s.get("risk_tier", "").lower() == tier.lower()]

        total_available = len(filtered_scores)
        capped_scores = filtered_scores[:budget]

        for s in capped_scores:
            tx_id = s.get("transaction_id")
            tx_info = txs.get(tx_id, {})
            alerts.append({
                "transaction_id": tx_id,
                "run_id": s.get("run_id", "RUN-IBM-HI-SMALL-20261020-01"),
                "timestamp": tx_info.get("timestamp", ""),
                "sender_account": tx_info.get("sender_account", ""),
                "receiver_account": tx_info.get("receiver_account", ""),
                "amount": tx_info.get("amount", 0.0),
                "receiving_currency": tx_info.get("receiving_currency", "US Dollar"),
                "payment_format": tx_info.get("payment_format", "ACH"),
                "model_risk_score": s.get("model_risk_score", 0.0),
                "risk_rank": s.get("risk_rank", 1),
                "risk_tier": s.get("risk_tier", "Low"),
                "fused_score": s.get("fused_score", s.get("model_risk_score", 0.0)),
                "anomaly_score": s.get("anomaly_score", 0.0),
                "model_version": s.get("model_version", "LightGBM-4.5.0-muleguard")
            })

    sanitized = [_sanitize_record(a) for a in alerts]

    return {
        "status": "success",
        "data_source": data_source,
        "disclaimer": BENCHMARK_DISCLAIMER,
        "budget": budget,
        "tier_filter": tier,
        "total_available": total_available,
        "returned_count": len(sanitized),
        "alerts": sanitized
    }


@router.get("/transactions/{transaction_id}/evidence", response_model=BenchmarkEvidenceResponse)
def get_benchmark_evidence(
    transaction_id: str = Path(..., description="Benchmark transaction identifier (e.g., IBM_TX_0040621)")
):
    """
    Returns grounded multi-source explainability evidence for a specific benchmark transaction.
    Includes statistical model probability, behavioral velocity, and graph pattern signals.
    """
    data_source = "supabase_database"
    evidence_record = None

    if _supabase_client:
        try:
            res = _supabase_client.table("ibm_benchmark_evidence").select("*").eq("transaction_id", transaction_id).execute()
            if res.data:
                evidence_record = res.data[0]
        except Exception:
            data_source = "local_fixture_fallback"
    else:
        data_source = "local_fixture_fallback"

    if not evidence_record:
        data_source = "local_fixture_fallback"
        all_ev = _load_fixture(FIXTURE_EVIDENCE_PATH, [])
        for ev in all_ev:
            if ev.get("transaction_id") == transaction_id:
                evidence_record = ev
                break

    if not evidence_record:
        raise HTTPException(
            status_code=404,
            detail=f"Benchmark evidence for Transaction ID '{transaction_id}' not found."
        )

    sanitized = _sanitize_record(evidence_record)

    return {
        "status": "success",
        "data_source": data_source,
        "disclaimer": BENCHMARK_DISCLAIMER,
        "transaction_id": sanitized.get("transaction_id", transaction_id),
        "run_id": sanitized.get("run_id", "RUN-IBM-HI-SMALL-20261020-01"),
        "human_readable_summary": sanitized.get("human_readable_summary", ""),
        "contributing_signals": sanitized.get("contributing_signals", []),
        "graph_patterns": sanitized.get("graph_patterns", []),
        "provenance_breakdown": sanitized.get("provenance_breakdown", {})
    }
