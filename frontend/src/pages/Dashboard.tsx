import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { DollarSign, AlertTriangle, Clock, Store, Receipt, Mail, RefreshCw, TrendingUp, Zap } from 'lucide-react';
import { analyticsApi } from '@/api/analytics';
import { receiptsApi } from '@/api/receipts';
import { gmailApi } from '@/api/gmail';
import { useUserStore } from '@/store/userStore';
import { queryKeys } from '@/utils/constants';
import { formatCurrency, formatDate, formatRelative } from '@/utils/formatters';
import { Card } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line } from 'recharts';
import toast from 'react-hot-toast';

const STATUS_COLORS: Record<string, string> = { ok: '#10b981', low: '#f59e0b', critical: '#f97316', out_of_stock: '#ef4444' };

export default function Dashboard() {
  const userId = useUserStore((s) => s.userId) ?? '';
  const navigate = useNavigate();

  const { data: dashboard, isLoading } = useQuery({
    queryKey: queryKeys.dashboard(userId),
    queryFn: () => analyticsApi.dashboard(),
    refetchInterval: 60_000,
  });

  const { data: receipts } = useQuery({
    queryKey: queryKeys.receipts(userId, { page: 1 }),
    queryFn: () => receiptsApi.list({ page: 1, page_size: 3 }),
  });

  const { data: gmailStatus } = useQuery({
    queryKey: queryKeys.gmailStatus(userId),
    queryFn: () => gmailApi.status(),
  });

  const { data: inventory } = useQuery({
    queryKey: [...queryKeys.inventory(userId), 'status-counts'],
    queryFn: async () => {
      const { inventoryApi } = await import('@/api/inventory');
      const items = await inventoryApi.list();
      const counts = { ok: 0, low: 0, critical: 0, out_of_stock: 0 };
      (items as unknown as Array<{ status: string }>).forEach((item) => {
        const s = item.status as keyof typeof counts;
        if (s in counts) counts[s]++;
      });
      return counts;
    },
  });

  const handleSync = async () => {
    try {
      console.log('Starting Gmail sync with days_back=0...');
      const result = await gmailApi.sync(0);
      console.log('Gmail sync result:', result);
      toast.success('Gmail synced!');
    } catch (err) {
      console.error('Gmail sync failed:', err);
      /* error handled by interceptor */
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Dashboard</h1>
          <p className="text-[var(--color-text-secondary)] mt-2">Welcome back, here's your financial overview</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonCard /><SkeletonCard />
        </div>
      </div>
    );
  }

  const kpis = [
    { icon: DollarSign, label: 'Monthly Spend', value: formatCurrency(dashboard?.monthly_spend ?? 0), color: 'text-blue-400', bg: 'from-blue-500/20 to-blue-500/5', iconBg: 'bg-blue-500/20' },
    { icon: AlertTriangle, label: 'Low Stock Items', value: String(dashboard?.low_stock_count ?? 0), color: dashboard?.low_stock_count ? 'text-orange-400' : 'text-green-400', bg: dashboard?.low_stock_count ? 'from-orange-500/20 to-orange-500/5' : 'from-green-500/20 to-green-500/5', iconBg: dashboard?.low_stock_count ? 'bg-orange-500/20' : 'bg-green-500/20' },
    { icon: Clock, label: 'Running Out (7d)', value: String(dashboard?.items_running_out_7days?.length ?? 0), color: 'text-yellow-400', bg: 'from-yellow-500/20 to-yellow-500/5', iconBg: 'bg-yellow-500/20' },
    { icon: Store, label: 'Top Store', value: dashboard?.top_stores?.[0]?.store_name ?? 'N/A', color: 'text-cyan-400', bg: 'from-cyan-500/20 to-cyan-500/5', iconBg: 'bg-cyan-500/20' },
  ];

  const donutData = inventory
    ? Object.entries(inventory).filter(([, v]) => v > 0).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="space-y-8 pb-8">
      {/* Page Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">Dashboard</h1>
        <p className="text-[var(--color-text-secondary)] mt-2">Welcome back, here's your financial overview</p>
      </motion.div>

      {/* KPI Strip */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {kpis.map((kpi, i) => (
          <motion.div key={kpi.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
            <Card hover gradient>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide">{kpi.label}</p>
                  <p className={`text-3xl font-bold mt-2 ${kpi.color}`}>{kpi.value}</p>
                </div>
                <div className={`w-12 h-12 rounded-xl ${kpi.iconBg} flex items-center justify-center flex-shrink-0 ml-3`}>
                  <kpi.icon size={24} className={kpi.color} strokeWidth={2} />
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spending by Store */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
          <Card gradient>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide">Spending Breakdown</h2>
                <p className="text-xs text-[var(--color-muted)] mt-1">Expenses by store</p>
              </div>
              <Zap size={18} className="text-yellow-400" />
            </div>
            {dashboard?.top_stores?.length ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={dashboard.top_stores}>
                  <defs>
                    <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3b82f6" stopOpacity={1} />
                      <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.2} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="store_name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '8px', color: '#f1f5f9' }} />
                  <Bar dataKey="total_spend" fill="url(#barGradient)" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-[var(--color-muted)] py-16 text-center">No spending data yet</p>
            )}
          </Card>
        </motion.div>

        {/* Inventory Donut */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
          <Card gradient>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide">Inventory Health</h2>
                <p className="text-xs text-[var(--color-muted)] mt-1">Status distribution</p>
              </div>
              <TrendingUp size={18} className="text-green-400" />
            </div>
            {donutData.length ? (
              <div className="flex items-center gap-8">
                <ResponsiveContainer width="40%" height={180}>
                  <PieChart>
                    <Pie data={donutData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={4}>
                      {donutData.map((d) => <Cell key={d.name} fill={STATUS_COLORS[d.name] ?? '#94a3b8'} />)}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex-1 space-y-3">
                  {donutData.map((d) => (
                    <div key={d.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: STATUS_COLORS[d.name] }} />
                        <span className="capitalize text-sm text-[var(--color-text-secondary)] font-500">{d.name.replace('_', ' ')}</span>
                      </div>
                      <span className="text-sm font-semibold">{d.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-[var(--color-muted)] py-16 text-center">Upload a receipt to see inventory status</p>
            )}
          </Card>
        </motion.div>
      </div>

      {/* Running Out */}
      {dashboard?.items_running_out_7days?.length ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}>
          <Card gradient>
            <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide mb-6">⏰ Items Running Out Soon (7 Days)</h2>
            <div className="space-y-4">
              {dashboard.items_running_out_7days.slice(0, 5).map((item) => {
                const pct = Math.min(100, Math.max(0, ((item.estimated_days_left ?? 0) / 7) * 100));
                return (
                  <div key={item.canonical_name} className="flex items-center gap-4 group">
                    <span className="text-sm font-semibold capitalize w-40 truncate group-hover:text-blue-400 transition-colors">{item.canonical_name}</span>
                    <div className="flex-1 bg-[var(--color-surface-2)]/50 rounded-full h-2.5 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: STATUS_COLORS[item.status] ?? '#94a3b8' }}
                        transition={{ duration: 0.6 }}
                      />
                    </div>
                    <span className="text-xs text-[var(--color-muted)] w-24 text-right font-medium">
                      {item.estimated_days_left != null ? `${item.estimated_days_left.toFixed(1)}d` : 'N/A'}
                    </span>
                    <StatusBadge status={item.status} size="sm" />
                  </div>
                );
              })}
            </div>
          </Card>
        </motion.div>
      ) : null}

      {/* Recent Receipts */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}>
        <Card gradient>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide">Recent Receipts</h2>
              <p className="text-xs text-[var(--color-muted)] mt-1">Latest uploads</p>
            </div>
            <button onClick={() => navigate('/receipts')} className="text-sm font-semibold text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">
              View All <span>→</span>
            </button>
          </div>
          {receipts?.items?.length ? (
            <div className="space-y-2">
              {receipts.items.map((r) => (
                <motion.div 
                  key={r.id} 
                  className="flex items-center justify-between p-4 bg-[var(--color-surface)]/50 hover:bg-[var(--color-surface)]/80 rounded-lg transition-all duration-200 cursor-pointer group"
                  onClick={() => navigate(`/receipts`)}
                  whileHover={{ x: 4 }}
                >
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/30 to-purple-500/30 flex items-center justify-center flex-shrink-0">
                      <Receipt size={18} className="text-blue-400" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold group-hover:text-blue-400 transition-colors">{r.merchant_name}</p>
                      <p className="text-xs text-[var(--color-muted)]">{formatDate(r.purchased_at)} • {r.item_count} items</p>
                    </div>
                  </div>
                  <span className="text-sm font-bold mr-2">{formatCurrency(r.total)}</span>
                </motion.div>
              ))}
            </div>
          ) : (
            <EmptyState icon={Receipt} title="No receipts yet" description="Upload your first receipt to get started" />
          )}
        </Card>
      </motion.div>

      {/* Gmail Sync Banner */}
      {(gmailStatus as unknown as { connected: boolean })?.connected && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}>
          <Card gradient className="border-blue-500/30 bg-gradient-to-r from-blue-500/10 via-purple-500/5 to-blue-500/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500/30 to-purple-500/30 flex items-center justify-center flex-shrink-0">
                  <Mail size={22} className="text-blue-400" />
                </div>
                <div>
                  <p className="text-sm font-semibold">Gmail Connected</p>
                  <p className="text-xs text-[var(--color-muted)]">
                    Last synced {(gmailStatus as unknown as { last_synced_at?: string }).last_synced_at ? formatRelative((gmailStatus as unknown as { last_synced_at: string }).last_synced_at) : 'never'}
                  </p>
                </div>
              </div>
              <motion.button 
                onClick={handleSync}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 hover:from-blue-500/30 hover:to-purple-500/30 rounded-lg text-sm font-semibold transition-all"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <RefreshCw size={16} /> Sync Now
              </motion.button>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
