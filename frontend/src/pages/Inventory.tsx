import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Search, Grid3X3, List, AlertTriangle, Edit3 } from 'lucide-react';
import { inventoryApi, type InventoryItem } from '@/api/inventory';
import { useUserStore } from '@/store/userStore';
import { useUIStore } from '@/store/uiStore';
import { queryKeys } from '@/utils/constants';
import { formatQuantity } from '@/utils/formatters';
import { getStatusColor } from '@/utils/statusColors';
import { Card } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';
import toast from 'react-hot-toast';

const STATUS_TABS = ['all', 'ok', 'low', 'critical', 'out_of_stock'] as const;

function DaysLeftRing({ daysLeft, threshold, status }: { daysLeft: number | null; threshold: number; status: string }) {
  const size = 56;
  const strokeWidth = 4;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const maxDays = threshold * 3;
  const pct = daysLeft != null ? Math.min(1, Math.max(0, daysLeft / maxDays)) : 0;
  const offset = circumference * (1 - pct);
  const color = getStatusColor(status);

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={strokeWidth} />
      <motion.circle
        cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth={strokeWidth}
        strokeLinecap="round" strokeDasharray={circumference}
        initial={{ strokeDashoffset: circumference }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
      />
      <text x={size / 2} y={size / 2} textAnchor="middle" dominantBaseline="central" fill={color}
        fontSize="11" fontWeight="600" transform={`rotate(90, ${size / 2}, ${size / 2})`}>
        {daysLeft != null ? `${Math.round(daysLeft)}d` : '—'}
      </text>
    </svg>
  );
}

export default function Inventory() {
  const userId = useUserStore((s) => s.userId) ?? '';
  const queryClient = useQueryClient();
  const openModal = useUIStore((s) => s.openModal);
  const closeModal = useUIStore((s) => s.closeModal);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState('estimatedDaysLeft');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [adjustQty, setAdjustQty] = useState('');
  const [adjustUnit, setAdjustUnit] = useState('');
  const [adjustReason, setAdjustReason] = useState('');

  const { data: items, isLoading } = useQuery({
    queryKey: queryKeys.inventory(userId),
    queryFn: () => inventoryApi.list({ sort_by: sortBy, ...(statusFilter !== 'all' ? { status: statusFilter } : {}) }),
  });

  const adjustMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { current_quantity: number; unit: string; reason?: string } }) =>
      inventoryApi.adjust(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.inventory(userId) });
      toast.success('Inventory updated!');
      closeModal();
    },
  });

  const filtered = (items as unknown as InventoryItem[] | undefined)?.filter((item) =>
    item.canonical_name.toLowerCase().includes(search.toLowerCase())
  ) ?? [];

  const lowStockCount = filtered.filter((i) => ['low', 'critical', 'out_of_stock'].includes(i.status)).length;

  const openAdjust = (item: InventoryItem) => {
    setSelectedItem(item);
    setAdjustQty(String(item.current_quantity));
    setAdjustUnit(item.unit);
    setAdjustReason('');
    openModal('adjust-inventory');
  };

  const handleAdjust = () => {
    if (!selectedItem) return;
    adjustMutation.mutate({
      id: selectedItem.canonical_item_id,
      data: { current_quantity: parseFloat(adjustQty) || 0, unit: adjustUnit, reason: adjustReason || undefined },
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">Pantry Inventory</h1>
          <p className="text-[var(--color-text-secondary)] mt-2">Manage your grocery items and low stock alerts</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">Pantry Inventory</h1>
        <p className="text-[var(--color-text-secondary)] mt-2">Manage your grocery items and low stock alerts</p>
      </motion.div>

      {/* Low stock alert */}
      {lowStockCount > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 p-4 bg-gradient-to-r from-orange-500/20 to-orange-500/5 border border-orange-500/30 rounded-xl">
          <AlertTriangle size={20} className="text-orange-400 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-orange-300">
              {lowStockCount} item{lowStockCount !== 1 ? 's' : ''} need attention
            </p>
            <p className="text-xs text-orange-300/70">These items are low or out of stock</p>
          </div>
        </motion.div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-muted)]" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search items..."
            className="w-full pl-9 pr-4 py-2.5 bg-[var(--color-surface)]/50 border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 focus:bg-[var(--color-surface)] transition-all" />
        </div>

        <div className="flex gap-1 bg-[var(--color-surface)]/50 border border-[var(--color-border)] rounded-lg p-1">
          {STATUS_TABS.map((tab) => (
            <button key={tab} onClick={() => setStatusFilter(tab)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold capitalize transition-all
                ${statusFilter === tab ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/20' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'}`}>
              {tab === 'out_of_stock' ? 'Out' : tab}
            </button>
          ))}
        </div>

        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2.5 bg-[var(--color-surface)]/50 border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 focus:bg-[var(--color-surface)] transition-all">
          <option value="estimatedDaysLeft">Days Left</option>
          <option value="currentQuantity">Quantity</option>
          <option value="name">Name</option>
        </select>

        <div className="flex gap-0.5 bg-[var(--color-surface)]/50 border border-[var(--color-border)] rounded-lg p-1">
          <button onClick={() => setViewMode('grid')} className={`p-1.5 rounded-md ${viewMode === 'grid' ? 'bg-sky-500 text-white' : 'text-[var(--color-muted)]'}`}><Grid3X3 size={16} /></button>
          <button onClick={() => setViewMode('list')} className={`p-1.5 rounded-md ${viewMode === 'list' ? 'bg-sky-500 text-white' : 'text-[var(--color-muted)]'}`}><List size={16} /></button>
        </div>
      </div>

      {/* Content */}
      {filtered.length === 0 ? (
        <EmptyState title="No inventory items" description="Upload a receipt to populate your pantry" />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((item, i) => (
            <motion.div key={item.canonical_item_id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
              <Card hover className="relative">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold capitalize text-sm">{item.canonical_name}</h3>
                    <p className="text-xs text-[var(--color-muted)] capitalize">{item.category}</p>
                  </div>
                  <DaysLeftRing daysLeft={item.estimated_days_left} threshold={item.threshold_quantity} status={item.status} />
                </div>
                <p className="text-xl font-bold mb-1" style={{ fontFamily: 'var(--font-mono)' }}>
                  {formatQuantity(item.current_quantity, item.unit)}
                </p>
                <div className="flex items-center justify-between mt-3">
                  <StatusBadge status={item.status} size="sm" />
                  <button onClick={() => openAdjust(item)} aria-label="Adjust inventory"
                    className="p-1.5 hover:bg-[var(--color-surface-2)] rounded-lg transition-colors">
                    <Edit3 size={14} className="text-[var(--color-muted)]" />
                  </button>
                </div>
                {item.estimated_days_left != null && (
                  <p className="text-[11px] text-[var(--color-muted)] mt-2">
                    Runs out in ~{Math.ceil(item.estimated_days_left)} days
                  </p>
                )}
              </Card>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-muted)] uppercase">
                <th className="p-3">Item</th><th className="p-3">Category</th><th className="p-3">Qty</th>
                <th className="p-3">Threshold</th><th className="p-3">Days Left</th><th className="p-3">Status</th><th className="p-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.canonical_item_id} className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-2)]/30">
                  <td className="p-3 font-medium capitalize">{item.canonical_name}</td>
                  <td className="p-3 text-[var(--color-muted)] capitalize">{item.category}</td>
                  <td className="p-3" style={{ fontFamily: 'var(--font-mono)' }}>{formatQuantity(item.current_quantity, item.unit)}</td>
                  <td className="p-3" style={{ fontFamily: 'var(--font-mono)' }}>{formatQuantity(item.threshold_quantity, item.unit)}</td>
                  <td className="p-3">{item.estimated_days_left != null ? `${item.estimated_days_left.toFixed(1)}d` : '—'}</td>
                  <td className="p-3"><StatusBadge status={item.status} size="sm" /></td>
                  <td className="p-3">
                    <button onClick={() => openAdjust(item)} className="text-sky-400 hover:text-sky-300 text-xs font-medium">Edit</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Adjust Modal */}
      <Modal id="adjust-inventory" title={`Adjust ${selectedItem?.canonical_name ?? 'Item'}`}>
        {selectedItem && (
          <div className="space-y-4">
            <div className="bg-[var(--color-bg)] p-3 rounded-lg border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-muted)]">Current</p>
              <p className="text-lg font-bold">{formatQuantity(selectedItem.current_quantity, selectedItem.unit)}</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">New Quantity</label>
              <input type="number" step="0.01" value={adjustQty} onChange={(e) => setAdjustQty(e.target.value)}
                className="w-full px-4 py-2.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Unit</label>
              <input value={adjustUnit} onChange={(e) => setAdjustUnit(e.target.value)}
                className="w-full px-4 py-2.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Reason (optional)</label>
              <textarea value={adjustReason} onChange={(e) => setAdjustReason(e.target.value)} rows={2}
                className="w-full px-4 py-2.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500 resize-none" />
            </div>
            <button onClick={handleAdjust} disabled={adjustMutation.isPending}
              className="w-full py-2.5 bg-sky-500 hover:bg-sky-600 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50">
              {adjustMutation.isPending ? 'Saving...' : 'Update Inventory'}
            </button>
          </div>
        )}
      </Modal>
    </div>
  );
}
