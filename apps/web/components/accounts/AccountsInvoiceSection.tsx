'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Mail } from 'lucide-react'
import { toast } from 'sonner'

import { DraftDocumentCreatePanel, DraftRowActions } from '@/components/quotes/DraftDocumentActions'
import {
  buildInvoiceQueryParams,
  InvoiceListFilters,
  type InvoiceFilterState,
} from '@/components/quotes/DocumentListFilters'
import { invoices } from '@/lib/api-client'
import { formatCurrency, formatDate } from '@/lib/utils'

const EMPTY_FILTERS: InvoiceFilterState = {
  title: '',
  invoice_number: '',
  total_min: '',
  total_max: '',
  due_date_from: '',
  due_date_to: '',
}

type InvoiceRow = {
  id: string
  invoice_number: string
  title: string
  total_pence: number
  paid_pence: number
  status: string
  due_date?: string
  customer_name?: string
  payment_channel?: string
}

export function AccountsInvoiceSection({
  category,
  title,
  description,
}: {
  category: 'cash_in' | 'cash_pending' | 'cash_out'
  title: string
  description: string
}) {
  const qc = useQueryClient()
  const [filters, setFilters] = useState<InvoiceFilterState>(EMPTY_FILTERS)
  const [showFilters, setShowFilters] = useState(false)
  const [payChannel, setPayChannel] = useState<'online' | 'cash_deposit'>('cash_deposit')

  const params = buildInvoiceQueryParams(filters, { category })

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', category, params],
    queryFn: () => invoices.list(params).then((r) => r.data),
  })

  const sendInv = useMutation({
    mutationFn: (id: string) => invoices.send(id),
    onSuccess: () => {
      toast.success('Invoice emailed to customer')
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['accounts-dashboard'] })
    },
    onError: () => toast.error('Could not send invoice — check customer email'),
  })

  const recordPay = useMutation({
    mutationFn: (id: string) => invoices.recordPayment(id, { payment_channel: payChannel }),
    onSuccess: () => {
      toast.success('Payment recorded')
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['accounts-dashboard'] })
      qc.invalidateQueries({ queryKey: ['accounts', 'cash-saved'] })
    },
    onError: () => toast.error('Could not record payment'),
  })

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-white">{title}</h2>
        <p className="text-sm text-brand-teal-100/65 mt-1">{description}</p>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        <DraftDocumentCreatePanel kind="invoice" api={invoices} listQueryKey={['invoices', category]} />
        <button
          type="button"
          onClick={() => setShowFilters(!showFilters)}
          className="rounded-lg border border-brand-forest-700 px-3 py-2 text-sm text-brand-teal-100 hover:bg-brand-forest-900"
        >
          {showFilters ? 'Hide filters' : 'Filters'}
        </button>
        {category !== 'cash_in' && (
          <select
            value={payChannel}
            onChange={(e) => setPayChannel(e.target.value as 'online' | 'cash_deposit')}
            className="rounded-lg border border-brand-forest-700 bg-brand-forest-950 px-3 py-2 text-sm text-white"
            title="Payment channel when marking paid"
          >
            <option value="cash_deposit">cash deposit</option>
            <option value="online">online</option>
          </select>
        )}
      </div>

      {showFilters && <InvoiceListFilters value={filters} onChange={setFilters} />}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-brand-forest-800">
          <table className="min-w-[900px] w-full text-sm">
            <thead className="bg-brand-forest-900 text-brand-teal-100/70 text-left">
              <tr>
                {['Invoice #', 'Title', 'Customer', 'Total', 'Due', 'Status', 'Channel', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-xs uppercase tracking-wide font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-forest-800 bg-brand-forest-950">
              {(data?.items ?? []).length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-brand-teal-100/55">
                    No records in this category.
                  </td>
                </tr>
              )}
              {(data?.items as InvoiceRow[] | undefined)?.map((inv) => (
                <tr key={inv.id} className="hover:bg-brand-forest-900">
                  <td className="px-4 py-3 font-mono text-xs">{inv.invoice_number}</td>
                  <td className="px-4 py-3 font-medium text-white">{inv.title}</td>
                  <td className="px-4 py-3 text-brand-teal-100/80">{inv.customer_name ?? '—'}</td>
                  <td className="px-4 py-3 text-white">{formatCurrency(inv.total_pence)}</td>
                  <td className="px-4 py-3">{inv.due_date ? formatDate(inv.due_date) : '—'}</td>
                  <td className="px-4 py-3 capitalize">{inv.status}</td>
                  <td className="px-4 py-3">{inv.payment_channel ?? '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1 items-start">
                      <DraftRowActions
                        id={inv.id}
                        status={inv.status}
                        title={inv.title}
                        kind="invoice"
                        api={invoices}
                        listQueryKey={['invoices', category]}
                      />
                      {inv.status === 'draft' && (
                        <button
                          type="button"
                          onClick={() => sendInv.mutate(inv.id)}
                          className="text-xs text-brand-teal-300 hover:underline inline-flex items-center gap-1"
                        >
                          <Mail className="w-3 h-3" /> Send email
                        </button>
                      )}
                      {inv.status !== 'paid' && (
                        <button
                          type="button"
                          onClick={() => recordPay.mutate(inv.id)}
                          className="text-xs text-brand-teal-300 hover:underline"
                        >
                          Mark paid
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
