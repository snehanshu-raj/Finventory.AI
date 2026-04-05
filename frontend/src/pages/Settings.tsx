import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Mail, RefreshCw, Check, Zap } from 'lucide-react';
import { gmailApi, type SyncRun } from '@/api/gmail';
import { usersApi } from '@/api/users';
import { useUserStore } from '@/store/userStore';
import { queryKeys, UNIT_OPTIONS } from '@/utils/constants';
import { formatRelative, formatDateTime } from '@/utils/formatters';
import { Card } from '@/components/ui/Card';
import { SkeletonCard, SkeletonRow } from '@/components/ui/Skeleton';
import toast from 'react-hot-toast';

const TABS = ['Gmail', 'Staples', 'Preferences'] as const;

export default function Settings() {
  const userId = useUserStore((s) => s.userId) ?? '';
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<typeof TABS[number]>('Gmail');

  // Gmail
  const { data: gmailStatus, isLoading: gmailLoading } = useQuery({
    queryKey: queryKeys.gmailStatus(userId),
    queryFn: () => gmailApi.status(),
  });

  const { data: syncRuns, isLoading: runsLoading } = useQuery({
    queryKey: queryKeys.gmailSyncRuns(userId),
    queryFn: () => gmailApi.syncRuns(10),
  });

  const syncMutation = useMutation({
    mutationFn: (daysBack: number) => gmailApi.sync(daysBack),
    onSuccess: (data) => {
      const d = data as unknown as { messages_found: number; messages_stored: number };
      toast.success(`Synced! Found ${d.messages_found} emails, stored ${d.messages_stored} expenses.`);
      queryClient.invalidateQueries({ queryKey: queryKeys.gmailSyncRuns(userId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.gmailStatus(userId) });
    },
  });

  // User profile & staples
  const { data: userProfile, isLoading: userLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => usersApi.getUser(),
    enabled: activeTab === 'Staples' || activeTab === 'Preferences',
  });

  const profile = userProfile as unknown as {
    diet_profile?: { staples?: Array<{ canonical_item_id: string; canonical_name: string; daily_consumption_estimate: number; unit: string; threshold_quantity: number }> };
    preferences?: { currency: string; notification_enabled: boolean; notification_channels: string[] };
  } | undefined;

  const [editStaples, setEditStaples] = useState<Array<{ canonical_item_id: string; canonical_name: string; daily_consumption_estimate: number; unit: string; threshold_quantity: number }> | null>(null);

  const staplesMutation = useMutation({
    mutationFn: (staples: Array<{ canonical_item_id: string; canonical_name: string; daily_consumption_estimate: number; unit: string; threshold_quantity: number }>) =>
      usersApi.updateStaples(staples),
    onSuccess: () => {
      toast.success('Staples updated!');
      queryClient.invalidateQueries({ queryKey: ['user', userId] });
      setEditStaples(null);
    },
  });

  const gs = gmailStatus as unknown as { connected: boolean; email?: string; last_synced_at?: string } | undefined;
  const runs = (syncRuns as unknown as SyncRun[] | undefined) ?? [];

  return (
    <div className="space-y-8 pb-8">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">Settings</h1>
        <p className="text-[var(--color-text-secondary)] mt-2">Manage your account and integrations</p>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-1 bg-[var(--color-surface)]/50 border border-[var(--color-border)] rounded-lg p-1 w-fit">
        {TABS.map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all
              ${activeTab === tab ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/20' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'}`}>
            {tab}
          </button>
        ))}
      </div>

      {/* Gmail Tab */}
      {activeTab === 'Gmail' && (
        <div className="space-y-4">
          {gmailLoading ? <SkeletonCard /> : (
            <Card className="border-sky-500/20">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-sky-500/10 flex items-center justify-center">
                  <Mail size={24} className="text-sky-400" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">Gmail Integration</h3>
                    <span className="flex items-center gap-1 px-2 py-0.5 bg-green-500/10 text-green-400 rounded text-[10px] font-semibold">
                      <Check size={10} /> Connected
                    </span>
                  </div>
                  {gs?.email && <p className="text-sm text-[var(--color-muted)]">{gs.email}</p>}
                  <p className="text-xs text-[var(--color-muted)]">
                    Last synced: {gs?.last_synced_at ? formatRelative(gs.last_synced_at) : 'Never'}
                  </p>
                </div>
                <button onClick={() => syncMutation.mutate(7)} disabled={syncMutation.isPending}
                  className="flex items-center gap-1.5 px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50">
                  <RefreshCw size={14} className={syncMutation.isPending ? 'animate-spin' : ''} />
                  {syncMutation.isPending ? 'Syncing...' : 'Sync Now'}
                </button>
              </div>
            </Card>
          )}

          {/* Sync History */}
          <Card>
            <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-4">Sync History</h3>
            {runsLoading ? (
              <div className="space-y-2">{[...Array(3)].map((_, i) => <SkeletonRow key={i} />)}</div>
            ) : runs.length === 0 ? (
              <p className="text-sm text-[var(--color-muted)] py-4 text-center">No sync runs yet</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-muted)] uppercase">
                      <th className="pb-2 pr-3">Started</th><th className="pb-2 pr-3">Status</th><th className="pb-2 pr-3">Found</th>
                      <th className="pb-2 pr-3">Parsed</th><th className="pb-2">Errors</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map((run) => (
                      <tr key={run.id || run.started_at} className="border-b border-[var(--color-border)]/50">
                        <td className="py-2 pr-3 text-xs">{run.started_at ? formatDateTime(run.started_at) : '—'}</td>
                        <td className="py-2 pr-3">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium
                            ${run.status === 'completed' ? 'bg-green-500/10 text-green-400' : run.status === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'}`}>
                            {run.status}
                          </span>
                        </td>
                        <td className="py-2 pr-3">{run.messages_found}</td>
                        <td className="py-2 pr-3">{run.messages_parsed}</td>
                        <td className="py-2 text-xs text-red-400">{run.errors?.length ? run.errors.length : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Staples Tab */}
      {activeTab === 'Staples' && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase">Staple Configuration</h3>
            {!editStaples ? (
              <button onClick={() => setEditStaples(profile?.diet_profile?.staples ?? [])}
                className="text-sm text-sky-400 hover:text-sky-300 font-medium">Edit</button>
            ) : (
              <div className="flex gap-2">
                <button onClick={() => setEditStaples(null)} className="text-sm text-[var(--color-muted)] hover:text-[var(--color-text)]">Cancel</button>
                <button onClick={() => editStaples && staplesMutation.mutate(editStaples)} disabled={staplesMutation.isPending}
                  className="text-sm text-sky-400 hover:text-sky-300 font-medium">Save</button>
              </div>
            )}
          </div>

          {userLoading ? (
            <div className="space-y-2">{[...Array(3)].map((_, i) => <SkeletonRow key={i} />)}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-muted)] uppercase">
                    <th className="pb-2">Item</th><th className="pb-2">Daily</th><th className="pb-2">Unit</th><th className="pb-2">Threshold</th>
                  </tr>
                </thead>
                <tbody>
                  {(editStaples ?? profile?.diet_profile?.staples ?? []).map((s, i) => (
                    <tr key={s.canonical_item_id || i} className="border-b border-[var(--color-border)]/50">
                      <td className="py-2 capitalize font-medium">{s.canonical_name}</td>
                      <td className="py-2">
                        {editStaples ? (
                          <input type="number" step="0.01" value={s.daily_consumption_estimate}
                            onChange={(e) => setEditStaples((prev) => prev!.map((item, idx) => idx === i ? { ...item, daily_consumption_estimate: parseFloat(e.target.value) || 0 } : item))}
                            className="w-20 px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm outline-none" />
                        ) : s.daily_consumption_estimate}
                      </td>
                      <td className="py-2">
                        {editStaples ? (
                          <select value={s.unit}
                            onChange={(e) => setEditStaples((prev) => prev!.map((item, idx) => idx === i ? { ...item, unit: e.target.value } : item))}
                            className="px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm outline-none">
                            {UNIT_OPTIONS.map((u) => <option key={u} value={u}>{u}</option>)}
                          </select>
                        ) : s.unit}
                      </td>
                      <td className="py-2">
                        {editStaples ? (
                          <input type="number" step="0.1" value={s.threshold_quantity}
                            onChange={(e) => setEditStaples((prev) => prev!.map((item, idx) => idx === i ? { ...item, threshold_quantity: parseFloat(e.target.value) || 0 } : item))}
                            className="w-20 px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm outline-none" />
                        ) : s.threshold_quantity}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Preferences Tab */}
      {activeTab === 'Preferences' && (
        <Card>
          <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-4">Preferences</h3>
          {userLoading ? <SkeletonCard /> : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5">Currency</label>
                <p className="text-sm text-[var(--color-muted)]">{profile?.preferences?.currency ?? 'USD'}</p>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Notifications</span>
                <span className={`text-sm font-medium ${profile?.preferences?.notification_enabled ? 'text-green-400' : 'text-red-400'}`}>
                  {profile?.preferences?.notification_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">Channels</label>
                <div className="flex gap-2">
                  {(profile?.preferences?.notification_channels ?? []).map((ch) => (
                    <span key={ch} className="px-2 py-0.5 bg-sky-500/10 text-sky-400 rounded text-xs font-medium">{ch}</span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
