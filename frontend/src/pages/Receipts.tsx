import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';
import { Upload, Image, FileText, ChevronRight, AlertCircle, Check } from 'lucide-react';
import { receiptsApi, type Receipt, type ReceiptListItem } from '@/api/receipts';
import { useUserStore } from '@/store/userStore';
import { queryKeys } from '@/utils/constants';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { Card } from '@/components/ui/Card';
import { SkeletonRow } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import toast from 'react-hot-toast';

const confidenceBadge = (confidence: number) => {
  if (confidence >= 0.9) return <span className="text-[10px] px-1.5 py-0.5 bg-green-500/10 text-green-400 rounded font-medium">High</span>;
  if (confidence >= 0.8) return <span className="text-[10px] px-1.5 py-0.5 bg-yellow-500/10 text-yellow-400 rounded font-medium">Med</span>;
  return <span className="text-[10px] px-1.5 py-0.5 bg-orange-500/10 text-orange-400 rounded font-medium flex items-center gap-0.5"><AlertCircle size={10} /> Review</span>;
};

const ReceiptDetail = ({ receipt }: { receipt: Receipt }) => (
  <Card>
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="font-semibold text-lg">{receipt.merchant?.name ?? 'Unknown'}</h3>
        {receipt.merchant?.address && <p className="text-xs text-[var(--color-muted)]">{receipt.merchant.address}</p>}
      </div>
      <div className="text-right">
        <p className="text-xl font-bold text-sky-400">{formatCurrency(receipt.transaction?.total ?? 0)}</p>
        <p className="text-xs text-[var(--color-muted)]">{receipt.transaction?.purchased_at ? formatDate(receipt.transaction.purchased_at) : ''}</p>
      </div>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-muted)] uppercase">
            <th className="pb-2 pr-3">Raw Text</th><th className="pb-2 pr-3">Name</th><th className="pb-2 pr-3">Qty</th>
            <th className="pb-2 pr-3">Price</th><th className="pb-2">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {receipt.items?.map((item, i) => (
            <tr key={i} className="border-b border-[var(--color-border)]/50">
              <td className="py-2 pr-3 text-[var(--color-muted)] text-xs">{item.raw_text}</td>
              <td className="py-2 pr-3 capitalize font-medium">{item.canonical_name}</td>
              <td className="py-2 pr-3" style={{ fontFamily: 'var(--font-mono)' }}>{item.quantity} {item.unit}</td>
              <td className="py-2 pr-3" style={{ fontFamily: 'var(--font-mono)' }}>{formatCurrency(item.line_price)}</td>
              <td className="py-2">{confidenceBadge(item.confidence)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    <div className="flex items-center gap-4 mt-4 pt-3 border-t border-[var(--color-border)] text-xs text-[var(--color-muted)]">
      <span>Subtotal: {formatCurrency(receipt.transaction?.subtotal ?? 0)}</span>
      <span>Tax: {formatCurrency(receipt.transaction?.tax ?? 0)}</span>
      <span className="font-semibold text-[var(--color-text)]">Total: {formatCurrency(receipt.transaction?.total ?? 0)}</span>
    </div>
  </Card>
);

export default function Receipts() {
  const userId = useUserStore((s) => s.userId) ?? '';
  const queryClient = useQueryClient();
  const [uploadedReceipt, setUploadedReceipt] = useState<Receipt | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [selectedReceipt, setSelectedReceipt] = useState<Receipt | null>(null);
  const [page, setPage] = useState(1);
  const [monthFilter, setMonthFilter] = useState('');
  const [storeFilter, setStoreFilter] = useState('');

  const { data: receiptList, isLoading: listLoading } = useQuery({
    queryKey: queryKeys.receipts(userId, { page, month: monthFilter, store: storeFilter }),
    queryFn: () => receiptsApi.list({ page, page_size: 10, month: monthFilter || undefined, store: storeFilter || undefined }),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => receiptsApi.upload(userId, file),
    onSuccess: (data) => {
      setUploadedReceipt(data as unknown as Receipt);
      queryClient.invalidateQueries({ queryKey: ['receipts'] });
      const itemCount = (data as unknown as Receipt).items?.length ?? 0;
      toast.success(`Receipt scanned! ${itemCount} items found 🎉`);
    },
  });

  const onDrop = useCallback((files: File[]) => {
    const file = files[0];
    if (!file) return;
    setPreviewUrl(URL.createObjectURL(file));
    setUploadedReceipt(null);
    uploadMutation.mutate(file);
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/jpeg': [], 'image/png': [] },
    maxSize: 10 * 1024 * 1024,
    multiple: false,
  });

  const loadReceipt = async (id: string) => {
    try {
      const data = await receiptsApi.get(id);
      setSelectedReceipt(data as unknown as Receipt);
    } catch { /* handled */ }
  };


  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Receipts</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Upload */}
        <div className="space-y-4">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200
              ${isDragActive ? 'border-sky-400 bg-sky-500/5' : 'border-[var(--color-border)] hover:border-sky-400/50 hover:bg-sky-500/[0.02]'}
              ${uploadMutation.isPending ? 'pointer-events-none opacity-60' : ''}`}
          >
            <input {...getInputProps()} />
            {previewUrl && !uploadMutation.isPending ? (
              <div className="space-y-3">
                <img src={previewUrl} alt="Receipt preview" className="max-h-40 mx-auto rounded-lg object-contain" />
                {uploadedReceipt ? (
                  <div className="flex items-center justify-center gap-1.5 text-green-400 text-sm font-medium">
                    <Check size={16} /> Receipt processed
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="w-14 h-14 rounded-2xl bg-sky-500/10 flex items-center justify-center mx-auto">
                  <Upload size={24} className="text-sky-400" />
                </div>
                <div>
                  <p className="text-sm font-medium">{isDragActive ? 'Drop your receipt here' : 'Drag & drop receipt image'}</p>
                  <p className="text-xs text-[var(--color-muted)] mt-1">or click to browse — JPEG/PNG, max 10MB</p>
                </div>
              </div>
            )}
            {uploadMutation.isPending && (
              <div className="space-y-3">
                <div className="w-14 h-14 rounded-2xl bg-sky-500/10 flex items-center justify-center mx-auto">
                  <Image size={24} className="text-sky-400 animate-pulse" />
                </div>
                <p className="text-sm font-medium animate-pulse">Scanning receipt with AI...</p>
                <div className="w-48 h-1.5 bg-[var(--color-surface-2)] rounded-full mx-auto overflow-hidden">
                  <motion.div className="h-full bg-sky-400 rounded-full" animate={{ x: ['-100%', '100%'] }}
                    transition={{ repeat: Infinity, duration: 1.5, ease: 'easeInOut' }} style={{ width: '50%' }} />
                </div>
              </div>
            )}
          </div>

          {/* Uploaded receipt detail */}
          {uploadedReceipt && <ReceiptDetail receipt={uploadedReceipt} />}

          {/* Selected receipt detail */}
          {selectedReceipt && !uploadedReceipt && <ReceiptDetail receipt={selectedReceipt} />}
        </div>

        {/* Right: History */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <input value={monthFilter} onChange={(e) => { setMonthFilter(e.target.value); setPage(1); }}
              placeholder="Month (YYYY-MM)" type="month"
              className="flex-1 px-3 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500" />
            <input value={storeFilter} onChange={(e) => { setStoreFilter(e.target.value); setPage(1); }}
              placeholder="Store name"
              className="flex-1 px-3 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500" />
          </div>

          {listLoading ? (
            <div className="space-y-2">{[...Array(5)].map((_, i) => <SkeletonRow key={i} />)}</div>
          ) : !receiptList?.items?.length ? (
            <EmptyState icon={FileText} title="No receipts" description="Upload your first receipt to get started" />
          ) : (
            <div className="space-y-2">
              {receiptList.items.map((r: ReceiptListItem) => (
                <motion.div key={r.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  onClick={() => loadReceipt(r.id)}
                  className="flex items-center justify-between p-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl hover:border-sky-500/30 cursor-pointer transition-all">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-sky-500/10 flex items-center justify-center shrink-0">
                      <FileText size={16} className="text-sky-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{r.merchant_name}</p>
                      <p className="text-xs text-[var(--color-muted)]">{formatDate(r.purchased_at)} • {r.item_count} items</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold" style={{ fontFamily: 'var(--font-mono)' }}>
                      {formatCurrency(r.total)}
                    </span>
                    <ChevronRight size={14} className="text-[var(--color-muted)]" />
                  </div>
                </motion.div>
              ))}

              {/* Pagination */}
              {receiptList.pagination && receiptList.pagination.total_pages > 1 && (
                <div className="flex items-center justify-center gap-2 pt-3">
                  <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-2)]/80 disabled:opacity-30 transition-colors">Prev</button>
                  <span className="text-xs text-[var(--color-muted)]">{page} / {receiptList.pagination.total_pages}</span>
                  <button onClick={() => setPage((p) => Math.min(receiptList.pagination.total_pages, p + 1))} disabled={page >= receiptList.pagination.total_pages}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-2)]/80 disabled:opacity-30 transition-colors">Next</button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
