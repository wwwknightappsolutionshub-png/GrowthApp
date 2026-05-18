import { describe, expect, it, vi, beforeEach } from 'vitest'

vi.mock('axios', () => {
  const instance = {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
    defaults: { headers: { common: {} } },
  }
  return {
    default: {
      create: vi.fn(() => instance),
      __instance: instance,
    },
  }
})

import axios from 'axios'
import { billingInspectorApi } from '@/lib/api-client'

const mockAxios = axios as unknown as { __instance: { get: ReturnType<typeof vi.fn> } }

describe('billing_inspector_invoice', () => {
  beforeEach(() => {
    mockAxios.__instance.get.mockReset()
  })

  it('calls GET /invoice/{invoiceId}', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        id: 'inv-1',
        customer: { type: 'tenant', id: 't-1', name: 'Acme' },
        billing_period: { start: null, end: null },
        stripe_invoice_id: null,
        line_items: [],
        subtotal_pence: 0,
        tax_pence: 0,
        overage_pence: 0,
        discount_pence: 0,
        total_pence: 0,
        currency: 'gbp',
        status: 'paid',
        invoice_pdf_url: null,
        created_at: null,
        payment_attempts: [],
      },
    })
    const res = await billingInspectorApi.invoice('inv-1')
    expect(mockAxios.__instance.get).toHaveBeenCalledWith('/invoice/inv-1')
    expect(res.data.id).toBe('inv-1')
  })

  it('parses totals, taxes, overage and discount breakdown', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        id: 'inv-2',
        customer: { type: 'tenant', id: 't-2', name: 'Beta' },
        billing_period: { start: '2026-05-01', end: '2026-05-31' },
        stripe_invoice_id: 'in_xxx',
        line_items: [{ description: 'Subscription', amount_pence: 20000 }],
        subtotal_pence: 20000,
        tax_pence: 4000,
        overage_pence: 1500,
        discount_pence: 500,
        total_pence: 25000,
        currency: 'gbp',
        status: 'paid',
        invoice_pdf_url: 'https://x/inv.pdf',
        created_at: null,
        payment_attempts: [{ id: 'a-1', timestamp: null, action: 'payment_succeeded', status: 'ok', metadata: {} }],
      },
    })
    const res = await billingInspectorApi.invoice('inv-2')
    expect(res.data.line_items).toHaveLength(1)
    expect(res.data.tax_pence).toBe(4000)
    expect(res.data.payment_attempts).toHaveLength(1)
    expect(res.data.invoice_pdf_url).toMatch(/inv\.pdf$/)
  })
})
