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
    <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[430px] bg-[var(--color-surface)] border-t border-[var(--color-border)] z-50 shadow-[0_-4px_20px_rgba(0,0,0,0.05)]" style={{ borderRadius: '20px 20px 0 0' }}>
      <div className="flex items-center justify-around h-16 px-2 pb-safe">
        {tabs.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 py-1.5 px-3 rounded-xl transition-all duration-200
              ${isActive
                ? 'text-[var(--color-primary)]'
                : 'text-[var(--color-muted)] active:scale-90'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div className={`relative ${isActive ? '' : ''}`}>
                  <Icon size={22} strokeWidth={isActive ? 2.5 : 1.8} />
                  {isActive && (
                    <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-[var(--color-primary)]" />
                  )}
                </div>
                <span className={`text-[10px] font-medium ${isActive ? 'font-semibold' : ''}`}>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
