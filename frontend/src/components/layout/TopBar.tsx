import { Bell, Menu, Moon, Sun } from 'lucide-react';
import { useUIStore } from '@/store/uiStore';
import { useUserStore } from '@/store/userStore';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { notificationsApi } from '@/api/notifications';
import { queryKeys } from '@/utils/constants';

export function TopBar() {
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const theme = useUIStore((s) => s.theme);
  const toggleTheme = useUIStore((s) => s.toggleTheme);
  const userName = useUserStore((s) => s.userName);
  const userId = useUserStore((s) => s.userId);
  const navigate = useNavigate();

  const { data: notifData } = useQuery({
    queryKey: queryKeys.notifications(userId ?? ''),
    queryFn: () => notificationsApi.list({ page: 1, page_size: 5 }),
    enabled: !!userId,
    refetchInterval: 30_000,
  });

  const unreadCount = notifData?.items?.filter((n: { status: string }) => n.status !== 'dismissed').length ?? 0;

  return (
    <header className="h-14 bg-[var(--color-surface)] border-b border-[var(--color-border)] flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="hidden md:flex p-1.5 rounded-lg hover:bg-[var(--color-surface-2)] transition-colors"
          aria-label="Toggle sidebar"
        >
          <Menu size={20} />
        </button>
        <span className="md:hidden text-lg font-bold bg-gradient-to-r from-sky-400 to-cyan-300 bg-clip-text text-transparent">
          🧠 Finventory
        </span>
      </div>

      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-[var(--color-surface-2)] transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Notification bell */}
        <button
          onClick={() => navigate('/notifications')}
          className="relative p-2 rounded-lg hover:bg-[var(--color-surface-2)] transition-colors"
          aria-label="Notifications"
        >
          <Bell size={18} className={unreadCount > 0 ? 'animate-shake' : ''} />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* User avatar */}
        {userName && (
          <div className="hidden md:flex items-center gap-2 ml-2 px-3 py-1.5 bg-[var(--color-surface-2)] rounded-lg">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-sky-400 to-cyan-300 flex items-center justify-center text-xs font-bold text-slate-900">
              {userName.charAt(0).toUpperCase()}
            </div>
            <span className="text-sm font-medium">{userName}</span>
          </div>
        )}
      </div>
    </header>
  );
}
