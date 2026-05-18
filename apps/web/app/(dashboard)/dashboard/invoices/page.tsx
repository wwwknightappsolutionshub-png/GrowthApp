'use client'

import { useQuery } from '@tanstack/react-query'
import { invoices } from '@/lib/api-client'
import { formatCurrency, formatDate } from '@/lib/utils'
import { FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-brand-forest-800 text-brand-teal-100/70',
  sent: 'bg-brand-teal-400/20 text-brand-teal-100 ring-1 ring-brand-teal-300/30',
  paid: 'bg-green-400/20 text-green-100 ring-1 ring-green-300/30',
  overdue: 'bg-red-400/20 text-red-100 ring-1 ring-red-300/30',
  partial: 'bg-yellow-400/20 text-yellow-100 ring-1 ring-yellow-300/30',
}

const STATUS_ICONS: Record<string, any> = {
  draft: Clock,
  sent: Clock,
  paid: CheckCircle,
  overdue: AlertCircle,
}

export default function InvoicesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => invoices.list().then(r => r.data),
  })

  const totalPaid = data?.items?.filter((i: any) => i.status === 'paid').reduce((sum: number, i: any) => sum + i.total_pence, 0) ?? 0
  const totalOutstanding = data?.items?.filter((i: any) => i.status !== 'paid').reduce((sum: number, i: any) => sum + (i.total_pence - i.paid_pence), 0) ?? 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Invoices</h1>
          <p className="text-muted-foreground text-sm">Track payments and outstanding balances</p>
        </div>
      </div>

      {/* Summary */}
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
        <>
        <div className="space-y-3 md:hidden">
          {data?.items?.length === 0 && (
            <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 px-4 py-10 text-center">
              <FileText className="w-8 h-8 mx-auto mb-2 text-brand-teal-300/70" />
              <p className="text-sm text-brand-teal-100/60">No invoices yet. Accept a quote to auto-generate the first invoice.</p>
            </div>
          )}
          {data?.items?.map((invoice: any) => {
            const StatusIcon = STATUS_ICONS[invoice.status] || Clock
            return (
              <article key={invoice.id} className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-4 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-mono text-[11px] text-brand-teal-100/60">{invoice.invoice_number}</p>
                    <h3 className="mt-1 truncate font-semibold text-white">{invoice.title}</h3>
                  </div>
                  <span className={`inline-flex shrink-0 items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[invoice.status] || 'bg-gray-100 text-muted-foreground'}`}>
                    <StatusIcon className="w-3 h-3" />
                    {invoice.status}
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <p className="text-brand-teal-100/50">Total</p>
                    <p className="mt-0.5 font-semibold text-white">{formatCurrency(invoice.total_pence)}</p>
                  </div>
                  <div>
                    <p className="text-brand-teal-100/50">Paid</p>
                    <p className="mt-0.5 font-semibold text-brand-teal-100">{formatCurrency(invoice.paid_pence)}</p>
                  </div>
                  <div>
                    <p className="text-brand-teal-100/50">Due date</p>
                    <p className="mt-0.5 text-brand-teal-50">{invoice.due_date ? formatDate(invoice.due_date) : '—'}</p>
                  </div>
                  <div>
                    <p className="text-brand-teal-100/50">Payment</p>
                    {invoice.stripe_payment_link ? (
                      <a
                        href={invoice.stripe_payment_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-0.5 inline-flex text-brand-teal-100 underline underline-offset-2"
                      >
                        Pay now
                      </a>
                    ) : (
                      <p className="mt-0.5 text-brand-teal-50">—</p>
                    )}
                  </div>
                </div>
              </article>
            )
          })}
        </div>
        <div className="hidden overflow-x-auto rounded-xl border border-brand-forest-800 bg-brand-forest-950 shadow-sm md:block">
          <table className="min-w-[780px] w-full text-sm">
            <thead className="bg-brand-forest-900 border-b border-brand-forest-800">
              <tr>
                {['Invoice #', 'Title', 'Total', 'Paid', 'Status', 'Due Date', 'Payment Link'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-brand-teal-100/75 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-forest-800">
              {data?.items?.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-brand-teal-300/70" />
                    <p className="text-brand-teal-100/60">No invoices yet. Accept a quote to auto-generate the first invoice.</p>
                  </td>
                </tr>
              )}
              {data?.items?.map((invoice: any) => {
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
                        <a
                          href={invoice.stripe_payment_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-brand-teal-100 hover:text-white hover:underline"
                        >
                          Pay now
                        </a>
                      )}
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
