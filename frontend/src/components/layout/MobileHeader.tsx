import { Bell, Moon, Sun, Menu } from 'lucide-react';
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

export function MobileHeader({ onMenuClick }: { onMenuClick?: () => void }) {
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
    <header className="sticky top-0 z-40 bg-gradient-to-r from-[var(--color-surface)]/80 to-[var(--color-surface-2)]/80 backdrop-blur-lg border-b border-[var(--color-border)] pt-3 pb-2 px-4">
      {isHome ? (
        /* Home header with greeting */
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[var(--color-muted)]">Good {getGreeting()} 👋</p>
            <h1 className="text-xl font-bold text-[var(--color-text)]">{userName ?? 'User'}</h1>
          </div>
          <div className="flex items-center gap-2">
            {onMenuClick && (
              <button
                onClick={onMenuClick}
                className="lg:hidden w-9 h-9 rounded-lg bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-3)] flex items-center justify-center transition-colors shadow-sm"
                aria-label="Menu"
              >
                <Menu size={18} className="text-[var(--color-text-secondary)]" />
              </button>
            )}
            <button
              onClick={toggleTheme}
              className="w-9 h-9 rounded-lg bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-3)] flex items-center justify-center transition-colors shadow-sm"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun size={16} className="text-[var(--color-warning)]" /> : <Moon size={16} className="text-[var(--color-muted)]" />}
            </button>
            <button
              onClick={() => navigate('/notifications')}
              className="relative w-9 h-9 rounded-lg bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-3)] flex items-center justify-center transition-colors shadow-sm"
              aria-label="Notifications"
            >
              <Bell size={16} className={unreadCount > 0 ? 'text-[var(--color-primary)] animate-pulse' : 'text-[var(--color-text-secondary)]'} />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 min-w-[18px] h-5 bg-gradient-to-r from-red-500 to-red-600 text-white text-[9px] font-bold rounded-full flex items-center justify-center px-1 shadow-md">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-400 via-purple-400 to-cyan-400 flex items-center justify-center text-white text-sm font-bold shadow-md">
              {userName?.charAt(0)?.toUpperCase() ?? 'U'}
            </div>
          </div>
        </div>
      ) : (
        /* Sub-page header with title */
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-[var(--color-text)]">{title}</h1>
          <div className="flex items-center gap-2">
            {onMenuClick && (
              <button
                onClick={onMenuClick}
                className="lg:hidden w-9 h-9 rounded-lg bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-3)] flex items-center justify-center transition-colors shadow-sm"
                aria-label="Menu"
              >
                <Menu size={18} className="text-[var(--color-text-secondary)]" />
              </button>
            )}
            <button
              onClick={toggleTheme}
              className="w-9 h-9 rounded-lg bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-3)] flex items-center justify-center transition-colors shadow-sm"
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
