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
  const isOnboarded = useUserStore((s) => s.isOnboarded);

  if (!isOnboarded) {
    return <Navigate to="/onboarding" replace />;
  }

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
  const isOnboarded = useUserStore((s) => s.isOnboarded);
  const setUser = useUserStore((s) => s.setUser);
  const [isInitializing, setIsInitializing] = useState(true);

  // Check backend onboarding status on app mount
  useEffect(() => {
    const checkOnboarding = async () => {
      try {
        const response = await usersApi.checkOnboarding();
        const data = response as unknown as { onboarded: boolean; user_id: string };
        
        // If user is onboarded in backend but not in localStorage, update store
        if (data.onboarded && !isOnboarded) {
          // Fetch user profile to get name and email
          try {
            const profile = await usersApi.getUser(data.user_id);
            const p = profile as unknown as { id: string; name: string; email: string };
            setUser(p.id, p.name, p.email);
          } catch {
            // If profile fetch fails, still mark as onboarded with just ID
            setUser(data.user_id, 'User', 'user@example.com');
          }
        }
      } catch (err) {
        // Silently fail - user might not have internet or backend isn't ready
        console.debug('Onboarding check failed:', err);
      } finally {
        setIsInitializing(false);
      }
    };

    checkOnboarding();
  }, []);

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
            <Route path="/*" element={<ProtectedRoutes />} />
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
