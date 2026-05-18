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

describe('billing_inspector_overview', () => {
  beforeEach(() => {
    mockAxios.__instance.get.mockReset()
  })

  it('calls GET /overview', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        total_tenants: 10,
        total_freelancers: 3,
        total_mrr_gbp: 1250,
        tenant_mrr_gbp: 1100,
        freelancer_mrr_gbp: 150,
        upcoming_invoices_count: 5,
        overdue_invoices_count: 1,
        recent_payment_failures: [],
        global_overage_alerts: [],
      },
    })
    const res = await billingInspectorApi.overview()
    expect(mockAxios.__instance.get).toHaveBeenCalledWith('/overview')
    expect(res.data.total_tenants).toBe(10)
    expect(res.data.total_mrr_gbp).toBe(1250)
  })

  it('parses recent_payment_failures and overage alerts', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        total_tenants: 1,
        total_freelancers: 0,
        total_mrr_gbp: 0,
        tenant_mrr_gbp: 0,
        freelancer_mrr_gbp: 0,
        upcoming_invoices_count: 0,
        overdue_invoices_count: 2,
        recent_payment_failures: [
          { invoice_id: 'inv-1', tenant_id: 't-1', amount_pence: 5000, status: 'failed', created_at: null },
        ],
        global_overage_alerts: [
          { entity_type: 'tenant', entity_id: 't-1', entity_name: 'Acme', flag: 'seats_over_plan_limit' },
        ],
      },
    })
    const res = await billingInspectorApi.overview()
    expect(res.data.recent_payment_failures).toHaveLength(1)
    expect(res.data.recent_payment_failures[0].status).toBe('failed')
    expect(res.data.global_overage_alerts[0].flag).toBe('seats_over_plan_limit')
  })
})
