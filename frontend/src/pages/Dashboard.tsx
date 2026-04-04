import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { DollarSign, AlertTriangle, Clock, Store, Receipt, Mail, RefreshCw } from 'lucide-react';
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
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import toast from 'react-hot-toast';

const STATUS_COLORS: Record<string, string> = { ok: '#22c55e', low: '#facc15', critical: '#f97316', out_of_stock: '#ef4444' };

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
      await gmailApi.sync(0);
      toast.success('Gmail synced!');
    } catch { /* error handled by interceptor */ }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonCard /><SkeletonCard />
        </div>
      </div>
    );
  }

  const kpis = [
    { icon: DollarSign, label: 'Monthly Spend', value: formatCurrency(dashboard?.monthly_spend ?? 0), color: 'text-sky-400', bg: 'bg-sky-500/10' },
    { icon: AlertTriangle, label: 'Low Stock Items', value: String(dashboard?.low_stock_count ?? 0), color: dashboard?.low_stock_count ? 'text-orange-400' : 'text-green-400', bg: dashboard?.low_stock_count ? 'bg-orange-500/10' : 'bg-green-500/10' },
    { icon: Clock, label: 'Running Out (7d)', value: String(dashboard?.items_running_out_7days?.length ?? 0), color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
    { icon: Store, label: 'Top Store', value: dashboard?.top_stores?.[0]?.store_name ?? 'N/A', color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
  ];

  const donutData = inventory
    ? Object.entries(inventory).filter(([, v]) => v > 0).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, i) => (
          <motion.div key={kpi.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
            <Card hover>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wide">{kpi.label}</p>
                  <p className={`text-2xl font-bold mt-1 ${kpi.color}`}>{kpi.value}</p>
                </div>
                <div className={`w-10 h-10 rounded-xl ${kpi.bg} flex items-center justify-center`}>
                  <kpi.icon size={20} className={kpi.color} />
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Spending by Store */}
        <Card>
          <h2 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-4">Spending by Store</h2>
          {dashboard?.top_stores?.length ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={dashboard.top_stores}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="store_name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f1f5f9' }} />
                <Bar dataKey="total_spend" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-[var(--color-muted)] py-8 text-center">No spending data yet</p>
          )}
        </Card>

        {/* Inventory Donut */}
        <Card>
          <h2 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-4">Inventory Status</h2>
          {donutData.length ? (
            <div className="flex items-center gap-6">
              <ResponsiveContainer width="50%" height={180}>
                <PieChart>
                  <Pie data={donutData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3}>
                    {donutData.map((d) => <Cell key={d.name} fill={STATUS_COLORS[d.name] ?? '#94a3b8'} />)}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f1f5f9' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2">
                {donutData.map((d) => (
                  <div key={d.name} className="flex items-center gap-2 text-sm">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: STATUS_COLORS[d.name] }} />
                    <span className="capitalize text-[var(--color-muted)]">{d.name.replace('_', ' ')}</span>
                    <span className="font-semibold">{d.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-[var(--color-muted)] py-8 text-center">Upload a receipt to see inventory status</p>
          )}
        </Card>
      </div>

      {/* Running Out */}
      {dashboard?.items_running_out_7days?.length ? (
        <Card>
          <h2 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-4">⏰ Items Running Out Soon</h2>
          <div className="space-y-3">
            {dashboard.items_running_out_7days.map((item) => {
              const pct = Math.min(100, Math.max(0, ((item.estimated_days_left ?? 0) / 7) * 100));
              return (
                <div key={item.canonical_name} className="flex items-center gap-4">
                  <span className="text-sm font-medium capitalize w-32 truncate">{item.canonical_name}</span>
                  <div className="flex-1 bg-[var(--color-surface-2)] rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: STATUS_COLORS[item.status] ?? '#94a3b8' }}
                    />
                  </div>
                  <span className="text-xs text-[var(--color-muted)] w-20 text-right">
                    {item.estimated_days_left != null ? `${item.estimated_days_left.toFixed(1)}d left` : 'Unknown'}
                  </span>
                  <StatusBadge status={item.status} size="sm" />
                </div>
              );
            })}
          </div>
        </Card>
      ) : null}

      {/* Recent Receipts */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-[var(--color-muted)] uppercase">Recent Receipts</h2>
          <button onClick={() => navigate('/receipts')} className="text-xs text-sky-400 hover:text-sky-300 font-medium">View All →</button>
        </div>
        {receipts?.items?.length ? (
          <div className="space-y-2">
            {receipts.items.map((r) => (
              <div key={r.id} className="flex items-center justify-between p-3 bg-[var(--color-bg)] rounded-lg hover:bg-[var(--color-surface-2)]/30 transition-colors cursor-pointer"
                onClick={() => navigate(`/receipts`)}>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-sky-500/10 flex items-center justify-center">
                    <Receipt size={16} className="text-sky-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{r.merchant_name}</p>
                    <p className="text-xs text-[var(--color-muted)]">{formatDate(r.purchased_at)} • {r.item_count} items</p>
                  </div>
                </div>
                <span className="text-sm font-semibold">{formatCurrency(r.total)}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={Receipt} title="No receipts yet" description="Upload your first receipt to get started" />
        )}
      </Card>

      {/* Gmail Sync Banner */}
      {(gmailStatus as unknown as { connected: boolean })?.connected && (
        <Card className="border-sky-500/20 bg-gradient-to-r from-sky-500/5 to-transparent">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-sky-500/10 flex items-center justify-center">
                <Mail size={20} className="text-sky-400" />
              </div>
              <div>
                <p className="text-sm font-semibold">Gmail Connected</p>
                <p className="text-xs text-[var(--color-muted)]">
                  Last synced {(gmailStatus as unknown as { last_synced_at?: string }).last_synced_at ? formatRelative((gmailStatus as unknown as { last_synced_at: string }).last_synced_at) : 'never'}
                </p>
              </div>
            </div>
            <button onClick={handleSync}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-sky-500/10 text-sky-400 hover:bg-sky-500/20 rounded-lg text-sm font-medium transition-colors">
              <RefreshCw size={14} /> Sync Now
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}
