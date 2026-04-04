import { type ReactNode, useState } from 'react';
import { Menu, X } from 'lucide-react';
import { MobileNav } from './MobileNav';
import { MobileHeader } from './MobileHeader';
import { Sidebar } from './Sidebar';

export function AppLayout({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-[var(--color-bg)] via-[var(--color-bg-secondary)] to-[var(--color-bg)]">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block w-64 border-r border-[var(--color-border)] sticky top-0 h-screen overflow-y-auto bg-[var(--color-surface)]/40 backdrop-blur-xl">
        <Sidebar />
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile Sidebar Drawer */}
      <div
        className={`fixed left-0 top-0 h-screen w-64 bg-[var(--color-surface)]/95 backdrop-blur-xl z-50 transform transition-transform duration-300 lg:hidden
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="p-4 border-b border-[var(--color-border)] flex items-center justify-between">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Finventory</h1>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-2 hover:bg-[var(--color-surface-2)] rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        <Sidebar />
      </div>

      <div className="flex-1 flex flex-col lg:overflow-hidden">
        {/* Mobile Header */}
        <div className="lg:hidden sticky top-0 z-30">
          <MobileHeader onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
        </div>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto pb-24 lg:pb-8 px-4 lg:px-8 pt-4 lg:pt-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>

        {/* Mobile Bottom Navigation */}
        <div className="lg:hidden">
          <MobileNav />
        </div>
      </div>
    </div>
  );
}
