'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { quotes } from '@/lib/api-client'
import { DraftDocumentCreatePanel, DraftRowActions } from '@/components/quotes/DraftDocumentActions'
import {
  buildQuoteQueryParams,
  QuoteListFilters,
  type QuoteFilterState,
} from '@/components/quotes/DocumentListFilters'
import { IndustryAddonsUpgradeAlert } from '@/components/addons/IndustryAddonsUpgradeAlert'
import { formatCurrency, formatDate } from '@/lib/utils'
import { toast } from 'sonner'
import { FileText, Send, CheckCircle, XCircle, Clock, Mail } from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-brand-forest-800 text-brand-teal-100/70',
  sent: 'bg-brand-teal-400/20 text-brand-teal-100 ring-1 ring-brand-teal-300/30',
  viewed: 'bg-brand-teal-400/10 text-brand-teal-100 ring-1 ring-brand-teal-400/20',
  accepted: 'bg-green-400/20 text-green-100 ring-1 ring-green-300/30',
  declined: 'bg-red-400/20 text-red-100 ring-1 ring-red-300/30',
}

const STATUS_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  draft: Clock,
  sent: Send,
  accepted: CheckCircle,
  declined: XCircle,
}

const EMPTY_FILTERS: QuoteFilterState = {
  title: '',
  quote_number: '',
  total_min: '',
  total_max: '',
  valid_until_from: '',
  valid_until_to: '',
}

export default function QuotesPage() {
  const qc = useQueryClient()
  const [filters, setFilters] = useState<QuoteFilterState>(EMPTY_FILTERS)
  const [showFilters, setShowFilters] = useState(false)
  const params = buildQuoteQueryParams(filters)

  const { data, isLoading } = useQuery({
    queryKey: ['quotes', params],
    queryFn: () => quotes.list(params).then((r) => r.data),
  })

  const sendMutation = useMutation({
    mutationFn: (id: string) => quotes.send(id),
    onSuccess: () => {
      toast.success('Quote sent to customer!')
      qc.invalidateQueries({ queryKey: ['quotes'] })
    },
    onError: () => toast.error('Failed to send quote'),
  })

  const sendInvoiceMutation = useMutation({
    mutationFn: (id: string) => quotes.sendInvoice(id),
    onSuccess: () => {
      toast.success('Invoice created and emailed!')
      qc.invalidateQueries({ queryKey: ['quotes'] })
      qc.invalidateQueries({ queryKey: ['invoices'] })
    },
    onError: () => toast.error('Failed to send invoice — check customer email'),
  })

  return (
    <div className="space-y-6">
      <IndustryAddonsUpgradeAlert />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Quotes</h1>
          <p className="text-muted-foreground text-sm">Send professional quotes and track responses</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">{data?.total ?? 0} total</span>
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="rounded-lg border border-brand-forest-700 px-3 py-2 text-sm text-brand-teal-100 hover:bg-brand-forest-900"
          >
            {showFilters ? 'Hide filters' : 'Filter'}
          </button>
        </div>
      </div>

      <DraftDocumentCreatePanel kind="quote" api={quotes} listQueryKey={['quotes']} />

      {showFilters && <QuoteListFilters value={filters} onChange={setFilters} />}

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="hidden overflow-x-auto rounded-xl border border-brand-forest-800 bg-brand-forest-950 shadow-sm md:block">
          <table className="min-w-[900px] w-full text-sm">
            <thead className="bg-brand-forest-900 border-b border-brand-forest-800">
              <tr>
                {['Quote #', 'Customer', 'Title', 'Total', 'Status', 'Valid Until', 'Sent', ''].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-brand-teal-100/75 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-forest-800">
              {data?.items?.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-brand-teal-300/70" />
                    <p className="text-brand-teal-100/60">No quotes yet. Create your first quote with New quote.</p>
                  </td>
                </tr>
              )}
              {data?.items?.map((quote: {
                id: string
                quote_number: string
                customer_name?: string
                title: string
                total_pence: number
                status: string
                valid_until?: string
                sent_at?: string
              }) => {
                const StatusIcon = STATUS_ICONS[quote.status] || Clock
                return (
                  <tr key={quote.id} className="hover:bg-brand-forest-900">
                    <td className="px-4 py-3 font-mono text-xs text-brand-teal-100/60">{quote.quote_number}</td>
                    <td className="px-4 py-3 text-brand-teal-100/80">{quote.customer_name ?? '—'}</td>
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
                            <Send className="w-3 h-3" /> Send quote
                          </button>
                        )}
                        <button
                          onClick={() => sendInvoiceMutation.mutate(quote.id)}
                          disabled={sendInvoiceMutation.isPending}
                          className="text-xs text-brand-teal-300 hover:underline inline-flex items-center gap-1"
                        >
                          <Mail className="w-3 h-3" /> Send invoice by email
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
