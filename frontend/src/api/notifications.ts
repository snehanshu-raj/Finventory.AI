import client from './client';

export interface NotificationItem {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  status: string;
  channel: string;
  context?: Record<string, unknown>;
  created_at: string;
  sent_at?: string;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export const notificationsApi = {
  list: (params?: { page?: number; page_size?: number }) =>
    client.get<never, NotificationListResponse>('/api/v1/notifications', { params }),

  test: (data: { user_id: string; title: string; message: string }) =>
    client.post('/api/v1/notifications/test', data),

  dismiss: (notificationId: string) =>
    client.patch(`/api/v1/notifications/${notificationId}`, { status: 'dismissed' }),
};
