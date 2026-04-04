import { type InventoryStatus, statusConfig } from '@/utils/statusColors';

interface StatusBadgeProps {
  status: InventoryStatus | string;
  size?: 'sm' | 'md';
}

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = statusConfig[status as InventoryStatus] ?? statusConfig.ok;
  const sizeClasses = size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2.5 py-1';

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-md ${sizeClasses} ${config.bg} ${config.color} ring-1 ${config.ring}`}
    >
      {config.pulse && (
        <span className="relative flex h-2 w-2">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${config.color.replace('text-', 'bg-')}`} />
          <span className={`relative inline-flex rounded-full h-2 w-2 ${config.color.replace('text-', 'bg-')}`} />
        </span>
      )}
      {config.label}
    </span>
  );
}
