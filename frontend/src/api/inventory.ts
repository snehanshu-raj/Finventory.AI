import client from './client';

export interface InventoryItem {
  canonical_item_id: string;
  canonical_name: string;
  category: string;
  current_quantity: number;
  unit: string;
  threshold_quantity: number;
  daily_consumption_estimate: number;
  estimated_days_left: number | null;
  status: 'ok' | 'low' | 'critical' | 'out_of_stock';
  last_updated_at: string;
  last_receipt_at?: string;
  reminder_enabled: boolean;
  last_reminder_sent_at?: string;
}

export interface InventoryDetail {
  item: InventoryItem;
  recent_events: Array<{
    id: string;
    event_type: string;
    delta_quantity: number;
    unit: string;
    created_at: string;
    source: { type: string; referenceId?: string };
  }>;
}

export const inventoryApi = {
  list: (params?: { status?: string; category?: string; sort_by?: string }) =>
    client.get<never, InventoryItem[]>('/api/v1/inventory', { params }),

  lowStock: () =>
    client.get<never, InventoryItem[]>('/api/v1/inventory/low-stock'),

  getItem: (itemId: string) =>
    client.get<never, InventoryDetail>(`/api/v1/inventory/${itemId}`),

  adjust: (itemId: string, data: { current_quantity: number; unit: string; reason?: string }) =>
    client.patch<never, InventoryItem>(`/api/v1/inventory/${itemId}`, data),

  reset: () =>
    client.delete<never, { states_deleted: number; events_deleted: number }>('/api/v1/inventory/reset'),
};
