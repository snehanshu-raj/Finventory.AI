import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Receipt, Mail, DollarSign, ChevronDown } from 'lucide-react';
import { expensesApi, type UnifiedExpense } from '@/api/expenses';
import { useUserStore } from '@/store/userStore';
import { queryKeys } from '@/utils/constants';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { Card } from '@/components/ui/Card';
import { SkeletonCard, SkeletonRow } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';

export default function Expenses() {
  const userId = useUserStore((s) => s.userId) ?? '';
  const [source, setSource] = useState('all');
  const [category, setCategory] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['expenses', 'summary', userId],
    queryFn: () => expensesApi.summary(),
  });

  const { data: expenses, isLoading } = useQuery({
    queryKey: queryKeys.expenses(userId, { source, category }),
    queryFn: () => expensesApi.list({ source: source === 'all' ? undefined : source, category: category || undefined, limit: 50 }),
  });

  const s = summary as unknown as { today_total?: number; month_total?: number; by_source?: { receipt: number; gmail: number } } | undefined;
  const items = (expenses as unknown as { items?: UnifiedExpense[] })?.items ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Expenses</h1>

      {/* Summary Cards */}
      {summaryLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}</div>
      ) : s && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <p className="text-xs text-[var(--color-muted)] uppercase font-medium">Today</p>
            <p className="text-xl font-bold mt-1" style={{ fontFamily: 'var(--font-mono)' }}>{formatCurrency(s.today_total ?? 0)}</p>
          </Card>
          <Card>
            <p className="text-xs text-[var(--color-muted)] uppercase font-medium">This Month</p>
            <p className="text-xl font-bold mt-1 text-sky-400" style={{ fontFamily: 'var(--font-mono)' }}>{formatCurrency(s.month_total ?? 0)}</p>
          </Card>
          <Card>
            <p className="text-xs text-[var(--color-muted)] uppercase font-medium">Receipts</p>
            <p className="text-xl font-bold mt-1" style={{ fontFamily: 'var(--font-mono)' }}>{formatCurrency(s.by_source?.receipt ?? 0)}</p>
          </Card>
          <Card>
            <p className="text-xs text-[var(--color-muted)] uppercase font-medium">Gmail</p>
            <p className="text-xl font-bold mt-1" style={{ fontFamily: 'var(--font-mono)' }}>{formatCurrency(s.by_source?.gmail ?? 0)}</p>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-0.5">
          {['all', 'receipt', 'gmail'].map((s) => (
            <button key={s} onClick={() => setSource(s)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-colors
                ${source === s ? 'bg-sky-500 text-white' : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}>
              {s === 'all' ? 'All Sources' : s}
            </button>
          ))}
        </div>
        <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Filter by category"
          className="px-3 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500" />
      </div>

      {/* Expense Feed */}
      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <SkeletonRow key={i} />)}</div>
      ) : items.length === 0 ? (
        <EmptyState icon={DollarSign} title="No expenses found" description="Upload receipts or sync Gmail to see your expenses here" />
      ) : (
        <div className="space-y-2">
          {items.map((expense, i) => (
            <motion.div key={expense.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.02 }}>
              <div
                onClick={() => setExpandedId(expandedId === expense.id ? null : expense.id)}
                className={`flex items-center justify-between p-3 bg-[var(--color-surface)] border rounded-xl cursor-pointer transition-all hover:border-sky-500/20
                  ${expense.confidence < 0.85 ? 'border-l-2 border-l-yellow-400 border-[var(--color-border)]' : 'border-[var(--color-border)]'}`}>
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${expense.source === 'gmail' ? 'bg-red-500/10' : 'bg-sky-500/10'}`}>
                    {expense.source === 'gmail' ? <Mail size={16} className="text-red-400" /> : <Receipt size={16} className="text-sky-400" />}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{expense.merchant || 'Unknown'}</p>
                    <div className="flex items-center gap-2 text-xs text-[var(--color-muted)]">
                      <span>{expense.transaction_at ? formatDate(expense.transaction_at) : ''}</span>
                      {expense.category && (
                        <span className="px-1.5 py-0.5 bg-[var(--color-surface-2)] rounded text-[10px] capitalize">{expense.category}</span>
                      )}
                      {expense.confidence < 0.85 && (
                        <span className="px-1.5 py-0.5 bg-yellow-500/10 text-yellow-400 rounded text-[10px] font-medium">Needs Review</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold" style={{ fontFamily: 'var(--font-mono)' }}>{formatCurrency(expense.amount)}</span>
                  <ChevronDown size={14} className={`text-[var(--color-muted)] transition-transform ${expandedId === expense.id ? 'rotate-180' : ''}`} />
                </div>
              </div>
              {expandedId === expense.id && expense.meta && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                  className="ml-12 mt-1 p-3 bg-[var(--color-bg)] rounded-lg text-xs text-[var(--color-muted)] space-y-1">
                  {expense.meta.subject && <p><span className="font-medium">Subject:</span> {expense.meta.subject}</p>}
                  {expense.expense_type && <p><span className="font-medium">Type:</span> {expense.expense_type}</p>}
                  {expense.payment_method && <p><span className="font-medium">Payment:</span> {expense.payment_method}</p>}
                  <p><span className="font-medium">Confidence:</span> {(expense.confidence * 100).toFixed(0)}%</p>
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
