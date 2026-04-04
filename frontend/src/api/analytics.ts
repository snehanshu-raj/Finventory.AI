import client from './client';

export interface DashboardData {
  monthly_spend: number;
  low_stock_count: number;
  items_running_out_7days: Array<{
    canonical_name: string;
    estimated_days_left: number;
    status: string;
  }>;
  top_stores: Array<{
    store_name: string;
    total_spend: number;
    receipt_count: number;
  }>;
  savings_opportunities: unknown[];
}

export interface Prediction {
  canonical_item_id: string;
  canonical_name: string;
  current_quantity: number;
  daily_consumption_estimate: number;
  estimated_days_left: number | null;
  predicted_run_out_date: string | null;
  status: string;
}

export interface ExpenseSummary {
  current_month_total: number;
  previous_month_total: number;
  by_store: Array<{ store_name: string; total_spend: number; receipt_count: number }>;
  by_category: Array<{ category: string; total_spend: number; item_count: number }>;
  top_spend_items: Array<{ canonical_name: string; total_spend: number; purchase_count: number }>;
}

export interface BestStoreResult {
  canonical_item_id: string;
  best_store: string | null;
  stores: Array<{
    store_name: string;
    avg_unit_price: number;
    samples: number;
    last_seen: string;
  }>;
  confidence: number | null;
  insight: string;
}

export const analyticsApi = {
  dashboard: () =>
    client.get<never, DashboardData>('/api/v1/analytics/dashboard'),

  predictions: () =>
    client.get<never, Prediction[]>('/api/v1/analytics/predictions'),

  expensesSummary: () =>
    client.get<never, ExpenseSummary>('/api/v1/analytics/expenses/summary'),

  bestStore: (item: string, window = '30d') =>
    client.get<never, BestStoreResult>('/api/v1/analytics/prices/best-store', {
      params: { item, window },
    }),

  compareStores: (item: string, window = '30d') =>
    client.get<never, BestStoreResult>('/api/v1/analytics/prices/compare', {
      params: { item, window },
    }),
};
