export const DEFAULT_STAPLES = [
  { name: 'milk', unit: 'liter', daily: 0.5, threshold: 1.0 },
  { name: 'rice', unit: 'kg', daily: 0.18, threshold: 1.0 },
  { name: 'eggs', unit: 'count', daily: 2, threshold: 6 },
  { name: 'bread', unit: 'count', daily: 1, threshold: 2 },
  { name: 'butter', unit: 'g', daily: 10, threshold: 100 },
  { name: 'oil', unit: 'liter', daily: 0.02, threshold: 0.5 },
  { name: 'sugar', unit: 'kg', daily: 0.02, threshold: 0.5 },
  { name: 'salt', unit: 'kg', daily: 0.005, threshold: 0.5 },
  { name: 'flour', unit: 'kg', daily: 0.05, threshold: 1.0 },
  { name: 'atta', unit: 'kg', daily: 0.1, threshold: 1.0 },
];

export const CURRENCIES = [
  { value: 'USD', label: 'USD ($)' },
  { value: 'EUR', label: 'EUR (€)' },
  { value: 'GBP', label: 'GBP (£)' },
  { value: 'INR', label: 'INR (₹)' },
];

export const UNIT_OPTIONS = ['kg', 'g', 'liter', 'ml', 'count', 'lb', 'oz'];

export const queryKeys = {
  inventory: (userId: string) => ['inventory', userId] as const,
  inventoryItem: (userId: string, itemId: string) => ['inventory', userId, itemId] as const,
  receipts: (userId: string, filters?: Record<string, unknown>) => ['receipts', userId, filters] as const,
  dashboard: (userId: string) => ['analytics', 'dashboard', userId] as const,
  predictions: (userId: string) => ['analytics', 'predictions', userId] as const,
  expensesSummary: (userId: string) => ['analytics', 'expenses', userId] as const,
  meals: (userId: string) => ['meals', userId] as const,
  shopping: (userId: string) => ['shopping', userId] as const,
  notifications: (userId: string) => ['notifications', userId] as const,
  expenses: (userId: string, filters?: Record<string, unknown>) => ['expenses', userId, filters] as const,
  gmailStatus: (userId: string) => ['gmail', 'status', userId] as const,
  gmailSyncRuns: (userId: string) => ['gmail', 'sync-runs', userId] as const,
};
