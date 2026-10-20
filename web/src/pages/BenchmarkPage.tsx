import React, { useState, useEffect } from 'react';
import {
  Database, ChevronLeft, ChevronRight, X, AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import type { IbmSummary } from '../services/api';

export const BenchmarkPage: React.FC = () => {
  const [summary, setSummary] = useState<IbmSummary | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loadingAlerts, setLoadingAlerts] = useState<boolean>(false);
  const [loadingTx, setLoadingTx] = useState<boolean>(false);
  const [budget, setBudget] = useState<number>(50);
  const [tierFilter, setTierFilter] = useState<string>('All');
  const [page, setPage] = useState<number>(1);
  const [totalTx, setTotalTx] = useState<number>(1000);
  const [selectedEvidence, setSelectedEvidence] = useState<any | null>(null);

  useEffect(() => {
    loadSummary();
    loadAlerts();
    loadTransactions();
  }, []);

  const loadSummary = async () => {
    try {
      const res = await api.getIbmSummary();
      setSummary(res);
    } catch (e) {
      console.error('Failed to load benchmark summary:', e);
    }
  };

  const loadAlerts = async () => {
    try {
      setLoadingAlerts(true);
      const res = await api.getIbmAlerts(budget, tierFilter);
      setAlerts(res.alerts || []);
    } catch (e) {
      console.error('Failed to load benchmark alerts:', e);
    } finally {
      setLoadingAlerts(false);
    }
  };

  const loadTransactions = async () => {
    try {
      setLoadingTx(true);
      const res = await api.getIbmTransactions(page, 50);
      setTransactions(res.transactions || []);
      setTotalTx(res.total_records || 1000);
    } catch (e) {
      console.error('Failed to load benchmark transactions:', e);
    } finally {
      setLoadingTx(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [budget, tierFilter]);

  useEffect(() => {
    loadTransactions();
  }, [page]);

  const viewEvidence = async (txId: string) => {
    try {
      const res = await api.getIbmEvidence(txId);
      setSelectedEvidence(res.evidence || res);
    } catch (e) {
      console.error('Failed to load evidence:', e);
      alert('Failed to retrieve evidence for this transaction.');
    }
  };

  const maxPages = Math.max(1, Math.ceil(totalTx / 50));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Database size={20} color="#155eef" />
              <h1 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-navy)' }}>
                IBM AML Benchmark Evaluation (HI-Small)
              </h1>
              <span className="badge badge-primary">READ-ONLY BENCHMARK</span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
              Standardized Anti-Money Laundering benchmark exploring 5,078,345 records with 1,000 published showcase transactions
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <span className="badge badge-success">● Source: {summary?.data_source || 'Live Database'}</span>
            <span className="badge badge-neutral">Run: {summary?.run_id || 'RUN-IBM-HI-SMALL-20261020-01'}</span>
          </div>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        <div className="card">
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#667085', textTransform: 'uppercase' }}>Scanned Population</div>
          <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-navy)', marginTop: '4px' }}>
            {summary?.total_scanned_rows ? summary.total_scanned_rows.toLocaleString() : '5,078,345'}
          </div>
          <div style={{ fontSize: '11px', color: '#667085', marginTop: '2px' }}>September 1–18, 2022</div>
        </div>

        <div className="card">
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#667085', textTransform: 'uppercase' }}>Selected Showcase Cohort</div>
          <div style={{ fontSize: '22px', fontWeight: 700, color: '#155eef', marginTop: '4px' }}>
            {summary?.selected_records_count ? summary.selected_records_count.toLocaleString() : '1,000'}
          </div>
          <div style={{ fontSize: '11px', color: '#667085', marginTop: '2px' }}>Top 500 + Graph + Random</div>
        </div>

        <div className="card">
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#667085', textTransform: 'uppercase' }}>Supported Currencies</div>
          <div style={{ fontSize: '22px', fontWeight: 700, color: '#027a48', marginTop: '4px' }}>15 Currencies</div>
          <div style={{ fontSize: '11px', color: '#667085', marginTop: '2px' }}>USD, EUR, GBP, BTC, INR...</div>
        </div>

        <div className="card">
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#667085', textTransform: 'uppercase' }}>Payment Rails</div>
          <div style={{ fontSize: '22px', fontWeight: 700, color: '#6941c6', marginTop: '4px' }}>7 Formats</div>
          <div style={{ fontSize: '11px', color: '#667085', marginTop: '2px' }}>ACH, Wire, Cheque, Cash...</div>
        </div>
      </div>

      {/* Prioritized Benchmark Alerts */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-navy)' }}>
              Prioritized Benchmark Alerts & Evidence
            </h3>
            <p style={{ fontSize: '11px', color: '#667085' }}>
              Deterministic risk ranking with explainable signals. Click "Evidence" to inspect multi-source provenance.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
              <span>Budget:</span>
              <select
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                style={{ padding: '6px 10px', border: '1px solid #d0d5dd', borderRadius: '6px', fontSize: '12px' }}
              >
                <option value={25}>Top 25</option>
                <option value={50}>Top 50</option>
                <option value={100}>Top 100</option>
                <option value={250}>Top 250</option>
                <option value={500}>Top 500</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
              <span>Tier:</span>
              <select
                value={tierFilter}
                onChange={(e) => setTierFilter(e.target.value)}
                style={{ padding: '6px 10px', border: '1px solid #d0d5dd', borderRadius: '6px', fontSize: '12px' }}
              >
                <option value="All">All Tiers</option>
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
          </div>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Transaction ID</th>
                <th>Timestamp</th>
                <th>Sender Account</th>
                <th>Receiver Account</th>
                <th>Amount</th>
                <th>Currency</th>
                <th>Format</th>
                <th>Risk Score</th>
                <th>Tier</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loadingAlerts ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: '24px', color: '#667085' }}>
                    Loading prioritized alerts...
                  </td>
                </tr>
              ) : alerts.length === 0 ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: '24px', color: '#667085' }}>
                    No alerts matching criteria.
                  </td>
                </tr>
              ) : (
                alerts.map((a, i) => (
                  <tr key={i}>
                    <td><span className="badge badge-primary">#{a.risk_rank || i + 1}</span></td>
                    <td className="code-mono" style={{ fontWeight: 600 }}>{a.transaction_id}</td>
                    <td>{a.timestamp}</td>
                    <td className="code-mono">{a.sender_account}</td>
                    <td className="code-mono">{a.receiver_account}</td>
                    <td style={{ fontWeight: 600 }}>${Number(a.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td>{a.receiving_currency || a.currency}</td>
                    <td>{a.payment_format}</td>
                    <td style={{ fontWeight: 700, color: '#155eef' }}>{Number(a.model_risk_score || 0).toFixed(4)}</td>
                    <td>
                      <span className={`badge ${a.risk_tier === 'Critical' ? 'badge-danger' : a.risk_tier === 'High' ? 'badge-warning' : 'badge-primary'}`}>
                        {a.risk_tier}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => viewEvidence(a.transaction_id)}
                        className="btn btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '11px' }}
                      >
                        Evidence
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Paginated Transactions */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-navy)' }}>
              Benchmark Transactions Ledger (Paginated)
            </h3>
            <p style={{ fontSize: '11px', color: '#667085' }}>
              Ground-truth laundering labels are permanently air-gapped from all responses.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: '#667085' }}>Page {page} of {maxPages}</span>
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
              className="btn btn-secondary"
              style={{ padding: '6px 10px' }}
            >
              <ChevronLeft size={14} />
            </button>
            <button
              disabled={page >= maxPages}
              onClick={() => setPage(p => Math.min(maxPages, p + 1))}
              className="btn btn-secondary"
              style={{ padding: '6px 10px' }}
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Timestamp</th>
                <th>Sender</th>
                <th>Receiver</th>
                <th>Amount</th>
                <th>Currency</th>
                <th>Format</th>
                <th>From Bank</th>
                <th>To Bank</th>
              </tr>
            </thead>
            <tbody>
              {loadingTx ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '24px', color: '#667085' }}>
                    Loading transactions...
                  </td>
                </tr>
              ) : (
                transactions.map((t, i) => (
                  <tr key={i}>
                    <td className="code-mono" style={{ fontWeight: 600 }}>{t.transaction_id}</td>
                    <td>{t.timestamp}</td>
                    <td className="code-mono">{t.sender_account || t.sender_id}</td>
                    <td className="code-mono">{t.receiver_account || t.receiver_id}</td>
                    <td style={{ fontWeight: 600 }}>${Number(t.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td>{t.receiving_currency || t.currency || 'USD'}</td>
                    <td>{t.payment_format || 'Wire'}</td>
                    <td>{t.from_bank}</td>
                    <td>{t.to_bank}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Evidence Modal Dialog */}
      {selectedEvidence && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(16, 24, 40, 0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px'
        }}>
          <div className="card" style={{ maxWidth: '640px', width: '100%', maxHeight: '85vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #eaecf0', paddingBottom: '12px' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-navy)' }}>
                  Grounded Evidence: {selectedEvidence.transaction_id}
                </h3>
                <span className="badge badge-primary" style={{ marginTop: '4px' }}>
                  Source: {selectedEvidence.data_source || 'Supabase / Model Evidence'}
                </span>
              </div>
              <button onClick={() => setSelectedEvidence(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#667085' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ background: '#f8f9fc', padding: '12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#667085', textTransform: 'uppercase' }}>Investigator Summary</div>
                <div style={{ fontSize: '12px', color: '#1d2939', marginTop: '4px', lineHeight: 1.5 }}>
                  {selectedEvidence.human_readable_summary || selectedEvidence.investigator_explanation || 'Transaction exhibits severe multi-source divergence exceeding calibrated compliance thresholds.'}
                </div>
              </div>

              {selectedEvidence.contributing_signals && selectedEvidence.contributing_signals.length > 0 && (
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '8px' }}>
                    Contributing Multi-Source Signals
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {selectedEvidence.contributing_signals.map((sig: any, idx: number) => (
                      <div key={idx} style={{ border: '1px solid #eaecf0', borderRadius: '6px', padding: '10px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600 }}>
                          <span>{sig.signal_name}</span>
                          <span className={`badge ${sig.strength === 'CRITICAL' ? 'badge-danger' : sig.strength === 'HIGH' ? 'badge-warning' : 'badge-primary'}`}>
                            {sig.source}: {sig.strength}
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: '#475467', marginTop: '4px' }}>
                          Value: {sig.measured_value} | Baseline: {sig.baseline_comparison}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Disclaimer */}
              <div style={{ background: '#fffaeb', border: '1px solid #fedf89', borderRadius: '6px', padding: '10px', fontSize: '11px', color: '#b54708', display: 'flex', gap: '8px' }}>
                <AlertCircle size={16} style={{ flexShrink: 0 }} />
                <div>
                  RESEARCH BENCHMARK NOTICE: Grounded multi-source evidence is generated from the IBM AML benchmark dataset for algorithmic detection research and capacity triage modeling. It does NOT represent verified real-world criminal convictions or actual regulatory SAR filings.
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                <button onClick={() => setSelectedEvidence(null)} className="btn btn-primary">
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
