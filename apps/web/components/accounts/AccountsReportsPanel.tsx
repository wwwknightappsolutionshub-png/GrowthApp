'use client'

import { useState } from 'react'
import { Download } from 'lucide-react'
import { toast } from 'sonner'

import { accounts } from '@/lib/api-client'
import { inputClass, labelClass } from '@/components/quotes/QuoteInvoiceForm'

const CATEGORIES = [
  { value: 'cash_in', label: 'Cash in' },
  { value: 'cash_pending', label: 'Cash pending' },
  { value: 'cash_out', label: 'Cash out' },
  { value: 'cash_saved', label: 'Cash saved' },
  { value: 'quotes', label: 'Quotes' },
] as const

export function AccountsReportsPanel() {
  const [category, setCategory] = useState<string>('cash_in')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [loading, setLoading] = useState(false)

  const download = async () => {
    setLoading(true)
    try {
      const params: { category: string; date_from?: string; date_to?: string } = { category }
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      const res = await accounts.reports(params)
      const blob = new Blob([res.data], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `accounts-${category}.csv`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Report downloaded')
    } catch {
      toast.error('Could not generate report')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-white">Reports</h2>
        <p className="text-sm text-brand-teal-100/65 mt-1">
          Export CSV by category with optional date range.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 max-w-3xl rounded-xl border border-brand-forest-700 bg-brand-forest-900/60 p-4">
        <div>
          <label className={labelClass}>Report type</label>
          <select className={inputClass} value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass}>From</label>
          <input className={inputClass} type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>To</label>
          <input className={inputClass} type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </div>
      </div>

      <button
        type="button"
        disabled={loading}
        onClick={download}
        className="inline-flex items-center gap-2 rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
      >
        <Download className="w-4 h-4" />
        {loading ? 'Generating…' : 'Download CSV'}
      </button>
    </div>
  )
}
