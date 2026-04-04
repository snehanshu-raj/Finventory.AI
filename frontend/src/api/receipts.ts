import client from './client';

export interface ReceiptItem {
  raw_text: string;
  canonical_item_id: string;
  canonical_name: string;
  category: string;
  brand?: string;
  quantity: number;
  unit: string;
  normalized_quantity?: number;
  normalized_unit?: string;
  unit_price?: number;
  line_price: number;
  confidence: number;
  is_grocery: boolean;
}

export interface Receipt {
  id: string;
  user_id: string;
  merchant: {
    name: string;
    normalized_name: string;
    store_id?: string;
    address?: string;
    phone?: string;
  };
  transaction: {
    receipt_number?: string;
    purchased_at: string;
    currency: string;
    subtotal: number;
    tax: number;
    tip: number;
    total: number;
    payment_method?: string;
  };
  items: ReceiptItem[];
  totals: {
    itemCount: number;
    groceryItemsCount: number;
    nonGroceryItemsCount: number;
  };
  review: {
    needsHumanReview: boolean;
    reviewed: boolean;
    reviewedAt?: string;
  };
  image_url: string;
  created_at: string;
}

export interface ReceiptListItem {
  id: string;
  merchant_name: string;
  total: number;
  item_count: number;
  purchased_at: string;
  image_url: string;
}

export interface ReceiptListResponse {
  items: ReceiptListItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export const receiptsApi = {
  upload: (userId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post<never, Receipt>('/api/v1/receipts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { user_id: userId },
    });
  },

  list: (params: { page?: number; page_size?: number; month?: string; store?: string }) =>
    client.get<never, ReceiptListResponse>('/api/v1/receipts', { params }),

  get: (receiptId: string) =>
    client.get<never, Receipt>(`/api/v1/receipts/${receiptId}`),

  review: (receiptId: string, data: { merchant_name?: string; items?: Partial<ReceiptItem>[] }) =>
    client.patch<never, Receipt>(`/api/v1/receipts/${receiptId}/review`, data),

  delete: (receiptId: string) =>
    client.delete(`/api/v1/receipts/${receiptId}`),
};
