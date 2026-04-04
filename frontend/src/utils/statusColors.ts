export type InventoryStatus = 'ok' | 'low' | 'critical' | 'out_of_stock';

export const statusConfig: Record<InventoryStatus, { color: string; bg: string; ring: string; text: string; label: string; pulse: boolean }> = {
  ok: {
    color: 'text-green-500',
    bg: 'bg-green-500/10',
    ring: 'ring-green-500/30',
    text: '#22c55e',
    label: 'In Stock',
    pulse: false,
  },
  low: {
    color: 'text-yellow-400',
    bg: 'bg-yellow-400/10',
    ring: 'ring-yellow-400/30',
    text: '#facc15',
    label: 'Low',
    pulse: false,
  },
  critical: {
    color: 'text-orange-500',
    bg: 'bg-orange-500/10',
    ring: 'ring-orange-500/30',
    text: '#f97316',
    label: 'Critical',
    pulse: true,
  },
  out_of_stock: {
    color: 'text-red-500',
    bg: 'bg-red-500/10',
    ring: 'ring-red-500/30',
    text: '#ef4444',
    label: 'Out of Stock',
    pulse: true,
  },
};

export function getStatusColor(status: string): string {
  return statusConfig[status as InventoryStatus]?.text ?? '#94a3b8';
}
