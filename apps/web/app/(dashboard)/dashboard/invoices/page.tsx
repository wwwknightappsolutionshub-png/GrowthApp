'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Mail } from 'lucide-react'
import { invoices } from '@/lib/api-client'
import { DraftDocumentCreatePanel, DraftRowActions } from '@/components/quotes/DraftDocumentActions'
import {
  buildInvoiceQueryParams,
  InvoiceListFilters,
  type InvoiceFilterState,
} from '@/components/quotes/DocumentListFilters'
import { IndustryAddonsUpgradeAlert } from '@/components/addons/IndustryAddonsUpgradeAlert'
import { toast } from 'sonner'
import { formatCurrency, formatDate } from '@/lib/utils'
import { FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-brand-forest-800 text-brand-teal-100/70',
  sent: 'bg-brand-teal-400/20 text-brand-teal-100 ring-1 ring-brand-teal-300/30',
  paid: 'bg-green-400/20 text-green-100 ring-1 ring-green-300/30',
  overdue: 'bg-red-400/20 text-red-100 ring-1 ring-red-300/30',
  partial: 'bg-yellow-400/20 text-yellow-100 ring-1 ring-yellow-300/30',
}

const STATUS_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  draft: Clock,
  sent: Clock,
  paid: CheckCircle,
  overdue: AlertCircle,
}

const EMPTY_FILTERS: InvoiceFilterState = {
  title: '',
  invoice_number: '',
  total_min: '',
  total_max: '',
  due_date_from: '',
  due_date_to: '',
}

export default function InvoicesPage() {
  const qc = useQueryClient()
  const [filters, setFilters] = useState<InvoiceFilterState>(EMPTY_FILTERS)
  const [showFilters, setShowFilters] = useState(false)
  const params = buildInvoiceQueryParams(filters)

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', params],
    queryFn: () => invoices.list(params).then((r) => r.data),
  })

  const totalPaid = data?.items?.filter((i: { status: string }) => i.status === 'paid').reduce((sum: number, i: { total_pence: number }) => sum + i.total_pence, 0) ?? 0
  const totalOutstanding = data?.items?.filter((i: { status: string }) => i.status !== 'paid').reduce((sum: number, i: { total_pence: number; paid_pence: number }) => sum + (i.total_pence - i.paid_pence), 0) ?? 0

  const recordPay = useMutation({
    mutationFn: (id: string) => invoices.recordPayment(id, { payment_channel: 'cash_deposit' }),
    onSuccess: () => {
      toast.success('Payment recorded')
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['accounts-dashboard'] })
    },
    onError: () => toast.error('Could not record payment'),
  })

  const sendInv = useMutation({
    mutationFn: (id: string) => invoices.send(id),
    onSuccess: () => {
      toast.success('Invoice sent by email')
      qc.invalidateQueries({ queryKey: ['invoices'] })
    },
    onError: () => toast.error('Send failed — add customer email'),
  })

  return (
    <div className="space-y-6">
      <IndustryAddonsUpgradeAlert />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Invoices</h1>
          <p className="text-muted-foreground text-sm">Track payments and outstanding balances</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <DraftDocumentCreatePanel kind="invoice" api={invoices} listQueryKey={['invoices']} />
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="rounded-lg border border-brand-forest-700 px-3 py-2 text-sm text-brand-teal-100 hover:bg-brand-forest-900"
          >
            {showFilters ? 'Hide filters' : 'Filter'}
          </button>
        </div>
      </div>

      {showFilters && <InvoiceListFilters value={filters} onChange={setFilters} />}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-5 shadow-sm">
          <p className="text-sm text-brand-teal-100/75 mb-1">Total Collected</p>
          <p className="text-2xl font-bold text-brand-teal-100">{formatCurrency(totalPaid)}</p>
        </div>
        <div className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-5 shadow-sm">
          <p className="text-sm text-brand-teal-100/75 mb-1">Outstanding</p>
          <p className="text-2xl font-bold text-amber-100">{formatCurrency(totalOutstanding)}</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="hidden overflow-x-auto rounded-xl border border-brand-forest-800 bg-brand-forest-950 shadow-sm md:block">
          <table className="min-w-[960px] w-full text-sm">
            <thead className="bg-brand-forest-900 border-b border-brand-forest-800">
              <tr>
                {['Invoice #', 'Title', 'Total', 'Paid', 'Status', 'Due Date', 'Payment Link', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-brand-teal-100/75 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-forest-800">
              {data?.items?.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-brand-teal-300/70" />
                    <p className="text-brand-teal-100/60">No invoices yet. Create one with Add New.</p>
                  </td>
                </tr>
              )}
              {data?.items?.map((invoice: {
                id: string
                invoice_number: string
                title: string
                total_pence: number
                paid_pence: number
                status: string
                due_date?: string
                stripe_payment_link?: string
              }) => {
                const StatusIcon = STATUS_ICONS[invoice.status] || Clock
                return (
                  <tr key={invoice.id} className="hover:bg-brand-forest-900">
                    <td className="px-4 py-3 font-mono text-xs text-brand-teal-100/60">{invoice.invoice_number}</td>
                    <td className="px-4 py-3 font-medium text-white max-w-[180px] truncate">{invoice.title}</td>
                    <td className="px-4 py-3 font-semibold text-white">{formatCurrency(invoice.total_pence)}</td>
                    <td className="px-4 py-3 text-brand-teal-100 font-medium">{formatCurrency(invoice.paid_pence)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[invoice.status] || 'bg-gray-100 text-muted-foreground'}`}>
                        <StatusIcon className="w-3 h-3" />
                        {invoice.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-brand-teal-100/70">{invoice.due_date ? formatDate(invoice.due_date) : '—'}</td>
                    <td className="px-4 py-3">
                      {invoice.stripe_payment_link && (
                        <a href={invoice.stripe_payment_link} target="_blank" rel="noopener noreferrer" className="text-xs text-brand-teal-100 hover:underline">
                          Pay now
                        </a>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-1 items-start">
                        <DraftRowActions id={invoice.id} status={invoice.status} title={invoice.title} kind="invoice" api={invoices} listQueryKey={['invoices']} />
                        {invoice.status === 'draft' && (
                          <button type="button" onClick={() => sendInv.mutate(invoice.id)} className="text-xs text-brand-teal-300 hover:underline inline-flex items-center gap-1">
                            <Mail className="w-3 h-3" /> Send email
                          </button>
                        )}
                        {invoice.status !== 'paid' && (
                          <button type="button" onClick={() => recordPay.mutate(invoice.id)} className="text-xs text-brand-teal-300 hover:underline">
                            Mark paid
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
      )}
    </div>
  )
}
