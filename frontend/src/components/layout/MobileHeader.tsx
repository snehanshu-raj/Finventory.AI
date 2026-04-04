import { Bell, Moon, Sun } from 'lucide-react';
import { useUIStore } from '@/store/uiStore';
import { useUserStore } from '@/store/userStore';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { notificationsApi } from '@/api/notifications';
import { queryKeys } from '@/utils/constants';

const TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/inventory': 'Pantry',
  '/receipts': 'Scan Receipt',
  '/analytics': 'Insights',
  '/meals': 'Meals',
  '/shopping': 'Shopping',
  '/expenses': 'Expenses',
  '/notifications': 'Notifications',
  '/settings': 'Settings',
};

export function MobileHeader() {
  const theme = useUIStore((s) => s.theme);
  const toggleTheme = useUIStore((s) => s.toggleTheme);
  const userName = useUserStore((s) => s.userName);
  const userId = useUserStore((s) => s.userId);
  const navigate = useNavigate();
  const location = useLocation();

  const title = TITLES[location.pathname] ?? 'Finventory';

  const { data: notifData } = useQuery({
    queryKey: queryKeys.notifications(userId ?? ''),
    queryFn: () => notificationsApi.list({ page: 1, page_size: 5 }),
    enabled: !!userId,
    refetchInterval: 30_000,
  });

  const unreadCount = (notifData as unknown as { items?: Array<{ status: string }> })?.items?.filter((n) => n.status !== 'dismissed').length ?? 0;

  const isHome = location.pathname === '/';

  return (
    <header className="sticky top-0 z-40 bg-[var(--color-bg)] pt-3 pb-2 px-4">
      {isHome ? (
        /* Home header with greeting */
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[var(--color-muted)]">Good {getGreeting()} 👋</p>
            <h1 className="text-xl font-bold text-[var(--color-text)]">{userName ?? 'User'}</h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="w-9 h-9 rounded-full bg-[var(--color-surface)] flex items-center justify-center shadow-sm"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun size={16} className="text-[var(--color-warning)]" /> : <Moon size={16} className="text-[var(--color-muted)]" />}
            </button>
            <button
              onClick={() => navigate('/notifications')}
              className="relative w-9 h-9 rounded-full bg-[var(--color-surface)] flex items-center justify-center shadow-sm"
              aria-label="Notifications"
            >
              <Bell size={16} className={unreadCount > 0 ? 'text-[var(--color-primary)] animate-shake' : 'text-[var(--color-muted)]'} />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 bg-[var(--color-danger)] text-white text-[9px] font-bold rounded-full flex items-center justify-center px-1">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center text-white text-sm font-bold shadow-sm">
              {userName?.charAt(0)?.toUpperCase() ?? 'U'}
            </div>
          </div>
        </div>
      ) : (
        /* Sub-page header with title */
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-[var(--color-text)]">{title}</h1>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="w-9 h-9 rounded-full bg-[var(--color-surface)] flex items-center justify-center shadow-sm"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun size={16} className="text-[var(--color-warning)]" /> : <Moon size={16} className="text-[var(--color-muted)]" />}
            </button>
          </div>
        </div>
      )}
    </header>
  );
}

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  return 'evening';
}
