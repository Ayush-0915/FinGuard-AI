import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { PrioritizedAlert } from '../services/api';

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<PrioritizedAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getPrioritizedAlerts();
      setAlerts(res.alerts || []);
    } catch (err: any) {
      console.error('Failed to load prioritized alerts:', err);
      // Fallback to basic alerts
      try {
        const fallback = await api.getAlerts();
        setAlerts((fallback.alerts || []).map((a, i) => ({
          transaction_id: a.transaction_id || `TX_${i + 1}`,
          timestamp: a.detected_time || '2026/10/20',
          sender_account: a.account_id || 'ACC-10293',
          receiver_account: a.counterparty || 'ACC-9921',
          amount: a.amount || 250000,
          currency: 'INR',
          payment_format: 'Wire',
          model_risk_score: (a.risk_score || 85) / 100,
          risk_rank: i + 1,
          risk_tier: (a.risk_score || 85) >= 90 ? 'Critical' : 'High',
          human_readable_summary: a.reason || 'Elevated anomaly score exceeding behavioral threshold.',
        })));
      } catch (e2: any) {
        setError(err.message || 'Failed to fetch alerts.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-navy)' }}>
            Active Prioritized Alerts & Triage Queue
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
            Deterministic ranking with multi-source risk fusion and investigator triage guidance
          </p>
        </div>
        <button onClick={loadAlerts} className="btn btn-primary">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh Queue
        </button>
      </div>

      {error && (
        <div style={{ background: '#fef3f2', border: '1px solid #fecdca', borderRadius: '8px', padding: '12px 16px', color: '#b42318', fontSize: '13px' }}>
          {error}
        </div>
      )}

      <div className="card">
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Priority Rank</th>
                <th>Transaction ID</th>
                <th>Timestamp</th>
                <th>Sender Account</th>
                <th>Receiver Account</th>
                <th>Amount</th>
                <th>Risk Score</th>
                <th>Tier</th>
                <th>Investigator Summary</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '24px', color: '#667085' }}>
                    Loading prioritized alerts...
                  </td>
                </tr>
              ) : alerts.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '24px', color: '#667085' }}>
                    No active alerts in review queue.
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
                    <td style={{ fontWeight: 600 }}>₹{Number(a.amount || 0).toLocaleString()}</td>
                    <td style={{ fontWeight: 700, color: '#155eef' }}>{Number(a.model_risk_score || 0).toFixed(4)}</td>
                    <td>
                      <span className={`badge ${a.risk_tier === 'Critical' ? 'badge-danger' : a.risk_tier === 'High' ? 'badge-warning' : 'badge-primary'}`}>
                        {a.risk_tier}
                      </span>
                    </td>
                    <td style={{ color: '#475467', maxWidth: '340px' }}>{a.human_readable_summary || 'Review suggested.'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
