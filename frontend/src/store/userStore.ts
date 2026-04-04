import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserState {
  userId: string | null;
  userName: string | null;
  userEmail: string | null;
  isOnboarded: boolean;
  setUser: (userId: string, name: string, email: string) => void;
  clearUser: () => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      userId: null,
      userName: null,
      userEmail: null,
      isOnboarded: false,
      setUser: (userId, userName, userEmail) =>
        set({ userId, userName, userEmail, isOnboarded: true }),
      clearUser: () =>
        set({ userId: null, userName: null, userEmail: null, isOnboarded: false }),
    }),
    { name: 'finventory-user' }
  )
);
