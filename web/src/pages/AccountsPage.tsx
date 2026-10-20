import React, { useState, useEffect } from 'react';
import { Search, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { AccountItem } from '../services/api';

export const AccountsPage: React.FC = () => {
  const [accounts, setAccounts] = useState<AccountItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState<string>('');
  const [riskFilter, setRiskFilter] = useState<string>('All');
  const [regionFilter] = useState<string>('All');

  const loadAccounts = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getAccounts({
        search,
        risk_level: riskFilter,
        region: regionFilter,
      });
      setAccounts(res.accounts || []);
    } catch (err: any) {
      console.error('Failed to load accounts:', err);
      setError(err.message || 'Failed to fetch accounts.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAccounts();
  }, [riskFilter, regionFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadAccounts();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-navy)' }}>
            Monitored Accounts Directory
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
            Inspect account risk levels, debit/credit velocity, and regional distribution
          </p>
        </div>
        <button onClick={loadAccounts} className="btn btn-primary">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div style={{ background: '#fef3f2', border: '1px solid #fecdca', borderRadius: '8px', padding: '12px 16px', color: '#b42318', fontSize: '13px' }}>
          {error}
        </div>
      )}

      {/* Filter Row */}
      <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Search Account ID, Holder Name, or Number..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: '240px', padding: '8px 12px', border: '1px solid #d0d5dd', borderRadius: '6px', fontSize: '12px' }}
        />
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          style={{ padding: '8px 12px', border: '1px solid #d0d5dd', borderRadius: '6px', fontSize: '12px', background: '#fff' }}
        >
          <option value="All">All Risk Levels</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <button type="submit" className="btn btn-primary">
          <Search size={14} /> Search
        </button>
      </form>

      {/* Accounts Table */}
      <div className="card">
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Account ID</th>
                <th>Holder Name</th>
                <th>Account Number</th>
                <th>Region</th>
                <th>Total Inflow (Credit)</th>
                <th>Total Outflow (Debit)</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '24px', color: '#667085' }}>
                    Loading accounts...
                  </td>
                </tr>
              ) : accounts.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '24px', color: '#667085' }}>
                    No accounts found matching search filters.
                  </td>
                </tr>
              ) : (
                accounts.map((acc, i) => (
                  <tr key={i}>
                    <td className="code-mono" style={{ fontWeight: 600 }}>{acc.account_id}</td>
                    <td style={{ fontWeight: 600 }}>{acc.holder_name}</td>
                    <td className="code-mono">{acc.account_number}</td>
                    <td>{acc.region || 'India'}</td>
                    <td style={{ color: '#027a48', fontWeight: 600 }}>₹{Number(acc.credit_amount || 0).toLocaleString()}</td>
                    <td style={{ color: '#d92d20', fontWeight: 600 }}>₹{Number(acc.debit_amount || 0).toLocaleString()}</td>
                    <td style={{ fontWeight: 700, color: '#155eef' }}>{acc.risk_score} / 100</td>
                    <td>
                      <span className={`badge ${acc.risk_level === 'Critical' ? 'badge-danger' : acc.risk_level === 'High' ? 'badge-warning' : acc.risk_level === 'Low' ? 'badge-success' : 'badge-primary'}`}>
                        {acc.risk_level}
                      </span>
                    </td>
                    <td><span className="badge badge-neutral">{acc.status || 'ACTIVE'}</span></td>
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
