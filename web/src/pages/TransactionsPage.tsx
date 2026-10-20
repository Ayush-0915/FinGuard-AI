import React, { useState, useEffect } from 'react';
import { Search, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { TransactionItem } from '../services/api';

export const TransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState<string>('');
  const [riskFilter, setRiskFilter] = useState<string>('All');
  const [methodFilter, setMethodFilter] = useState<string>('All');

  const loadTransactions = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getTransactions({
        search,
        risk_level: riskFilter,
        payment_method: methodFilter,
      });
      setTransactions(res.transactions || []);
    } catch (err: any) {
      console.error('Failed to load transactions:', err);
      setError(err.message || 'Failed to fetch transactions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [riskFilter, methodFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadTransactions();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-navy)' }}>
            Transactions Ledger
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
            Full transaction stream across UPI, Net Banking, Cards, and Wire rails
          </p>
        </div>
        <button onClick={loadTransactions} className="btn btn-primary">
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
          placeholder="Search Transaction ID, Sender, Receiver..."
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
        <select
          value={methodFilter}
          onChange={(e) => setMethodFilter(e.target.value)}
          style={{ padding: '8px 12px', border: '1px solid #d0d5dd', borderRadius: '6px', fontSize: '12px', background: '#fff' }}
        >
          <option value="All">All Payment Methods</option>
          <option value="UPI">UPI</option>
          <option value="Net Banking">Net Banking</option>
          <option value="Debit Card">Debit Card</option>
          <option value="Credit Card">Credit Card</option>
          <option value="Wire">Wire</option>
          <option value="PayPal">PayPal</option>
        </select>
        <button type="submit" className="btn btn-primary">
          <Search size={14} /> Search
        </button>
      </form>

      {/* Transactions Table */}
      <div className="card">
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Timestamp</th>
                <th>Sender</th>
                <th>Receiver</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Risk Score</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '24px', color: '#667085' }}>
                    Loading transactions...
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '24px', color: '#667085' }}>
                    No transactions found matching filters.
                  </td>
                </tr>
              ) : (
                transactions.map((t, i) => (
                  <tr key={i}>
                    <td className="code-mono" style={{ fontWeight: 600 }}>{t.transaction_id}</td>
                    <td>{t.timestamp}</td>
                    <td className="code-mono">{t.sender_name || t.sender_id}</td>
                    <td className="code-mono">{t.receiver_name || t.receiver_id}</td>
                    <td style={{ fontWeight: 600 }}>₹{Number(t.amount || 0).toLocaleString()}</td>
                    <td><span className="badge badge-neutral">{t.payment_method || 'UPI'}</span></td>
                    <td style={{ fontWeight: 700, color: (t.risk_score || 0) >= 80 ? '#d92d20' : '#155eef' }}>
                      {t.risk_score} / 100
                    </td>
                    <td>
                      <span className={`badge ${t.status === 'FLAGGED' ? 'badge-danger' : 'badge-success'}`}>
                        {t.status}
                      </span>
                    </td>
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
