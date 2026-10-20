import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard, AlertTriangle, Users, DollarSign,
  Database, Cpu
} from 'lucide-react';
import { api } from './services/api';
import { DashboardPage } from './pages/DashboardPage';
import { AlertsPage } from './pages/AlertsPage';
import { AccountsPage } from './pages/AccountsPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { BenchmarkPage } from './pages/BenchmarkPage';
import { ModelIntelligencePage } from './pages/ModelIntelligencePage';

interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ size?: number; color?: string }>;
  badge?: string;
}

interface NavGroup {
  group: string;
  items: NavItem[];
}

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<string>('model-intelligence');
  const [healthStatus, setHealthStatus] = useState<'checking' | 'connected' | 'offline'>('checking');

  useEffect(() => {
    checkBackendHealth();
    const timer = setInterval(checkBackendHealth, 30000);
    return () => clearInterval(timer);
  }, []);

  const checkBackendHealth = async () => {
    try {
      await api.getHealth();
      setHealthStatus('connected');
    } catch {
      setHealthStatus('offline');
    }
  };

  const navGroups: NavGroup[] = [
    {
      group: 'OVERVIEW',
      items: [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
      ],
    },
    {
      group: 'RISK MONITORING',
      items: [
        { id: 'alerts', label: 'Active Alerts', icon: AlertTriangle },
      ],
    },
    {
      group: 'INVESTIGATION',
      items: [
        { id: 'accounts', label: 'Accounts Directory', icon: Users },
        { id: 'transactions', label: 'Transactions Ledger', icon: DollarSign },
      ],
    },
    {
      group: 'BENCHMARK EVALUATION',
      items: [
        { id: 'benchmark', label: 'IBM AML Benchmark', icon: Database, badge: 'Read-Only' },
      ],
    },
    {
      group: 'ANALYTICS',
      items: [
        { id: 'model-intelligence', label: 'Model Intelligence', icon: Cpu, badge: 'Verified' },
      ],
    },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--color-bg-canvas)' }}>
      {/* Sidebar */}
      <aside style={{
        width: '260px',
        background: '#ffffff',
        borderRight: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        position: 'sticky',
        top: 0,
        height: '100vh',
        zIndex: 50,
      }}>
        {/* Brand Header */}
        <div style={{ padding: '20px 22px', borderBottom: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #155eef 0%, #0040c1 100%)',
            color: '#fff',
            borderRadius: '8px',
            width: '36px',
            height: '36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '18px',
          }}>
            🛡️
          </div>
          <div>
            <div style={{ fontSize: '16px', fontWeight: 800, color: 'var(--color-navy)', letterSpacing: '-0.3px' }}>
              FinGuard AI
            </div>
            <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>
              Financial Crime Platform
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <div style={{ flex: 1, padding: '16px 12px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {navGroups.map((grp, gIdx) => (
            <div key={gIdx}>
              <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--color-text-subtle)', padding: '4px 12px', letterSpacing: '0.6px' }}>
                {grp.group}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '4px' }}>
                {grp.items.map(item => {
                  const Icon = item.icon;
                  const isActive = activePage === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActivePage(item.id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '9px 12px',
                        borderRadius: '6px',
                        background: isActive ? '#eff8ff' : 'transparent',
                        color: isActive ? '#155eef' : '#344054',
                        fontWeight: isActive ? 600 : 500,
                        fontSize: '13px',
                        border: 'none',
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Icon size={16} color={isActive ? '#155eef' : '#667085'} />
                        {item.label}
                      </div>
                      {item.badge && (
                        <span style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: '10px',
                          background: isActive ? '#155eef' : '#f2f4f7',
                          color: isActive ? '#ffffff' : '#475467',
                        }}>
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* System Health Status Footer */}
        <div style={{ padding: '14px 18px', borderTop: '1px solid var(--color-border)', background: '#fafbfc' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px' }}>
            <span style={{ color: '#667085', fontWeight: 500 }}>Backend API</span>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontWeight: 600,
              color: healthStatus === 'connected' ? '#027a48' : '#b54708',
            }}>
              <span style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: healthStatus === 'connected' ? '#12b76a' : '#f79009',
              }} />
              {healthStatus === 'connected' ? 'Connected' : 'Connecting...'}
            </span>
          </div>
          <div style={{ fontSize: '10px', color: '#98a2b3', marginTop: '4px', fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {api.getBaseUrl()}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '28px 36px', maxWidth: '1440px', overflowY: 'auto' }}>
        {activePage === 'dashboard' && <DashboardPage />}
        {activePage === 'alerts' && <AlertsPage />}
        {activePage === 'accounts' && <AccountsPage />}
        {activePage === 'transactions' && <TransactionsPage />}
        {activePage === 'benchmark' && <BenchmarkPage />}
        {activePage === 'model-intelligence' && <ModelIntelligencePage />}
      </main>
    </div>
  );
};

export default App;
