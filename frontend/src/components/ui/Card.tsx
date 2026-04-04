import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  gradient?: boolean;
}

export function Card({ children, className = '', hover = false, gradient = false }: CardProps) {
  const baseClasses = `
    rounded-xl p-5 transition-all duration-300
    ${gradient 
      ? 'bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-surface-2)] border border-[var(--color-border)]'
      : 'bg-[var(--color-surface)]/60 backdrop-blur-xl border border-[var(--color-border)]'
    }
    ${hover 
      ? 'hover:border-blue-400/50 hover:bg-[var(--color-surface)]/80 hover:shadow-xl hover:shadow-blue-500/10 cursor-pointer' 
      : ''
    }
  `;
  return <div className={`${baseClasses} ${className}`}>{children}</div>;
}
