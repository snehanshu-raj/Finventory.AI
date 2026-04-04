import { format, formatDistanceToNow } from 'date-fns';

export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatQuantity(qty: number, unit: string): string {
  const formatted = qty % 1 === 0 ? qty.toString() : qty.toFixed(2);
  return `${formatted} ${unit}`;
}

export function formatDate(dateStr: string | Date): string {
  const d = typeof dateStr === 'string' ? new Date(dateStr) : dateStr;
  return format(d, 'MMM d, yyyy');
}

export function formatDateTime(dateStr: string | Date): string {
  const d = typeof dateStr === 'string' ? new Date(dateStr) : dateStr;
  return format(d, 'MMM d, yyyy h:mm a');
}

export function formatRelative(dateStr: string | Date): string {
  const d = typeof dateStr === 'string' ? new Date(dateStr) : dateStr;
  return formatDistanceToNow(d, { addSuffix: true });
}

export function formatPercentChange(current: number, previous: number): { value: string; positive: boolean } {
  if (previous === 0) return { value: 'N/A', positive: true };
  const change = ((current - previous) / previous) * 100;
  return {
    value: `${change > 0 ? '+' : ''}${change.toFixed(1)}%`,
    positive: change <= 0,
  };
}
