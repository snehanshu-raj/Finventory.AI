import { lazy, Suspense, useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AppLayout } from '@/components/layout/AppLayout';
import { useUserStore } from '@/store/userStore';
import { useUIStore } from '@/store/uiStore';
import { usersApi } from '@/api/users';

const Onboarding = lazy(() => import('@/pages/Onboarding'));
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Inventory = lazy(() => import('@/pages/Inventory'));
const Receipts = lazy(() => import('@/pages/Receipts'));
const Analytics = lazy(() => import('@/pages/Analytics'));
const Meals = lazy(() => import('@/pages/Meals'));
const Shopping = lazy(() => import('@/pages/Shopping'));
const Expenses = lazy(() => import('@/pages/Expenses'));
const Notifications = lazy(() => import('@/pages/Notifications'));
const Settings = lazy(() => import('@/pages/Settings'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 300_000,
      retry: 2,
      refetchOnWindowFocus: true,
    },
  },
});

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 opacity-30 animate-pulse" />
        <div className="absolute inset-2 rounded-full border-2 border-transparent border-t-blue-400 border-r-purple-400 animate-spin" />
      </div>
    </div>
  );
}

function ProtectedRoutes() {
  return (
    <AppLayout>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/receipts" element={<Receipts />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/meals" element={<Meals />} />
          <Route path="/shopping" element={<Shopping />} />
          <Route path="/expenses" element={<Expenses />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </AppLayout>
  );
}

export default function App() {
  const theme = useUIStore((s) => s.theme);
  const setUser = useUserStore((s) => s.setUser);
  const clearUser = useUserStore((s) => s.clearUser);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isOnboarded, setIsOnboarded] = useState(false);

  // Always check API on mount - source of truth is database
  useEffect(() => {
    const checkOnboardingFromDB = async () => {
      try {
        const user = await usersApi.getOnboardingData();
        const userData = user as unknown as { 
          id: string
          name: string
          email: string
          household_profile?: { household_size?: number }
        };
        
        // Check if user has actual onboarding data
        const hasHousehold = userData.household_profile?.household_size && userData.household_profile.household_size > 0;
        const hasName = userData.name && userData.name.trim() !== '';
        
        if (hasHousehold && hasName) {
          setUser(userData.id, userData.name, userData.email);
          setIsOnboarded(true);
        } else {
          clearUser();
          setIsOnboarded(false);
        }
      } catch (err) {
        console.debug('Onboarding check failed:', err);
        clearUser();
        setIsOnboarded(false);
      } finally {
        setIsInitializing(false);
      }
    };

    checkOnboardingFromDB();
  }, [setUser, clearUser]);

  useEffect(() => {
    document.documentElement.classList.toggle('light', theme === 'light');
  }, [theme]);

  if (isInitializing) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-[#0f172a] via-[#1a2744] to-[#0f172a]">
        <PageLoader />
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/*" element={isOnboarded ? <ProtectedRoutes /> : <Navigate to="/onboarding" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
            color: '#f1f5f9',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: '12px',
            fontSize: '14px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.4), 0 0 20px rgba(59, 130, 246, 0.1)',
            backdropFilter: 'blur(10px)',
          },
        }}
      />
    </QueryClientProvider>
  );
}
