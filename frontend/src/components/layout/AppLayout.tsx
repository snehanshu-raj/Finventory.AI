import { type ReactNode } from 'react';
import { MobileNav } from './MobileNav';
import { MobileHeader } from './MobileHeader';

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col min-h-screen bg-[var(--color-bg)]">
      {/* Mobile header */}
      <MobileHeader />

      {/* Main content — scrollable area with bottom padding for nav */}
      <main className="flex-1 overflow-y-auto px-4 pt-2 pb-24">
        {children}
      </main>

      {/* Bottom tab navigation */}
      <MobileNav />
    </div>
  );
}
