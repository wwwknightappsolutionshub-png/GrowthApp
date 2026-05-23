'use client'

import { inputClass, labelClass } from '@/components/quotes/QuoteInvoiceForm'

export const RECURRENCY_OPTIONS = [
  { value: '', label: 'None' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'bi_yearly', label: 'Bi-Yearly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'monthly', label: 'Monthly' },
] as const

export function recurrencyLabel(value: string | null | undefined): string {
  return RECURRENCY_OPTIONS.find((o) => o.value === value)?.label ?? '—'
}

export function RecurrencySelect({
  value,
  onChange,
}: {
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div>
      <label className={labelClass}>Recurrency</label>
      <select className={inputClass} value={value} onChange={(e) => onChange(e.target.value)}>
        {RECURRENCY_OPTIONS.map((o) => (
          <option key={o.value || 'none'} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <p className="mt-1 text-[11px] text-brand-teal-100/50">
        For renewal reminders only — not automatic billing.
      </p>
    </div>
  )
}
