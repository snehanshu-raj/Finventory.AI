import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  Receipt,
  BarChart3,
  ChefHat,
  ShoppingCart,
  Wallet,
  Bell,
  Settings,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inventory', icon: Package, label: 'Inventory' },
  { to: '/receipts', icon: Receipt, label: 'Receipts' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/meals', icon: ChefHat, label: 'Meals' },
  { to: '/shopping', icon: ShoppingCart, label: 'Shopping' },
  { to: '/expenses', icon: Wallet, label: 'Expenses' },
  { to: '/notifications', icon: Bell, label: 'Notifications' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar() {
  return (
    <aside className="h-full w-full flex flex-col">
      {/* Logo Section */}
      <div className="p-6 border-b border-[var(--color-border)]/50">
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
          ✨ Finventory
        </h1>
        <p className="text-xs text-[var(--color-text-secondary)] mt-1">Smart Financial Companion</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `relative flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-500 transition-all duration-200 group
              ${isActive
                ? 'text-blue-300 bg-gradient-to-r from-blue-500/20 to-purple-500/10 shadow-lg shadow-blue-500/10 border border-blue-500/20'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-2)]/60'
              }`
            }
          >
            <Icon size={19} className="shrink-0" strokeWidth={2} />
            <span>{label}</span>
            {/* Active indicator */}
            {/* Placeholder for isActive - will be set by NavLink */}
          </NavLink>
        ))}
      </nav>

      {/* Bottom section with stats */}
      <div className="p-4 border-t border-[var(--color-border)]/50 space-y-3">
        <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-lg p-3 border border-blue-500/10">
          <p className="text-xs font-semibold text-[var(--color-text-secondary)]">Quick Access</p>
          <p className="text-2xs text-[var(--color-muted)] mt-1">Stay on top of your finances</p>
        </div>
        <p className="text-[10px] text-[var(--color-muted)] text-center">Finventory.AI v1.0</p>
      </div>
    </aside>
  );
}
