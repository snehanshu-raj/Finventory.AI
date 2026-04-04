import client from './client';

export interface GmailStatus {
  connected: boolean;
  email?: string;
  last_synced_at?: string;
  sync_enabled?: boolean;
}

export interface SyncRun {
  id: string;
  user_id: string;
  started_at: string;
  completed_at?: string;
  status: string;
  query_used?: string;
  messages_found: number;
  messages_parsed: number;
  messages_stored: number;
  errors: string[];
}

export interface SyncResult {
  messages_found: number;
  messages_parsed: number;
  messages_stored: number;
  errors: string[];
}

export const gmailApi = {
  status: () =>
    client.get<never, GmailStatus>('/api/v1/integrations/gmail/status'),

  sync: (daysBack = 0) =>
    client.post<never, SyncResult>('/api/v1/integrations/gmail/sync', null, {
      params: { days_back: daysBack },
    }),

  syncRuns: (limit = 10) =>
    client.get<never, SyncRun[]>('/api/v1/integrations/gmail/sync-runs', {
      params: { limit },
    }),
};
