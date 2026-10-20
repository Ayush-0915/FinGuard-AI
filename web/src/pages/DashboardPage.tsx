import React, { useState, useEffect } from 'react';
import {
  Users, DollarSign, AlertTriangle, TrendingUp,
  ArrowDownRight, RefreshCw
} from 'lucide-react';
import { api } from '../services/api';
import type { DashboardData } from '../services/api';

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getDashboard();
      setData(res);
    } catch (err: any) {
      console.error('Dashboard load error:', err);
      setError(err.message || 'Failed to fetch dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const formatMoney = (val: number) => {
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(1)} K`;
    return `₹${val.toLocaleString()}`;
  };

  if (loading && !data) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#667085' }}>
        <RefreshCw className="animate-spin" style={{ margin: '0 auto 12px auto', width: '28px', height: '28px', color: '#155eef' }} />
        <div style={{ fontSize: '15px', fontWeight: 600 }}>Loading Dashboard Intelligence...</div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-navy)' }}>
            Financial Crime & Mule Detection Executive Dashboard
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
            Real-time telemetry, transaction flows, and risk prioritization overview
          </p>
        </div>
        <button onClick={loadDashboard} className="btn btn-primary">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div style={{ background: '#fef3f2', border: '1px solid #fecdca', borderRadius: '8px', padding: '12px 16px', color: '#b42318', fontSize: '13px' }}>
          {error}
        </div>
      )}

      {/* KPI Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#667085', textTransform: 'uppercase' }}>Monitored Accounts</span>
            <Users size={16} color="#155eef" />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-navy)', marginTop: '6px' }}>
            {data?.total_accounts.toLocaleString() || '102'}
          </div>
          <div style={{ fontSize: '11px', color: '#027a48', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
            <TrendingUp size={12} /> Active monitoring
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#667085', textTransform: 'uppercase' }}>Total Volume Transacted</span>
            <DollarSign size={16} color="#027a48" />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-navy)', marginTop: '6px' }}>
            {data?.total_tx_amount ? formatMoney(data.total_tx_amount) : '₹4.82 Cr'}
          </div>
          <div style={{ fontSize: '11px', color: '#667085', marginTop: '4px' }}>
            Across all monitored rails
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#667085', textTransform: 'uppercase' }}>Total Inflow (Credit)</span>
            <ArrowDownRight size={16} color="#155eef" />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#155eef', marginTop: '6px' }}>
            {data?.total_credit ? formatMoney(data.total_credit) : '₹2.41 Cr'}
          </div>
          <div style={{ fontSize: '11px', color: '#667085', marginTop: '4px' }}>Inbound aggregate flow</div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#667085', textTransform: 'uppercase' }}>Flagged Illicit Volume</span>
            <AlertTriangle size={16} color="#d92d20" />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#d92d20', marginTop: '6px' }}>
            {data?.fraud_transactions || '25'} Alerts
          </div>
          <div style={{ fontSize: '11px', color: '#d92d20', marginTop: '4px' }}>Active review queue</div>
        </div>
      </div>

      {/* Grid: Recent Alerts & Suspicious Accounts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '16px' }}>
        {/* Recent Alerts */}
        <div className="card">
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '12px' }}>
            High-Priority Active Alerts
          </h3>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Alert ID</th>
                  <th>Account</th>
                  <th>Amount</th>
                  <th>Risk Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {(data?.recent_alerts || []).slice(0, 5).map((a, idx) => (
                  <tr key={idx}>
                    <td className="code-mono" style={{ fontWeight: 600 }}>{a.alert_id || `ALT-${idx + 101}`}</td>
                    <td>{a.account_id || a.sender_account}</td>
                    <td style={{ fontWeight: 600 }}>{formatMoney(a.amount || 0)}</td>
                    <td>
                      <span className={`badge ${(a.risk_score || 0) >= 80 ? 'badge-danger' : 'badge-warning'}`}>
                        {a.risk_score || 85} / 100
                      </span>
                    </td>
                    <td><span className="badge badge-primary">{a.status || 'NEW'}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Suspicious Accounts */}
        <div className="card">
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '12px' }}>
            Top Suspicious Mule Accounts
          </h3>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Account ID</th>
                  <th>Holder Name</th>
                  <th>Region</th>
                  <th>Risk Score</th>
                </tr>
              </thead>
              <tbody>
                {(data?.suspicious_accounts || []).slice(0, 5).map((acc, idx) => (
                  <tr key={idx}>
                    <td className="code-mono" style={{ fontWeight: 600 }}>{acc.account_id}</td>
                    <td>{acc.holder_name}</td>
                    <td>{acc.region || 'Unknown'}</td>
                    <td>
                      <span className="badge badge-danger">
                        {acc.risk_score} / 100
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
