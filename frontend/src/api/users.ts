import client from './client';

export interface OnboardingPayload {
  name: string;
  email: string;
  household_profile: {
    household_size: number;
    adults: number;
    children: number;
  };
  diet_profile: {
    staples: Array<{
      canonical_item_id: string;
      canonical_name: string;
      daily_consumption_estimate: number;
      unit: string;
      threshold_quantity: number;
    }>;
  };
  preferences: {
    currency: string;
    locale: string;
    notification_enabled: boolean;
    notification_channels: string[];
  };
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string;
  household_profile: {
    household_size: number;
    adults: number;
    children: number;
  };
  diet_profile: {
    staples: Array<{
      canonical_item_id: string;
      canonical_name: string;
      daily_consumption_estimate: number;
      unit: string;
      threshold_quantity: number;
    }>;
  };
  preferences: {
    currency: string;
    locale: string;
    notification_enabled: boolean;
    notification_channels: string[];
  };
}

export const usersApi = {
  onboard: (data: OnboardingPayload) =>
    client.post<never, UserProfile>('/api/v1/users/onboarding', data),

  getUser: (userId: string) =>
    client.get<never, UserProfile>(`/api/v1/users/${userId}`, { params: { user_id: undefined } }),

  updateStaples: (userId: string, staples: OnboardingPayload['diet_profile']['staples']) =>
    client.patch<never, UserProfile>(`/api/v1/users/${userId}/staples`, { staples }, { params: { user_id: undefined } }),
};
