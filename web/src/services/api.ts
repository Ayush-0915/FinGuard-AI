/**
 * FinGuard AI — API Client Service
 * Communicates with the FastAPI backend deployment on Render or localhost.
 * Strictly read-only against benchmark and model intelligence endpoints.
 */

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error ${response.status} on ${path}: ${errorText || response.statusText}`);
  }

  return response.json();
}

// -------------------------------------------------------------
// Type Definitions
// -------------------------------------------------------------

export interface HealthResponse {
  status: string;
  database?: string;
  model?: string;
  timestamp?: string;
}

export interface DashboardData {
  total_accounts: number;
  total_tx_amount: number;
  total_credit: number;
  total_debit: number;
  fraud_transactions: number;
  active_alerts: number;
  recent_alerts: any[];
  suspicious_accounts: any[];
  chart_data?: {
    labels: string[];
    total: number[];
    credit: number[];
    debit: number[];
    fraud: number[];
  };
  regional_risk?: Record<string, number>;
  payment_methods?: Record<string, any>;
}

export interface AccountItem {
  account_id: string;
  holder_name: string;
  account_number: string;
  ifsc_code?: string;
  region: string;
  city?: string;
  age_months?: number;
  credit_amount: number;
  debit_amount: number;
  risk_score: number;
  risk_level: string;
  status: string;
}

export interface TransactionItem {
  transaction_id: string;
  timestamp: string;
  sender_id: string;
  receiver_id: string;
  sender_name?: string;
  receiver_name?: string;
  amount: number;
  payment_method: string;
  risk_score: number;
  risk_level: string;
  status: string;
  receiving_currency?: string;
  payment_currency?: string;
  payment_format?: string;
}

export interface PrioritizedAlert {
  transaction_id: string;
  timestamp: string;
  sender_account: string;
  receiver_account: string;
  amount: number;
  currency: string;
  payment_format: string;
  model_risk_score: number;
  risk_rank: number;
  risk_tier: string;
  contributing_signals?: any[];
  graph_patterns?: any[];
  human_readable_summary?: string;
}

export interface ModelIntelligenceData {
  status: string;
  production_model: {
    model_name: string;
    model_file: string;
    algorithm: string;
    num_features: number;
    best_iteration: number;
    scale_pos_weight: number;
    max_depth: number;
    num_leaves: number;
    learning_rate: number;
    objective: string;
    sha256: string;
    encoders_file: string;
    encoders_sha256: string;
    isolation_forest_file: string;
    isolation_forest_sha256: string;
    shap_explainer_file: string;
    shap_explainer_sha256: string;
    status: string;
    audit_date: string;
    role: string;
  };
  secondary_model: {
    model_name: string;
    model_file: string;
    algorithm: string;
    n_estimators: number;
    max_samples: number;
    contamination: string | number;
    sha256: string;
    status: string;
    score_semantics: string;
  };
  experimental_model: {
    model_name: string;
    model_file: string;
    algorithm: string;
    num_features: number;
    best_iteration: number;
    validation_calibrated_threshold: number;
    training_rows: number;
    validation_rows: number;
    test_rows: number;
    sha256: string;
    status: string;
    audit_date: string;
  };
  performance_metrics: {
    experimental_lightgbm: {
      roc_auc: number;
      pr_auc: number;
      precision: number;
      recall: number;
      f1: number;
      specificity: number;
      fpr: number;
      mcc: number;
      threshold: number;
      confusion_matrix: {
        tp: number;
        fp: number;
        tn: number;
        fn: number;
      };
    };
    zero_shot_baseline: {
      roc_auc: number;
      pr_auc: number;
      precision: number;
      recall: number;
      f1: number;
      specificity: number;
      fpr: number;
      mcc: number;
      threshold: number;
      confusion_matrix: {
        tp: number;
        fp: number;
        tn: number;
        fn: number;
      };
    };
  };
  features: Array<{
    name: string;
    category: string;
    description: string;
    gain_rank: number;
    gain_pct: number;
    splits: number;
    data_source: string;
    used_in_lightgbm: boolean;
    used_in_fusion: boolean;
  }>;
  feature_count: number;
  risk_fusion: {
    weights: {
      model: number;
      graph: number;
      behavior: number;
      rule: number;
    };
    formula: string;
    operational_tiers: Record<string, { range: string; action: string; sla: string }>;
    score_semantics: Record<string, string>;
  };
  alert_budgets: Array<{
    budget: number;
    tp: number;
    fp: number;
    precision: number;
    recall: number;
    tier: string;
    desc: string;
  }>;
  dataset_info: {
    name: string;
    total_transactions: number;
    illicit_transactions: number;
    legitimate_transactions: number;
    illicit_prevalence_pct: number;
    time_period: string;
    num_currencies: number;
    currencies: string[];
    num_payment_formats: number;
    payment_formats: string[];
    dataset_separation: Record<string, string>;
    provenance_statement: string;
  };
  explainability_and_limitations: {
    shap_explainer: string;
    top_gain_features: Array<{ feature: string; gain_pct: number; description: string }>;
    limitations: Array<{ title: string; detail: string }>;
  };
}

export interface IbmSummary {
  status: string;
  data_source: string;
  disclaimer: string;
  run_id: string;
  source_dataset: string;
  source_sha256: string;
  total_scanned_rows: number;
  selected_records_count: number;
  model_version: string;
  pipeline_version: string;
  selection_policy: string;
  tier_distribution: Record<string, number>;
  timestamp_range: {
    start: string;
    end: string;
  };
}

// -------------------------------------------------------------
// API Client Object
// -------------------------------------------------------------

export const api = {
  getBaseUrl: () => API_BASE,

  getHealth: () => fetchJson<HealthResponse>('/health'),

  getDashboard: () => fetchJson<DashboardData>('/dashboard'),

  getAccounts: (params?: { search?: string; risk_level?: string; region?: string }) => {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.risk_level && params.risk_level !== 'All') q.append('risk_level', params.risk_level);
    if (params?.region && params.region !== 'All') q.append('region', params.region);
    return fetchJson<{ total: number; accounts: AccountItem[] }>(`/accounts?${q.toString()}`);
  },

  getAccountDetail: (id: string) => fetchJson<AccountItem>(`/accounts/${id}`),

  getTransactions: (params?: { account_id?: string; search?: string; risk_level?: string; payment_method?: string }) => {
    const q = new URLSearchParams();
    if (params?.account_id) q.append('account_id', params.account_id);
    if (params?.search) q.append('search', params.search);
    if (params?.risk_level && params.risk_level !== 'All') q.append('risk_level', params.risk_level);
    if (params?.payment_method && params.payment_method !== 'All') q.append('payment_method', params.payment_method);
    return fetchJson<{ total: number; transactions: TransactionItem[] }>(`/transactions?${q.toString()}`);
  },

  getAlerts: () => fetchJson<{ total: number; alerts: any[] }>('/alerts'),

  getPrioritizedAlerts: () => fetchJson<{ status: string; total_alerts: number; alerts: PrioritizedAlert[] }>('/api/v2/alerts/prioritized'),

  getCases: (status?: string, tier?: string) => {
    const q = new URLSearchParams();
    if (status && status !== 'All') q.append('status', status);
    if (tier && tier !== 'All') q.append('tier', tier);
    return fetchJson<{ status: string; total_cases: number; cases: any[] }>(`/api/v2/cases?${q.toString()}`);
  },

  getCaseDetail: (id: string) => fetchJson<{ status: string; case: any }>(`/api/v2/cases/${id}`),

  getModelIntelligence: () => fetchJson<ModelIntelligenceData>('/api/v2/model/intelligence'),

  getIbmSummary: (runId?: string) => {
    const q = runId ? `?run_id=${encodeURIComponent(runId)}` : '';
    return fetchJson<IbmSummary>(`/api/v2/ibm/summary${q}`);
  },

  getIbmAlerts: (budget = 50, tier = 'All') => {
    const q = new URLSearchParams({ budget: budget.toString(), tier });
    return fetchJson<{ status: string; data_source: string; total_available: number; returned_count: number; alerts: any[] }>(`/api/v2/ibm/alerts?${q.toString()}`);
  },

  getIbmTransactions: (page = 1, limit = 50, accountId?: string) => {
    const q = new URLSearchParams({ page: page.toString(), limit: limit.toString() });
    if (accountId) q.append('account_id', accountId);
    return fetchJson<{ status: string; data_source: string; total_records: number; transactions: any[] }>(`/api/v2/ibm/transactions?${q.toString()}`);
  },

  getIbmEvidence: (txId: string) => fetchJson<{ status: string; data_source: string; evidence: any }>(`/api/v2/ibm/transactions/${txId}/evidence`),

  getRegionalRisk: () => fetchJson<any>('/regional-risk'),

  getPaymentMethods: () => fetchJson<any>('/payment-methods'),
};
