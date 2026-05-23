'use client'

import { inputClass, labelClass } from '@/components/quotes/QuoteInvoiceForm'

export type InvoiceFilterState = {
  title: string
  invoice_number: string
  total_min: string
  total_max: string
  due_date_from: string
  due_date_to: string
}

export type QuoteFilterState = {
  title: string
  quote_number: string
  total_min: string
  total_max: string
  valid_until_from: string
  valid_until_to: string
}

export function InvoiceListFilters({
  value,
  onChange,
}: {
  value: InvoiceFilterState
  onChange: (v: InvoiceFilterState) => void
}) {
  const set = (k: keyof InvoiceFilterState, v: string) => onChange({ ...value, [k]: v })
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 rounded-xl border border-brand-forest-700 bg-brand-forest-900/60 p-4">
      <div>
        <label className={labelClass}>Title</label>
        <input className={inputClass} value={value.title} onChange={(e) => set('title', e.target.value)} placeholder="Search title" />
      </div>
      <div>
        <label className={labelClass}>Invoice #</label>
        <input className={inputClass} value={value.invoice_number} onChange={(e) => set('invoice_number', e.target.value)} placeholder="INV-0001" />
      </div>
      <div>
        <label className={labelClass}>Total min (£)</label>
        <input className={inputClass} type="number" min="0" step="0.01" value={value.total_min} onChange={(e) => set('total_min', e.target.value)} />
      </div>
      <div>
        <label className={labelClass}>Total max (£)</label>
        <input className={inputClass} type="number" min="0" step="0.01" value={value.total_max} onChange={(e) => set('total_max', e.target.value)} />
      </div>
      <div>
        <label className={labelClass}>Due from</label>
        <input className={inputClass} type="date" value={value.due_date_from} onChange={(e) => set('due_date_from', e.target.value)} />
      </div>
      <div>
        <label className={labelClass}>Due to</label>
        <input className={inputClass} type="date" value={value.due_date_to} onChange={(e) => set('due_date_to', e.target.value)} />
      </div>
    </div>
  )
}

export function QuoteListFilters({
  value,
  onChange,
}: {
  value: QuoteFilterState
  onChange: (v: QuoteFilterState) => void
}) {
  const set = (k: keyof QuoteFilterState, v: string) => onChange({ ...value, [k]: v })
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 rounded-xl border border-brand-forest-700 bg-brand-forest-900/60 p-4">
      <div>
        <label className={labelClass}>Title</label>
        <input className={inputClass} value={value.title} onChange={(e) => set('title', e.target.value)} placeholder="Search title" />
      </div>
      <div>
        <label className={labelClass}>Quote #</label>
        <input className={inputClass} value={value.quote_number} onChange={(e) => set('quote_number', e.target.value)} placeholder="QT-0001" />
      </div>
      <div>
        <label className={labelClass}>Total min (£)</label>
        <input className={inputClass} type="number" min="0" step="0.01" value={value.total_min} onChange={(e) => set('total_min', e.target.value)} />
      </div>
      <div>
        <label className={labelClass}>Total max (£)</label>
        <input className={inputClass} type="number" min="0" step="0.01" value={value.total_max} onChange={(e) => set('total_max', e.target.value)} />
      </div>
      <div>
        <label className={labelClass}>Valid until from</label>
        <input className={inputClass} type="date" value={value.valid_until_from} onChange={(e) => set('valid_until_from', e.target.value)} />
      </div>
      <div>
        <label className={labelClass}>Valid until to</label>
        <input className={inputClass} type="date" value={value.valid_until_to} onChange={(e) => set('valid_until_to', e.target.value)} />
      </div>
    </div>
  )
}

export function buildInvoiceQueryParams(
  filters: InvoiceFilterState,
  extra?: { category?: string },
): Record<string, string | number> {
  const p: Record<string, string | number> = {}
  if (extra?.category) p.category = extra.category
  if (filters.title) p.title = filters.title
  if (filters.invoice_number) p.invoice_number = filters.invoice_number
  if (filters.total_min) p.total_min = Math.round(parseFloat(filters.total_min) * 100)
  if (filters.total_max) p.total_max = Math.round(parseFloat(filters.total_max) * 100)
  if (filters.due_date_from) p.due_date_from = filters.due_date_from
  if (filters.due_date_to) p.due_date_to = filters.due_date_to
  return p
}

export function buildQuoteQueryParams(filters: QuoteFilterState): Record<string, string | number> {
  const p: Record<string, string | number> = {}
  if (filters.title) p.title = filters.title
  if (filters.quote_number) p.quote_number = filters.quote_number
  if (filters.total_min) p.total_min = Math.round(parseFloat(filters.total_min) * 100)
  if (filters.total_max) p.total_max = Math.round(parseFloat(filters.total_max) * 100)
  if (filters.valid_until_from) p.valid_until_from = filters.valid_until_from
  if (filters.valid_until_to) p.valid_until_to = filters.valid_until_to
  return p
}
