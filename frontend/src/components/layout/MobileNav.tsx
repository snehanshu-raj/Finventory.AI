import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Package, Camera, BarChart3, MoreHorizontal } from 'lucide-react';

const tabs = [
  { to: '/', icon: LayoutDashboard, label: 'Home' },
  { to: '/inventory', icon: Package, label: 'Pantry' },
  { to: '/receipts', icon: Camera, label: 'Scan' },
  { to: '/analytics', icon: BarChart3, label: 'Insights' },
  { to: '/settings', icon: MoreHorizontal, label: 'More' },
];

export function MobileNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-[var(--color-surface)] to-[var(--color-surface)]/95 border-t border-[var(--color-border)] z-50 shadow-[0_-4px_30px_rgba(0,0,0,0.2)] backdrop-blur-xl" style={{ borderRadius: '20px 20px 0 0' }}>
      <div className="flex items-center justify-around h-16 px-2 pb-safe max-w-7xl mx-auto">
        {tabs.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1.5 py-2 px-3 rounded-lg transition-all duration-200
              ${isActive
                ? 'text-blue-400 bg-blue-500/10 shadow-lg shadow-blue-500/10'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] active:scale-90'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={22} strokeWidth={isActive ? 2.4 : 1.8} />
                <span className={`text-[10px] font-600 ${isActive ? 'font-bold' : ''}`}>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
