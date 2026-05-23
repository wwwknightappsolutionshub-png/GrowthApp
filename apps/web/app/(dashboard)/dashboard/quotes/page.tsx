'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { quotes } from '@/lib/api-client'
import { DraftDocumentCreatePanel, DraftRowActions } from '@/components/quotes/DraftDocumentActions'
import { formatCurrency, formatDate } from '@/lib/utils'
import { toast } from 'sonner'
import { FileText, Send, CheckCircle, XCircle, Clock } from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-brand-forest-800 text-brand-teal-100/70',
  sent: 'bg-brand-teal-400/20 text-brand-teal-100 ring-1 ring-brand-teal-300/30',
  viewed: 'bg-brand-teal-400/10 text-brand-teal-100 ring-1 ring-brand-teal-400/20',
  accepted: 'bg-green-400/20 text-green-100 ring-1 ring-green-300/30',
  declined: 'bg-red-400/20 text-red-100 ring-1 ring-red-300/30',
}

const STATUS_ICONS: Record<string, any> = {
  draft: Clock,
  sent: Send,
  accepted: CheckCircle,
  declined: XCircle,
}

export default function QuotesPage() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['quotes'],
    queryFn: () => quotes.list().then(r => r.data),
  })

  const sendMutation = useMutation({
    mutationFn: (id: string) => quotes.send(id),
    onSuccess: () => {
      toast.success('Quote sent to customer!')
      qc.invalidateQueries({ queryKey: ['quotes'] })
    },
    onError: () => toast.error('Failed to send quote'),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Quotes</h1>
          <p className="text-muted-foreground text-sm">Send professional quotes and track responses</p>
        </div>
        <span className="text-sm text-muted-foreground">{data?.total ?? 0} total</span>
      </div>

      <DraftDocumentCreatePanel kind="quote" api={quotes} listQueryKey={['quotes']} />

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
        </div>
      ) : (
        <>
        <div className="space-y-3 md:hidden">
          {data?.items?.length === 0 && (
            <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 px-4 py-10 text-center">
              <FileText className="w-8 h-8 mx-auto mb-2 text-brand-teal-300/70" />
              <p className="text-sm text-brand-teal-100/60">No quotes yet. Create your first quote from a deal in the Pipeline.</p>
            </div>
          )}
          {data?.items?.map((quote: any) => {
            const StatusIcon = STATUS_ICONS[quote.status] || Clock
            return (
              <article key={quote.id} className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-4 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-mono text-[11px] text-brand-teal-100/60">{quote.quote_number}</p>
                    <h3 className="mt-1 truncate font-semibold text-white">{quote.title}</h3>
                  </div>
                  <span className={`inline-flex shrink-0 items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[quote.status] || 'bg-gray-100 text-muted-foreground'}`}>
                    <StatusIcon className="w-3 h-3" />
                    {quote.status}
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <p className="text-brand-teal-100/50">Total</p>
                    <p className="mt-0.5 font-semibold text-white">{formatCurrency(quote.total_pence)}</p>
                  </div>
                  <div>
                    <p className="text-brand-teal-100/50">Valid until</p>
                    <p className="mt-0.5 text-brand-teal-50">{quote.valid_until ? formatDate(quote.valid_until) : '—'}</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-brand-teal-100/50">Sent</p>
                    <p className="mt-0.5 text-brand-teal-50">{quote.sent_at ? formatDate(quote.sent_at) : 'Not sent yet'}</p>
                  </div>
                </div>
                {quote.status === 'draft' && (
                  <div className="mt-4 flex flex-col gap-2">
                    <DraftRowActions id={quote.id} status={quote.status} title={quote.title} kind="quote" api={quotes} listQueryKey={['quotes']} />
                    <button
                      onClick={() => sendMutation.mutate(quote.id)}
                      disabled={sendMutation.isPending}
                      className="flex w-full items-center justify-center gap-1 rounded-lg bg-brand-forest-700 px-3 py-2 text-xs font-semibold text-brand-forest-foreground hover:bg-brand-forest-800 disabled:opacity-50"
                    >
                      <Send className="w-3 h-3" /> Send
                    </button>
                  </div>
                )}
              </article>
            )
          })}
        </div>
        <div className="hidden overflow-x-auto rounded-xl border border-brand-forest-800 bg-brand-forest-950 shadow-sm md:block">
          <table className="min-w-[760px] w-full text-sm">
            <thead className="bg-brand-forest-900 border-b border-brand-forest-800">
              <tr>
                {['Quote #', 'Title', 'Total', 'Status', 'Valid Until', 'Sent', ''].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-brand-teal-100/75 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-forest-800">
              {data?.items?.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-brand-teal-300/70" />
                    <p className="text-brand-teal-100/60">No quotes yet. Create your first quote from a deal in the Pipeline.</p>
                  </td>
                </tr>
              )}
              {data?.items?.map((quote: any) => {
                const StatusIcon = STATUS_ICONS[quote.status] || Clock
                return (
                  <tr key={quote.id} className="hover:bg-brand-forest-900">
                    <td className="px-4 py-3 font-mono text-xs text-brand-teal-100/60">{quote.quote_number}</td>
                    <td className="px-4 py-3 font-medium text-white max-w-[200px] truncate">{quote.title}</td>
                    <td className="px-4 py-3 font-semibold text-white">{formatCurrency(quote.total_pence)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[quote.status] || 'bg-gray-100 text-muted-foreground'}`}>
                        <StatusIcon className="w-3 h-3" />
                        {quote.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-brand-teal-100/70">{quote.valid_until ? formatDate(quote.valid_until) : '—'}</td>
                    <td className="px-4 py-3 text-brand-teal-100/70">{quote.sent_at ? formatDate(quote.sent_at) : '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-1.5 items-start">
                        <DraftRowActions id={quote.id} status={quote.status} title={quote.title} kind="quote" api={quotes} listQueryKey={['quotes']} />
                        {quote.status === 'draft' && (
                          <button
                            onClick={() => sendMutation.mutate(quote.id)}
                            disabled={sendMutation.isPending}
                            className="text-xs bg-brand-forest-700 text-brand-forest-foreground px-3 py-1.5 rounded-lg hover:bg-brand-forest-800 disabled:opacity-50 flex items-center gap-1"
                          >
                            <Send className="w-3 h-3" /> Send
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        </>
      )}
    </div>
  )
}
