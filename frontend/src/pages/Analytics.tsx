import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Search, ArrowRight } from 'lucide-react';
import { analyticsApi } from '@/api/analytics';
import { useUserStore } from '@/store/userStore';
import { queryKeys } from '@/utils/constants';
import { formatCurrency, formatDate, formatPercentChange } from '@/utils/formatters';
import { getStatusColor } from '@/utils/statusColors';
import { Card } from '@/components/ui/Card';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const CATEGORY_COLORS = ['#0ea5e9', '#f97316', '#22c55e', '#eab308', '#a855f7', '#ec4899', '#14b8a6', '#f43f5e'];
const TABS = ['Spending', 'Predictions', 'Price Insights'] as const;

export default function Analytics() {
  const userId = useUserStore((s) => s.userId) ?? '';
  const [activeTab, setActiveTab] = useState<typeof TABS[number]>('Spending');
  const [priceItem, setPriceItem] = useState('');
  const [priceQuery, setPriceQuery] = useState('');

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: queryKeys.expensesSummary(userId),
    queryFn: () => analyticsApi.expensesSummary(),
    enabled: activeTab === 'Spending',
  });

  const { data: predictions, isLoading: predLoading } = useQuery({
    queryKey: queryKeys.predictions(userId),
    queryFn: () => analyticsApi.predictions(),
    enabled: activeTab === 'Predictions',
  });

  const { data: bestStore, isLoading: priceLoading } = useQuery({
    queryKey: ['prices', 'best-store', priceQuery],
    queryFn: () => analyticsApi.bestStore(priceQuery),
    enabled: activeTab === 'Price Insights' && !!priceQuery,
  });

  const { data: storeCompare } = useQuery({
    queryKey: ['prices', 'compare', priceQuery],
    queryFn: () => analyticsApi.compareStores(priceQuery),
    enabled: activeTab === 'Price Insights' && !!priceQuery,
  });

  const s = summary as unknown as { current_month_total: number; previous_month_total: number; by_category: Array<{ category: string; total_spend: number }>; by_store: Array<{ store_name: string; total_spend: number }>; top_spend_items: Array<{ canonical_name: string; total_spend: number; purchase_count: number }> } | undefined;
  const pct = s ? formatPercentChange(s.current_month_total, s.previous_month_total) : null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics</h1>

      {/* Tabs */}
      <div className="flex gap-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-0.5 w-fit">
        {TABS.map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors
              ${activeTab === tab ? 'bg-sky-500 text-white' : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}>
            {tab}
          </button>
        ))}
      </div>

      {/* Spending Tab */}
      {activeTab === 'Spending' && (
        summaryLoading ? <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><SkeletonCard /><SkeletonCard /></div> : !s ? (
          <EmptyState title="No spending data" description="Upload receipts to see your spending analytics" />
        ) : (
          <div className="space-y-6">
            {/* Month comparison */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <p className="text-xs text-[var(--color-muted)] uppercase font-medium">This Month</p>
                <p className="text-3xl font-bold mt-1 text-sky-400">{formatCurrency(s.current_month_total)}</p>
              </Card>
              <Card>
                <p className="text-xs text-[var(--color-muted)] uppercase font-medium">Last Month</p>
                <p className="text-3xl font-bold mt-1">{formatCurrency(s.previous_month_total)}</p>
              </Card>
              <Card>
                <p className="text-xs text-[var(--color-muted)] uppercase font-medium">Change</p>
                <div className="flex items-center gap-2 mt-1">
                  {pct?.positive ? <TrendingDown size={20} className="text-green-400" /> : <TrendingUp size={20} className="text-red-400" />}
                  <p className={`text-3xl font-bold ${pct?.positive ? 'text-green-400' : 'text-red-400'}`}>{pct?.value}</p>
                </div>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* By Category donut */}
              <Card>
                <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-4">By Category</h3>
                {s.by_category?.length ? (
                  <div className="flex items-center gap-4">
                    <ResponsiveContainer width="50%" height={200}>
                      <PieChart>
                        <Pie data={s.by_category.map((c) => ({ name: c.category, value: c.total_spend }))} dataKey="value" nameKey="name"
                          cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2}>
                          {s.by_category.map((_, i) => <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />)}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f1f5f9' }}
                          formatter={(value: number) => formatCurrency(value)} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="space-y-1.5">
                      {s.by_category.map((c, i) => (
                        <div key={c.category} className="flex items-center gap-2 text-xs">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }} />
                          <span className="capitalize text-[var(--color-muted)]">{c.category}</span>
                          <span className="font-semibold ml-auto">{formatCurrency(c.total_spend)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : <p className="text-sm text-[var(--color-muted)] py-6 text-center">No data</p>}
              </Card>

              {/* By Store bar */}
              <Card>
                <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-4">By Store</h3>
                {s.by_store?.length ? (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={s.by_store}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="store_name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f1f5f9' }}
                        formatter={(value: number) => formatCurrency(value)} />
                      <Bar dataKey="total_spend" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : <p className="text-sm text-[var(--color-muted)] py-6 text-center">No data</p>}
              </Card>
            </div>

            {/* Top items table */}
            {s.top_spend_items?.length > 0 && (
              <Card>
                <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-4">Top Spend Items</h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-muted)] uppercase">
                      <th className="pb-2">Item</th><th className="pb-2">Total Spend</th><th className="pb-2">Purchases</th>
                    </tr>
                  </thead>
                  <tbody>
                    {s.top_spend_items.map((item) => (
                      <tr key={item.canonical_name} className="border-b border-[var(--color-border)]/50">
                        <td className="py-2 capitalize font-medium">{item.canonical_name}</td>
                        <td className="py-2" style={{ fontFamily: 'var(--font-mono)' }}>{formatCurrency(item.total_spend)}</td>
                        <td className="py-2 text-[var(--color-muted)]">{item.purchase_count}x</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            )}
          </div>
        )
      )}

      {/* Predictions Tab */}
      {activeTab === 'Predictions' && (
        predLoading ? <SkeletonCard /> : !(predictions as unknown as unknown[] | undefined)?.length ? (
          <EmptyState title="No predictions yet" description="Upload receipts and set up staples to see run-out predictions" />
        ) : (
          <Card>
            <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-5">Run-Out Timeline</h3>
            <div className="space-y-3">
              {(predictions as unknown as Array<{ canonical_name: string; estimated_days_left: number | null; predicted_run_out_date: string | null; status: string; current_quantity: number }>)
                ?.filter((p) => p.estimated_days_left != null)
                .sort((a, b) => (a.estimated_days_left ?? 999) - (b.estimated_days_left ?? 999))
                .map((p, i) => {
                  const days = p.estimated_days_left ?? 0;
                  const maxDays = 30;
                  const pct = Math.min(100, (days / maxDays) * 100);
                  const color = getStatusColor(p.status);
                  return (
                    <motion.div key={p.canonical_name} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}
                      className="flex items-center gap-4">
                      <span className="text-sm font-medium capitalize w-28 truncate">{p.canonical_name}</span>
                      <div className="flex-1 bg-[var(--color-surface-2)] rounded-full h-3 overflow-hidden">
                        <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.6, delay: i * 0.04 }}
                          className="h-full rounded-full" style={{ backgroundColor: color }} />
                      </div>
                      <span className="text-xs text-[var(--color-muted)] w-36 text-right">
                        {p.predicted_run_out_date ? `Runs out ${formatDate(p.predicted_run_out_date)}` : `${days.toFixed(1)}d left`}
                      </span>
                    </motion.div>
                  );
                })}
            </div>
            {(predictions as unknown as Array<{ estimated_days_left: number | null; canonical_name: string }>)?.some((p) => p.estimated_days_left == null) && (
              <div className="mt-6 pt-4 border-t border-[var(--color-border)]">
                <h4 className="text-xs font-semibold text-[var(--color-muted)] uppercase mb-2">No Consumption Data</h4>
                <div className="flex flex-wrap gap-1.5">
                  {(predictions as unknown as Array<{ estimated_days_left: number | null; canonical_name: string }>)
                    ?.filter((p) => p.estimated_days_left == null)
                    .map((p) => (
                      <span key={p.canonical_name} className="px-2 py-0.5 bg-[var(--color-surface-2)] rounded text-xs capitalize">{p.canonical_name}</span>
                    ))}
                </div>
              </div>
            )}
          </Card>
        )
      )}

      {/* Price Insights Tab */}
      {activeTab === 'Price Insights' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-muted)]" />
              <input value={priceItem} onChange={(e) => setPriceItem(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && setPriceQuery(priceItem.toLowerCase().replace(/\s+/g, '_'))}
                placeholder="Search item (e.g. milk, eggs)" 
                className="w-full pl-9 pr-4 py-2.5 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500" />
            </div>
            <button onClick={() => setPriceQuery(priceItem.toLowerCase().replace(/\s+/g, '_'))}
              className="px-4 py-2.5 bg-sky-500 hover:bg-sky-600 text-white rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5">
              Compare <ArrowRight size={14} />
            </button>
          </div>

          {priceLoading && <SkeletonCard />}

          {bestStore && !priceLoading && (
            <div className="space-y-4">
              {(bestStore as unknown as { best_store: string | null }).best_store ? (
                <Card className="border-green-500/20 bg-gradient-to-r from-green-500/5 to-transparent">
                  <p className="text-xs text-green-400 uppercase font-semibold mb-1">🏆 Best Store</p>
                  <p className="text-2xl font-bold capitalize">{(bestStore as unknown as { best_store: string }).best_store}</p>
                  <p className="text-sm text-[var(--color-muted)] mt-1">{(bestStore as unknown as { insight: string }).insight}</p>
                </Card>
              ) : (
                <Card><p className="text-sm text-[var(--color-muted)]">{(bestStore as unknown as { insight: string }).insight}</p></Card>
              )}

              {(storeCompare as unknown as { stores?: Array<{ store_name: string; avg_unit_price: number; samples: number; last_seen: string }> })?.stores?.length ? (
                <Card>
                  <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-4">Store Comparison</h3>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-muted)] uppercase">
                        <th className="pb-2">Store</th><th className="pb-2">Avg Unit Price</th><th className="pb-2">Samples</th><th className="pb-2">Last Seen</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(storeCompare as unknown as { stores: Array<{ store_name: string; avg_unit_price: number; samples: number; last_seen: string }> }).stores.map((s) => (
                        <tr key={s.store_name} className="border-b border-[var(--color-border)]/50">
                          <td className="py-2 capitalize font-medium">{s.store_name}</td>
                          <td className="py-2" style={{ fontFamily: 'var(--font-mono)' }}>{formatCurrency(s.avg_unit_price)}</td>
                          <td className="py-2 text-[var(--color-muted)]">{s.samples}</td>
                          <td className="py-2 text-[var(--color-muted)]">{s.last_seen ? formatDate(s.last_seen) : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Card>
              ) : null}
            </div>
          )}

          {!priceQuery && !priceLoading && (
            <EmptyState icon={Search} title="Search for an item" description="Enter an item name to compare prices across stores" />
          )}
        </div>
      )}
    </div>
  );
}
