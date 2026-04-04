import client from './client';

export interface ShoppingItem {
  canonical_item_id: string;
  canonical_name: string;
  current_quantity: number;
  threshold_quantity?: number;
  estimated_days_left: number | null;
  cheapest_store: string | null;
  estimated_price: number | null;
}

export interface ShoppingList {
  must_buy_now: ShoppingItem[];
  buy_soon: ShoppingItem[];
}

export const shoppingApi = {
  suggest: (userId: string, budgetLimit?: number) =>
    client.post<never, ShoppingList>('/api/v1/shopping/suggest', {
      user_id: userId,
      budget_limit: budgetLimit,
    }),
};
