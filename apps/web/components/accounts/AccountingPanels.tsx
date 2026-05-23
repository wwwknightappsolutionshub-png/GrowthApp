'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { accounting } from '@/lib/api-client'
import { formatCurrency, formatDate } from '@/lib/utils'
import { inputClass, labelClass } from '@/components/quotes/QuoteInvoiceForm'

export function AccountingPanels() {
  const qc = useQueryClient()
  const [expOpen, setExpOpen] = useState(false)
  const [desc, setDesc] = useState('')
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState('general')
  const [expDate, setExpDate] = useState(new Date().toISOString().slice(0, 10))

  const { data: expenses } = useQuery({
    queryKey: ['accounting-expenses'],
    queryFn: () => accounting.listExpenses().then((r) => r.data),
  })

  const { data: recurring } = useQuery({
    queryKey: ['accounting-recurring'],
    queryFn: () => accounting.listRecurring().then((r) => r.data),
  })

  const createExp = useMutation({
    mutationFn: () =>
      accounting.createExpense({
        description: desc,
        amount_pence: Math.round(parseFloat(amount || '0') * 100),
        category,
        expense_date: expDate,
      }),
    onSuccess: () => {
      toast.success('Expense recorded')
      setExpOpen(false)
      qc.invalidateQueries({ queryKey: ['accounting-expenses'] })
      qc.invalidateQueries({ queryKey: ['accounts-dashboard'] })
    },
    onError: () => toast.error('Could not save expense'),
  })

  const removeExp = useMutation({
    mutationFn: (id: string) => accounting.deleteExpense(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['accounting-expenses'] })
      qc.invalidateQueries({ queryKey: ['accounts-dashboard'] })
    },
  })

  const exportPack = useMutation({
    mutationFn: async () => {
      const res = await accounting.exportAccountantPack(new Date().getFullYear())
      const blob = new Blob([res.data], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `accountant-pack-${new Date().getFullYear()}.csv`
      a.click()
      URL.revokeObjectURL(url)
    },
    onSuccess: () => toast.success('Export downloaded'),
    onError: () => toast.error('Export failed'),
  })

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-white">Accounting tools</h2>
        <button
          type="button"
          onClick={() => exportPack.mutate()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-brand-forest-600 px-3 py-2 text-xs font-semibold text-brand-teal-100 hover:bg-brand-forest-800"
        >
          <Download className="w-4 h-4" /> Accountant pack (CSV)
        </button>
      </div>

      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-900/50 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-white">Expenses</h3>
          <button
            type="button"
            onClick={() => setExpOpen(!expOpen)}
            className="inline-flex items-center gap-1 text-xs font-semibold text-brand-teal-300"
          >
            <Plus className="w-4 h-4" /> Add expense
          </button>
        </div>
        {expOpen && (
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="sm:col-span-2">
              <span className={labelClass}>Description</span>
              <input className={inputClass} value={desc} onChange={(e) => setDesc(e.target.value)} />
            </label>
            <label>
              <span className={labelClass}>Amount (£)</span>
              <input className={inputClass} type="number" min="0" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} />
            </label>
            <label>
              <span className={labelClass}>Category</span>
              <input className={inputClass} value={category} onChange={(e) => setCategory(e.target.value)} />
            </label>
            <label>
              <span className={labelClass}>Date</span>
              <input className={inputClass} type="date" value={expDate} onChange={(e) => setExpDate(e.target.value)} />
            </label>
            <button
              type="button"
              disabled={!desc || createExp.isPending}
              onClick={() => createExp.mutate()}
              className="rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              Save expense
            </button>
          </div>
        )}
        <ul className="divide-y divide-brand-forest-800">
          {(expenses?.items ?? []).length === 0 && (
            <li className="py-6 text-center text-sm text-brand-teal-100/55">No expenses logged yet.</li>
          )}
          {expenses?.items?.map((e: { id: string; description: string; amount_pence: number; expense_date: string; category: string }) => (
            <li key={e.id} className="flex items-center justify-between py-3 gap-3">
              <div>
                <p className="text-sm font-medium text-white">{e.description}</p>
                <p className="text-xs text-brand-teal-100/55">
                  {formatDate(e.expense_date)} · {e.category}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-white">{formatCurrency(e.amount_pence)}</span>
                <button type="button" onClick={() => removeExp.mutate(e.id)} className="text-red-300 hover:text-red-200">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-900/50 p-5">
        <div className="flex items-center gap-2 mb-3">
          <RefreshCw className="w-4 h-4 text-brand-teal-400" />
          <h3 className="font-semibold text-white">Recurring schedules</h3>
        </div>
        <p className="text-xs text-brand-teal-100/55 mb-4">
          Active schedules run daily via the worker. Create schedules via API or contact support for bulk setup.
        </p>
        <ul className="space-y-2">
          {(recurring?.items ?? []).length === 0 && (
            <li className="text-sm text-brand-teal-100/55">No recurring schedules yet.</li>
          )}
          {recurring?.items?.map((s: { id: string; title: string; next_run_at: string; interval_unit: string; is_active: boolean }) => (
            <li key={s.id} className="flex justify-between text-sm border border-brand-forest-700 rounded-lg px-3 py-2">
              <span className="text-white">{s.title}</span>
              <span className="text-brand-teal-100/60">
                Next {formatDate(s.next_run_at)} · {s.interval_unit}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export function AccountingUpgradeBanner() {
  return (
    <div className="rounded-xl border border-brand-teal-500/30 bg-brand-teal-600/10 p-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p className="text-sm font-semibold text-white">Unlock full Accounting</p>
        <p className="text-xs text-brand-teal-100/70 mt-0.5">
          Payments, expenses, recurring invoices, and UK tax exports.
        </p>
      </div>
      <Link
        href="/dashboard/accounts/upgrade"
        className="rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500"
      >
        View upgrade
      </Link>
    </div>
  )
}
