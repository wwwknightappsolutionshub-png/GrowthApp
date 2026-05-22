'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { FileText, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { crm, invoices } from '@/lib/api-client'
import { formatCurrency, formatDate } from '@/lib/utils'

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-brand-forest-800 text-brand-teal-100/70',
  sent: 'bg-brand-teal-400/20 text-brand-teal-100',
  paid: 'bg-green-400/20 text-green-100',
  overdue: 'bg-red-400/20 text-red-100',
  partial: 'bg-yellow-400/20 text-yellow-100',
}

export function AccountsInvoicesPanel() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [amountPence, setAmountPence] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', 'accounts'],
    queryFn: () => invoices.list().then((r) => r.data),
  })

  const { data: customers } = useQuery({
    queryKey: ['crm', 'customers', 'invoice-picker'],
    queryFn: () => crm.listCustomers({ page: 1, page_size: 100 }).then((r) => r.data),
    enabled: showCreate,
  })

  const createInv = useMutation({
    mutationFn: () =>
      invoices.create({
        customer_id: customerId,
        title: title || 'Invoice',
        items: [
          {
            description: title || 'Service',
            quantity: 1,
            unit_price_pence: Math.round(parseFloat(amountPence || '0') * 100),
          },
        ],
      }),
    onSuccess: () => {
      toast.success('Invoice created')
      setShowCreate(false)
      setTitle('')
      setAmountPence('')
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['accounts-dashboard'] })
    },
    onError: () => toast.error('Could not create invoice'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => invoices.delete(id),
    onSuccess: () => {
      toast.success('Invoice deleted')
      qc.invalidateQueries({ queryKey: ['invoices'] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Delete failed'),
  })

  const recordPay = useMutation({
    mutationFn: (id: string) => invoices.recordPayment(id),
    onSuccess: () => {
      toast.success('Payment recorded')
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['accounts-dashboard'] })
    },
  })

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-brand-teal-300" />
          Invoices
        </h2>
        <button
          type="button"
          onClick={() => setShowCreate(!showCreate)}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-forest-700 text-white text-sm font-semibold"
        >
          <Plus className="w-4 h-4" />
          New invoice
        </button>
      </div>

      {showCreate && (
        <div className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-4 space-y-3">
          <select
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-950 text-white text-sm"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
          >
            <option value="">Select customer *</option>
            {(customers?.items ?? []).map((c: { id: string; first_name: string; last_name?: string }) => (
              <option key={c.id} value={c.id}>
                {c.first_name} {c.last_name ?? ''}
              </option>
            ))}
          </select>
          <input
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-950 text-white text-sm"
            placeholder="Title / description"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <input
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-950 text-white text-sm"
            placeholder="Amount (£)"
            type="number"
            min="0"
            step="0.01"
            value={amountPence}
            onChange={(e) => setAmountPence(e.target.value)}
          />
          <button
            type="button"
            disabled={!customerId || createInv.isPending}
            onClick={() => createInv.mutate()}
            className="px-4 py-2 rounded-lg bg-brand-teal-600 text-white text-sm font-semibold disabled:opacity-50"
          >
            Create draft invoice
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="rounded-xl border border-brand-forest-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-brand-forest-900 text-brand-teal-100/70 text-left">
              <tr>
                <th className="px-4 py-3">Invoice</th>
                <th className="px-4 py-3">Due</th>
                <th className="px-4 py-3">Total</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-forest-800">
              {(data?.items ?? []).length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-brand-teal-100/60">
                    No invoices yet.
                  </td>
                </tr>
              ) : (
                data?.items?.map((inv: { id: string; invoice_number: string; title: string; due_date?: string; total_pence: number; status: string }) => (
                  <tr key={inv.id} className="bg-brand-forest-950 hover:bg-brand-forest-900">
                    <td className="px-4 py-3">
                      <p className="font-mono text-xs text-brand-teal-100/60">{inv.invoice_number}</p>
                      <p className="text-white font-medium">{inv.title}</p>
                    </td>
                    <td className="px-4 py-3 text-brand-teal-100/80">{inv.due_date ? formatDate(inv.due_date) : '—'}</td>
                    <td className="px-4 py-3 text-white">{formatCurrency(inv.total_pence)}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${STATUS_COLORS[inv.status] ?? ''}`}>
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      {inv.status !== 'paid' && (
                        <button
                          type="button"
                          onClick={() => recordPay.mutate(inv.id)}
                          className="text-xs text-brand-teal-300 hover:underline"
                        >
                          Mark paid
                        </button>
                      )}
                      {inv.status === 'draft' && (
                        <button
                          type="button"
                          onClick={() => {
                            if (confirm('Delete this draft invoice permanently?')) remove.mutate(inv.id)
                          }}
                          className="inline-flex items-center text-xs text-red-300 hover:underline"
                        >
                          <Trash2 className="w-3 h-3 mr-0.5" />
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-brand-teal-100/55">
        Full quote workflow: <Link href="/dashboard/quotes" className="text-brand-teal-300 hover:underline">Quotes</Link>
      </p>
    </div>
  )
}
