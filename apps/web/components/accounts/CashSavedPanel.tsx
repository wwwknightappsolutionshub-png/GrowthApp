'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { accounts } from '@/lib/api-client'
import { formatCurrency, formatDate } from '@/lib/utils'
import { inputClass, labelClass } from '@/components/quotes/QuoteInvoiceForm'

type Row = {
  id: string
  invoice_number: string
  title: string
  total_pence: number
  payment_date: string | null
  payment_channel: string
  customer_name?: string
}

export function CashSavedPanel() {
  const [channel, setChannel] = useState('')
  const [sortBy, setSortBy] = useState('deposit_date')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [depositFrom, setDepositFrom] = useState('')
  const [depositTo, setDepositTo] = useState('')
  const [amountMin, setAmountMin] = useState('')
  const [amountMax, setAmountMax] = useState('')

  const params: Record<string, string | number> = {
    sort_by: sortBy,
    sort_dir: sortDir,
  }
  if (channel) params.payment_channel = channel
  if (depositFrom) params.deposit_from = depositFrom
  if (depositTo) params.deposit_to = depositTo
  if (amountMin) params.total_min = Math.round(parseFloat(amountMin) * 100)
  if (amountMax) params.total_max = Math.round(parseFloat(amountMax) * 100)

  const { data, isLoading } = useQuery({
    queryKey: ['accounts', 'cash-saved', params],
    queryFn: () => accounts.cashSaved(params).then((r) => r.data),
  })

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-white">Cash saved</h2>
        <p className="text-sm text-brand-teal-100/65 mt-1">
          Bank deposit repository — paid invoices and cash received.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 rounded-xl border border-brand-forest-700 bg-brand-forest-900/60 p-4">
        <div>
          <label className={labelClass}>Channel</label>
          <select className={inputClass} value={channel} onChange={(e) => setChannel(e.target.value)}>
            <option value="">All</option>
            <option value="online">online</option>
            <option value="cash_deposit">cash deposit</option>
          </select>
        </div>
        <div>
          <label className={labelClass}>Deposit from</label>
          <input className={inputClass} type="date" value={depositFrom} onChange={(e) => setDepositFrom(e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Deposit to</label>
          <input className={inputClass} type="date" value={depositTo} onChange={(e) => setDepositTo(e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Sort by</label>
          <select className={inputClass} value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="deposit_date">Deposit date</option>
            <option value="amount">Amount</option>
            <option value="channel">Channel</option>
          </select>
        </div>
        <div>
          <label className={labelClass}>Direction</label>
          <select className={inputClass} value={sortDir} onChange={(e) => setSortDir(e.target.value as 'asc' | 'desc')}>
            <option value="desc">Newest first</option>
            <option value="asc">Oldest first</option>
          </select>
        </div>
        <div>
          <label className={labelClass}>Amount min (£)</label>
          <input className={inputClass} type="number" min="0" step="0.01" value={amountMin} onChange={(e) => setAmountMin(e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Amount max (£)</label>
          <input className={inputClass} type="number" min="0" step="0.01" value={amountMax} onChange={(e) => setAmountMax(e.target.value)} />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-brand-forest-800">
          <table className="min-w-[800px] w-full text-sm">
            <thead className="bg-brand-forest-900 text-brand-teal-100/70 text-left">
              <tr>
                {['Invoice #', 'Title', 'Total', 'Payment date', 'Payment channel'].map((h) => (
                  <th key={h} className="px-4 py-3 text-xs uppercase tracking-wide font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-forest-800 bg-brand-forest-950">
              {(data?.items as Row[] | undefined)?.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-brand-teal-100/55">
                    No paid deposits yet.
                  </td>
                </tr>
              )}
              {(data?.items as Row[] | undefined)?.map((row) => (
                <tr key={row.id} className="hover:bg-brand-forest-900">
                  <td className="px-4 py-3 font-mono text-xs">{row.invoice_number}</td>
                  <td className="px-4 py-3 text-white font-medium">{row.title}</td>
                  <td className="px-4 py-3">{formatCurrency(row.total_pence)}</td>
                  <td className="px-4 py-3">{row.payment_date ? formatDate(row.payment_date) : '—'}</td>
                  <td className="px-4 py-3 capitalize">{row.payment_channel?.replace('_', ' ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
