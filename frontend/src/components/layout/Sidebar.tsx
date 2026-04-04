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
    <aside className="h-full w-60 bg-[var(--color-surface)] border-r border-[var(--color-border)] flex flex-col">
      {/* Logo */}
      <div className="p-5 border-b border-[var(--color-border)]">
        <h1 className="text-xl font-bold bg-gradient-to-r from-sky-400 to-cyan-300 bg-clip-text text-transparent">
          🧠 Finventory.AI
        </h1>
        <p className="text-xs text-[var(--color-muted)] mt-0.5">Smart Pantry Manager</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group
              ${isActive
                ? 'bg-sky-500/10 text-sky-400 border-l-[3px] border-sky-400 pl-[9px]'
                : 'text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-2)]/50'
              }`
            }
          >
            <Icon size={18} className="shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-[var(--color-border)]">
        <p className="text-[10px] text-[var(--color-muted)] text-center">v1.0 — PantryPilot</p>
      </div>
    </aside>
  );
}
