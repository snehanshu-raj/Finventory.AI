import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Bell, BarChart3, Plus, X } from 'lucide-react';
import { notificationsApi, type NotificationItem } from '@/api/notifications';
import { useUserStore } from '@/store/userStore';
import { useUIStore } from '@/store/uiStore';
import { queryKeys } from '@/utils/constants';
import { formatRelative } from '@/utils/formatters';

import { SkeletonRow } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';
import toast from 'react-hot-toast';

const FILTERS = ['all', 'low_stock', 'weekly_summary', 'unread'] as const;

export default function Notifications() {
  const userId = useUserStore((s) => s.userId) ?? '';
  const queryClient = useQueryClient();
  const openModal = useUIStore((s) => s.openModal);
  const closeModal = useUIStore((s) => s.closeModal);
  const [filter, setFilter] = useState<string>('all');
  const [testTitle, setTestTitle] = useState('');
  const [testMessage, setTestMessage] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.notifications(userId),
    queryFn: () => notificationsApi.list({ page: 1, page_size: 50 }),
    refetchInterval: 30_000,
  });

  const dismissMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.dismiss(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.notifications(userId) });
      const prev = queryClient.getQueryData(queryKeys.notifications(userId));
      queryClient.setQueryData(queryKeys.notifications(userId), (old: unknown) => {
        const o = old as { items: NotificationItem[] } | undefined;
        if (!o) return old;
        return { ...o, items: o.items.filter((n) => n.id !== id) };
      });
      return { prev };
    },
    onError: (_err, _id, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(queryKeys.notifications(userId), ctx.prev);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: queryKeys.notifications(userId) }),
  });

  const testMutation = useMutation({
    mutationFn: () => notificationsApi.test({ user_id: userId, title: testTitle, message: testMessage }),
    onSuccess: () => {
      toast.success('Test notification sent!');
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications(userId) });
      closeModal();
      setTestTitle('');
      setTestMessage('');
    },
  });

  const items = (data as unknown as { items?: NotificationItem[] })?.items ?? [];
  const filtered = filter === 'all' ? items
    : filter === 'unread' ? items.filter((n) => n.status !== 'dismissed')
    : items.filter((n) => n.type === filter);

  const typeIcon = (type: string) => {
    switch (type) {
      case 'low_stock': return <Bell size={16} className="text-orange-400" />;
      case 'weekly_summary': return <BarChart3 size={16} className="text-sky-400" />;
      default: return <Bell size={16} className="text-[var(--color-muted)]" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Notifications</h1>
        <button onClick={() => openModal('test-notification')}
          className="flex items-center gap-1.5 px-3 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-sm font-medium hover:bg-[var(--color-surface-2)] transition-colors">
          <Plus size={14} /> Test Notification
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-0.5 w-fit">
        {FILTERS.map((f) => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-colors
              ${filter === f ? 'bg-sky-500 text-white' : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'}`}>
            {f.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* List */}
      {isLoading ? (
        <div className="space-y-2">{[...Array(5)].map((_, i) => <SkeletonRow key={i} />)}</div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={Bell} title="No notifications" description="You're all caught up! Notifications will appear here when items run low." />
      ) : (
        <div className="space-y-2">
          {filtered.map((n, i) => (
            <motion.div key={n.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }} transition={{ delay: i * 0.02 }}
              className="flex items-start gap-3 p-4 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl">
              <div className="w-9 h-9 rounded-lg bg-[var(--color-surface-2)] flex items-center justify-center shrink-0 mt-0.5">
                {typeIcon(n.type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold">{n.title}</p>
                <p className="text-xs text-[var(--color-muted)] mt-0.5">{n.message}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-[10px] text-[var(--color-muted)]">{n.created_at ? formatRelative(n.created_at) : ''}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium
                    ${n.status === 'dismissed' ? 'bg-[var(--color-surface-2)] text-[var(--color-muted)]' : 'bg-sky-500/10 text-sky-400'}`}>
                    {n.status}
                  </span>
                </div>
              </div>
              {n.status !== 'dismissed' && (
                <button onClick={() => dismissMutation.mutate(n.id)} aria-label="Dismiss notification"
                  className="p-1.5 hover:bg-[var(--color-surface-2)] rounded-lg transition-colors shrink-0">
                  <X size={14} className="text-[var(--color-muted)]" />
                </button>
              )}
            </motion.div>
          ))}
        </div>
      )}

      {/* Test Notification Modal */}
      <Modal id="test-notification" title="Send Test Notification">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5">Title</label>
            <input value={testTitle} onChange={(e) => setTestTitle(e.target.value)}
              className="w-full px-4 py-2.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Message</label>
            <textarea value={testMessage} onChange={(e) => setTestMessage(e.target.value)} rows={3}
              className="w-full px-4 py-2.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500 resize-none" />
          </div>
          <button onClick={() => testMutation.mutate()} disabled={testMutation.isPending || !testTitle}
            className="w-full py-2.5 bg-sky-500 hover:bg-sky-600 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50">
            {testMutation.isPending ? 'Sending...' : 'Send Notification'}
          </button>
        </div>
      </Modal>
    </div>
  );
}
