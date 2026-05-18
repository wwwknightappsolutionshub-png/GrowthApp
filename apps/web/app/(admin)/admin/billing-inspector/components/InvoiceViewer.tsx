'use client'

import { useState } from 'react'
import { Code2, Download, FileText } from 'lucide-react'

export interface InvoiceData {
  id: string
  customer: { type: string; id: string | null; name: string | null }
  billing_period: { start: string | null; end: string | null }
  stripe_invoice_id: string | null
  line_items: Array<{ description: string; amount_pence: number }>
  subtotal_pence: number
  tax_pence: number
  overage_pence: number
  discount_pence: number
  total_pence: number
  currency: string
  status: string
  invoice_pdf_url: string | null
  created_at: string | null
  payment_attempts: Array<{
    id: string
    timestamp: string | null
    action: string
    status: string | null
    metadata: Record<string, unknown>
  }>
}

function fmt(pence: number, ccy: string): string {
  return `${ccy.toUpperCase() === 'GBP' ? '£' : ccy.toUpperCase() + ' '}${(pence / 100).toFixed(2)}`
}

export function InvoiceViewer({ data }: { data: InvoiceData }) {
  const [rawOpen, setRawOpen] = useState(false)

  return (
    <div className="space-y-4 text-gray-200">
      <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-gray-500">Invoice</div>
            <div className="font-mono text-sm text-white">{data.id}</div>
            {data.stripe_invoice_id ? (
              <div className="mt-0.5 text-xs text-gray-500">Stripe · {data.stripe_invoice_id}</div>
            ) : null}
          </div>
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest ${
              data.status === 'paid'
                ? 'bg-emerald-500/15 text-emerald-300'
                : data.status === 'failed' || data.status === 'payment_failed'
                ? 'bg-red-500/15 text-red-300'
                : 'bg-amber-500/15 text-amber-300'
            }`}
          >
            {data.status}
          </span>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-gray-500">Customer</div>
            <div className="text-white">{data.customer.name ?? '—'}</div>
            <div className="text-xs text-gray-500">{data.customer.type}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-widest text-gray-500">Billing period</div>
            <div className="text-white">
              {data.billing_period.start
                ? new Date(data.billing_period.start).toLocaleDateString()
                : '—'}{' '}
              →{' '}
              {data.billing_period.end
                ? new Date(data.billing_period.end).toLocaleDateString()
                : '—'}
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
        <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Line items</div>
        <table className="min-w-full divide-y divide-gray-800 text-sm">
          <tbody className="divide-y divide-gray-800">
            {data.line_items.map((li, i) => (
              <tr key={i}>
                <td className="py-2 pr-4 text-gray-200">{li.description}</td>
                <td className="py-2 text-right tabular-nums text-gray-200">
                  {fmt(li.amount_pence, data.currency)}
                </td>
              </tr>
            ))}
            <tr>
              <td className="py-2 pr-4 text-gray-500">Subtotal</td>
              <td className="py-2 text-right tabular-nums">{fmt(data.subtotal_pence, data.currency)}</td>
            </tr>
            <tr>
              <td className="py-2 pr-4 text-gray-500">Taxes</td>
              <td className="py-2 text-right tabular-nums">{fmt(data.tax_pence, data.currency)}</td>
            </tr>
            <tr>
              <td className="py-2 pr-4 text-gray-500">Overage charges</td>
              <td className="py-2 text-right tabular-nums">{fmt(data.overage_pence, data.currency)}</td>
            </tr>
            <tr>
              <td className="py-2 pr-4 text-gray-500">Discounts</td>
              <td className="py-2 text-right tabular-nums">
                {fmt(-Math.abs(data.discount_pence), data.currency)}
              </td>
            </tr>
            <tr className="border-t border-gray-800">
              <td className="py-3 pr-4 font-bold text-white">Total</td>
              <td className="py-3 text-right text-base font-bold tabular-nums text-white">
                {fmt(data.total_pence, data.currency)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
        <div className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
          Payment attempts ({data.payment_attempts.length})
        </div>
        {data.payment_attempts.length === 0 ? (
          <div className="text-sm text-gray-500">No recorded payment attempts.</div>
        ) : (
          <ul className="space-y-1.5 text-sm">
            {data.payment_attempts.map((a) => (
              <li key={a.id} className="flex items-center justify-between gap-3">
                <span className="text-gray-300">
                  {a.timestamp ? new Date(a.timestamp).toLocaleString() : '—'} · {a.action}
                </span>
                {a.status ? (
                  <span className="text-xs text-gray-500">{String(a.status)}</span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setRawOpen((s) => !s)}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
        >
          <Code2 className="h-3.5 w-3.5" /> {rawOpen ? 'Hide' : 'Open'} Raw Invoice (JSON)
        </button>
        {data.invoice_pdf_url ? (
          <a
            href={data.invoice_pdf_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
          >
            <Download className="h-3.5 w-3.5" /> Download Invoice PDF
          </a>
        ) : (
          <button
            disabled
            title="No PDF URL on file"
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-800 bg-gray-900/50 px-3 py-1.5 text-xs text-gray-600"
          >
            <FileText className="h-3.5 w-3.5" /> Download Invoice PDF
          </button>
        )}
      </div>

      {rawOpen ? (
        <pre className="max-h-96 overflow-auto rounded-lg border border-gray-800 bg-gray-950 p-4 text-[11px] text-gray-300">
          {JSON.stringify(data, null, 2)}
        </pre>
      ) : null}
    </div>
  )
}
