-- ==============================================================================
-- FinGuard AI — Migration 003: Fix Anomaly Score Constraint
-- ==============================================================================
-- Diagnostic Root Cause:
-- Isolation Forest anomaly scores (-decision_function) have a mathematical domain
-- of [-0.5, 0.5] (bounded within [-1.0, 1.0]). Negative values denote inliers/normal
-- transactions. Migration 002 mistakenly enforced `anomaly_score BETWEEN 0.0 AND 1.0`,
-- triggering PostgreSQL check constraint violation (Error 23514) on inlier transactions
-- such as IBM_TX_0208384 (anomaly_score = -0.0254).
--
-- Solution:
-- Drop the overly restrictive [0.0, 1.0] constraint and replace it with the
-- mathematically sound range [-1.0, 1.0].
-- ==============================================================================

ALTER TABLE ibm_benchmark_scores 
    DROP CONSTRAINT IF EXISTS chk_ibm_anomaly_score,
    DROP CONSTRAINT IF EXISTS ibm_benchmark_scores_anomaly_score_check;

ALTER TABLE ibm_benchmark_scores 
    ADD CONSTRAINT chk_ibm_anomaly_score 
    CHECK (anomaly_score IS NULL OR (anomaly_score BETWEEN -1.0 AND 1.0));
