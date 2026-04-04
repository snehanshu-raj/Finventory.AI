import client from './client';

export interface UnifiedExpense {
  id: string;
  source: 'receipt' | 'gmail';
  source_id: string;
  merchant: string;
  normalized_merchant: string;
  amount: number;
  currency: string;
  transaction_at: string;
  category: string;
  payment_method?: string;
  expense_type?: string;
  confidence: number;
  meta?: {
    subject?: string;
    store_name?: string;
    receipt_id?: string;
    snippet?: string;
  };
}

export interface UnifiedExpenseList {
  items: UnifiedExpense[];
  total: number;
}

export interface UnifiedExpenseSummary {
  today_total: number;
  month_total: number;
  by_source: { receipt: number; gmail: number };
  by_category: Array<{ category: string; total: number }>;
  recent_merchants: string[];
}

export interface EmailExpense {
  id: string;
  user_id: string;
  gmail_message_id: string;
  source: 'gmail';
  sender: string;
  subject: string;
  snippet: string;
  received_at: string;
  expense_type: string;
  merchant: string;
  normalized_merchant: string;
  amount: number;
  currency: string;
  tax?: number;
  transaction_at: string;
  category: string;
  payment_method?: string;
  confidence: number;
  parsing_status: string;
  review: {
    needsHumanReview: boolean;
    reviewed: boolean;
    reviewedAt?: string;
  };
  raw_text: string;
  created_at: string;
}

export const expensesApi = {
  list: (params?: {
    source?: string;
    category?: string;
    from_date?: string;
    to_date?: string;
    merchant?: string;
    limit?: number;
    offset?: number;
  }) => client.get<never, UnifiedExpenseList>('/api/v1/expenses', { params }),

  summary: () =>
    client.get<never, UnifiedExpenseSummary>('/api/v1/expenses/summary'),

  emailExpenses: (params?: { page?: number; page_size?: number }) =>
    client.get<never, { items: EmailExpense[]; pagination: { page: number; page_size: number; total: number; total_pages: number } }>('/api/v1/email-expenses', { params }),

  reviewEmailExpense: (id: string, data: {
    merchant?: string;
    amount?: number;
    currency?: string;
    category?: string;
    expense_type?: string;
    transaction_at?: string;
  }) => client.patch<never, EmailExpense>(`/api/v1/email-expenses/${id}/review`, data),
};
