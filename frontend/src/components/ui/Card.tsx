import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export function Card({ children, className = '', hover = false }: CardProps) {
  return (
    <div
      className={`bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] p-5
        ${hover ? 'hover:border-sky-500/30 hover:shadow-lg hover:shadow-sky-500/5 transition-all duration-200 cursor-pointer' : ''}
        ${className}`}
    >
      {children}
    </div>
  );
}
