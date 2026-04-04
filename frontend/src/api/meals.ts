import client from './client';

export interface Meal {
  title: string;
  description: string;
  pantry_ingredients_used: string[];
  missing_ingredients: string[];
  prep_time_minutes: number;
  why_suggested: string;
}

export interface MealSuggestPayload {
  user_id: string;
  constraints?: {
    max_prep_minutes?: number;
    vegetarian?: boolean;
    budget_mode?: boolean;
  };
}

export const mealsApi = {
  suggest: (data: MealSuggestPayload) =>
    client.post<never, { meals: Meal[] }>('/api/v1/meals/suggest', data),
};
