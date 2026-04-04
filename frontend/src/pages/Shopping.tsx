import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { ShoppingCart, AlertCircle, Clock, Store, Copy } from 'lucide-react';
import { shoppingApi, type ShoppingItem } from '@/api/shopping';
import { useUserStore } from '@/store/userStore';
import { formatCurrency, formatQuantity } from '@/utils/formatters';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import toast from 'react-hot-toast';

export default function Shopping() {
  const userId = useUserStore((s) => s.userId) ?? '';
  const [budget, setBudget] = useState('');
  const [checked, setChecked] = useState<Set<string>>(new Set());

  const mutation = useMutation({
    mutationFn: () => shoppingApi.suggest(userId, budget ? parseFloat(budget) : undefined),
  });

  const data = mutation.data as unknown as { must_buy_now: ShoppingItem[]; buy_soon: ShoppingItem[] } | undefined;

  const toggleCheck = (id: string) => {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const copyToClipboard = () => {
    if (!data) return;
    const lines = [
      '🛒 Shopping List',
      '',
      '⚠️ MUST BUY NOW:',
      ...data.must_buy_now.map((i) => `  □ ${i.canonical_name}${i.cheapest_store ? ` — best at ${i.cheapest_store}` : ''}${i.estimated_price ? ` (~${formatCurrency(i.estimated_price)})` : ''}`),
      '',
      '🔶 BUY SOON:',
      ...data.buy_soon.map((i) => `  □ ${i.canonical_name}${i.cheapest_store ? ` — best at ${i.cheapest_store}` : ''}`),
    ];
    navigator.clipboard.writeText(lines.join('\n'));
    toast.success('Shopping list copied!');
  };

  const ItemRow = ({ item, urgent }: { item: ShoppingItem; urgent: boolean }) => {
    const isChecked = checked.has(item.canonical_item_id);
    return (
      <AnimatePresence>
        <motion.div layout
          className={`flex items-center gap-3 p-3 rounded-xl transition-all ${isChecked ? 'opacity-40' : ''} ${urgent ? 'bg-red-500/5 border border-red-500/10' : 'bg-yellow-500/5 border border-yellow-500/10'}`}>
          <button onClick={() => toggleCheck(item.canonical_item_id)}
            className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 transition-colors
              ${isChecked ? 'bg-green-500 border-green-500' : urgent ? 'border-red-400' : 'border-yellow-400'}`}>
            {isChecked && <span className="text-white text-xs">✓</span>}
          </button>
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-medium capitalize ${isChecked ? 'line-through' : ''}`}>{item.canonical_name}</p>
            <p className="text-xs text-[var(--color-muted)]">
              {formatQuantity(item.current_quantity, 'left')}
              {item.estimated_days_left != null ? ` • ${item.estimated_days_left.toFixed(1)}d left` : ''}
            </p>
          </div>
          {item.cheapest_store && (
            <span className="flex items-center gap-1 px-2 py-0.5 bg-green-500/10 text-green-400 rounded text-[10px] font-medium">
              <Store size={10} />{item.cheapest_store}
            </span>
          )}
          {item.estimated_price != null && (
            <span className="text-sm font-semibold" style={{ fontFamily: 'var(--font-mono)' }}>{formatCurrency(item.estimated_price)}</span>
          )}
        </motion.div>
      </AnimatePresence>
    );
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Smart Shopping List</h1>

      {/* Controls */}
      <div className="flex items-center gap-3">
        <input value={budget} onChange={(e) => setBudget(e.target.value)} type="number" step="1" min="0"
          placeholder="Budget limit (optional)"
          className="flex-1 max-w-xs px-4 py-2.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500" />
        <button onClick={() => mutation.mutate()} disabled={mutation.isPending}
          className="px-5 py-2.5 bg-sky-500 hover:bg-sky-600 text-white rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 disabled:opacity-50">
          <ShoppingCart size={16} /> {mutation.isPending ? 'Generating...' : 'Generate List'}
        </button>
      </div>

      {mutation.isPending && <div className="space-y-4"><SkeletonCard /><SkeletonCard /></div>}

      {!mutation.isPending && !data && (
        <EmptyState icon={ShoppingCart} title="Generate your shopping list" description="Based on your current inventory, we'll tell you what to buy and where to get the best prices." />
      )}

      {data && (
        <div className="space-y-6">
          {/* Must Buy Now */}
          {data.must_buy_now.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <AlertCircle size={16} className="text-red-400" />
                <h2 className="text-sm font-semibold text-red-400 uppercase">Must Buy Now</h2>
                <span className="text-xs text-[var(--color-muted)]">({data.must_buy_now.length} items)</span>
              </div>
              <div className="space-y-2">
                {data.must_buy_now.map((item) => <ItemRow key={item.canonical_item_id} item={item} urgent />)}
              </div>
            </div>
          )}

          {/* Buy Soon */}
          {data.buy_soon.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Clock size={16} className="text-yellow-400" />
                <h2 className="text-sm font-semibold text-yellow-400 uppercase">Buy Soon</h2>
                <span className="text-xs text-[var(--color-muted)]">({data.buy_soon.length} items)</span>
              </div>
              <div className="space-y-2">
                {data.buy_soon.map((item) => <ItemRow key={item.canonical_item_id} item={item} urgent={false} />)}
              </div>
            </div>
          )}

          {data.must_buy_now.length === 0 && data.buy_soon.length === 0 && (
            <EmptyState icon={ShoppingCart} title="You're all stocked up!" description="Nothing to buy right now. Check back later." />
          )}

          {/* Actions */}
          {(data.must_buy_now.length > 0 || data.buy_soon.length > 0) && (
            <div className="flex gap-3 pt-2">
              <button onClick={copyToClipboard}
                className="flex items-center gap-2 px-4 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-sm font-medium hover:bg-[var(--color-surface-2)] transition-colors">
                <Copy size={14} /> Copy to Clipboard
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
