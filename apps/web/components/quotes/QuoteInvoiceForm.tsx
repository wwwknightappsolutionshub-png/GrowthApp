'use client'

/** Shared draft line-item form for quotes and invoices (GBP, pence). */

export type LineItemDraft = {
  description: string
  quantity: number
  unit_price_pence: number
  vat_rate: number
}

export function poundsToPence(value: string): number {
  const n = parseFloat(value || '0')
  if (Number.isNaN(n) || n < 0) return 0
  return Math.round(n * 100)
}

export function lineItemFromPounds(description: string, pounds: string, quantity = 1, vat_rate = 20): LineItemDraft {
  return {
    description: description || 'Line item',
    quantity,
    unit_price_pence: poundsToPence(pounds),
    vat_rate,
  }
}

export const inputClass =
  'w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-950 text-white text-sm placeholder:text-brand-teal-100/40 focus:border-brand-teal-500 focus:outline-none focus:ring-2 focus:ring-brand-teal-500/40'

export const labelClass = 'block text-xs font-semibold uppercase tracking-widest text-brand-teal-100/70 mb-1'
