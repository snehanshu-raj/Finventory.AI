import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { PackageOpen } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ icon: Icon = PackageOpen, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-6 shadow-lg shadow-blue-500/10">
        <Icon size={32} className="text-blue-400 opacity-70" />
      </div>
      <h3 className="text-lg font-bold text-[var(--color-text)] mb-2">{title}</h3>
      <p className="text-sm text-[var(--color-text-secondary)] max-w-sm mb-6">{description}</p>
      {action}
    </div>
  );
}
