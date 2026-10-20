-- ==============================================================================
-- FinGuard AI — Migration 002: IBM AML Benchmark Hybrid Tables (Hardened)
-- ==============================================================================
-- Safety Guarantees:
-- 1. ZERO alterations or drops to existing accounts, transactions, alerts,
--    predictions, or investigations tables.
-- 2. Fully isolated schema dedicated to offline benchmark datasets.
-- 3. Strict numeric domain constraints and uniqueness enforcement.
-- 4. Idempotent DDL and Row-Level Security (RLS) policies.
-- ==============================================================================

-- 1. IBM Dataset Runs Metadata Table
CREATE TABLE IF NOT EXISTS ibm_dataset_runs (
    run_id TEXT PRIMARY KEY,
    source_dataset TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    total_scanned_rows BIGINT NOT NULL,
    selected_records_count INTEGER NOT NULL,
    model_version TEXT NOT NULL,
    pipeline_version TEXT NOT NULL,
    selection_policy TEXT NOT NULL,
    export_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. IBM Benchmark Transactions Table (Isolated from accounts FK)
CREATE TABLE IF NOT EXISTS ibm_benchmark_transactions (
    transaction_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES ibm_dataset_runs(run_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    sender_account TEXT NOT NULL,
    receiver_account TEXT NOT NULL,
    amount DOUBLE PRECISION NOT NULL CONSTRAINT chk_ibm_tx_amount CHECK (amount >= 0.0),
    receiving_currency TEXT NOT NULL,
    payment_currency TEXT NOT NULL,
    payment_format TEXT NOT NULL,
    from_bank INTEGER NOT NULL,
    to_bank INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. IBM Benchmark Model Scoring & Prioritization Table
CREATE TABLE IF NOT EXISTS ibm_benchmark_scores (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES ibm_dataset_runs(run_id) ON DELETE CASCADE,
    transaction_id TEXT NOT NULL REFERENCES ibm_benchmark_transactions(transaction_id) ON DELETE CASCADE,
    model_risk_score DOUBLE PRECISION NOT NULL CONSTRAINT chk_ibm_score_range CHECK (model_risk_score BETWEEN 0.0 AND 1.0),
    risk_rank INTEGER NOT NULL CONSTRAINT chk_ibm_risk_rank CHECK (risk_rank >= 1),
    risk_tier TEXT NOT NULL CONSTRAINT chk_ibm_risk_tier CHECK (risk_tier IN ('Critical', 'High', 'Medium', 'Low')),
    fused_score DOUBLE PRECISION CONSTRAINT chk_ibm_fused_score CHECK (fused_score IS NULL OR (fused_score BETWEEN 0.0 AND 1.0)),
    anomaly_score DOUBLE PRECISION CONSTRAINT chk_ibm_anomaly_score CHECK (anomaly_score IS NULL OR (anomaly_score BETWEEN 0.0 AND 1.0)),
    model_version TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_ibm_scores_run_tx UNIQUE (run_id, transaction_id)
);

-- 4. IBM Benchmark Grounded Explainability & Evidence Table
CREATE TABLE IF NOT EXISTS ibm_benchmark_evidence (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES ibm_dataset_runs(run_id) ON DELETE CASCADE,
    transaction_id TEXT NOT NULL REFERENCES ibm_benchmark_transactions(transaction_id) ON DELETE CASCADE,
    human_readable_summary TEXT NOT NULL,
    contributing_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    graph_patterns JSONB NOT NULL DEFAULT '[]'::jsonb,
    provenance_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_ibm_evidence_run_tx UNIQUE (run_id, transaction_id)
);

-- 5. High-Performance B-Tree Indexes
CREATE INDEX IF NOT EXISTS idx_ibm_tx_run_id ON ibm_benchmark_transactions(run_id);
CREATE INDEX IF NOT EXISTS idx_ibm_tx_sender ON ibm_benchmark_transactions(sender_account);
CREATE INDEX IF NOT EXISTS idx_ibm_tx_receiver ON ibm_benchmark_transactions(receiver_account);
CREATE INDEX IF NOT EXISTS idx_ibm_tx_timestamp ON ibm_benchmark_transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_ibm_scores_rank ON ibm_benchmark_scores(run_id, risk_rank);
CREATE INDEX IF NOT EXISTS idx_ibm_scores_tier ON ibm_benchmark_scores(risk_tier);
CREATE INDEX IF NOT EXISTS idx_ibm_evidence_tx ON ibm_benchmark_evidence(transaction_id);

-- 6. Row-Level Security (RLS) Activation
ALTER TABLE ibm_dataset_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ibm_benchmark_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ibm_benchmark_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE ibm_benchmark_evidence ENABLE ROW LEVEL SECURITY;

-- 7. Public Read-Only Access Policies
DROP POLICY IF EXISTS "Allow public read access on ibm_dataset_runs" ON ibm_dataset_runs;
CREATE POLICY "Allow public read access on ibm_dataset_runs" 
    ON ibm_dataset_runs FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "Allow public read access on ibm_benchmark_transactions" ON ibm_benchmark_transactions;
CREATE POLICY "Allow public read access on ibm_benchmark_transactions" 
    ON ibm_benchmark_transactions FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "Allow public read access on ibm_benchmark_scores" ON ibm_benchmark_scores;
CREATE POLICY "Allow public read access on ibm_benchmark_scores" 
    ON ibm_benchmark_scores FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "Allow public read access on ibm_benchmark_evidence" ON ibm_benchmark_evidence;
CREATE POLICY "Allow public read access on ibm_benchmark_evidence" 
    ON ibm_benchmark_evidence FOR SELECT TO anon, authenticated USING (true);

-- 8. Service-Role Write Policies
DROP POLICY IF EXISTS "Allow service_role full write on ibm_dataset_runs" ON ibm_dataset_runs;
CREATE POLICY "Allow service_role full write on ibm_dataset_runs" 
    ON ibm_dataset_runs FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service_role full write on ibm_benchmark_transactions" ON ibm_benchmark_transactions;
CREATE POLICY "Allow service_role full write on ibm_benchmark_transactions" 
    ON ibm_benchmark_transactions FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service_role full write on ibm_benchmark_scores" ON ibm_benchmark_scores;
CREATE POLICY "Allow service_role full write on ibm_benchmark_scores" 
    ON ibm_benchmark_scores FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service_role full write on ibm_benchmark_evidence" ON ibm_benchmark_evidence;
CREATE POLICY "Allow service_role full write on ibm_benchmark_evidence" 
    ON ibm_benchmark_evidence FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 9. Explicit Schema Grants
GRANT SELECT ON ibm_dataset_runs TO anon, authenticated;
GRANT SELECT ON ibm_benchmark_transactions TO anon, authenticated;
GRANT SELECT ON ibm_benchmark_scores TO anon, authenticated;
GRANT SELECT ON ibm_benchmark_evidence TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
