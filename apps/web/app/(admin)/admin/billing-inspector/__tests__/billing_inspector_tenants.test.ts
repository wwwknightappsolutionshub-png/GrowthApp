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

describe('billing_inspector_tenants', () => {
  beforeEach(() => {
    mockAxios.__instance.get.mockReset()
  })

  it('calls GET /tenants with no params', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: { items: [], total: 0, page: 1, page_size: 20 },
    })
    await billingInspectorApi.listTenants()
    expect(mockAxios.__instance.get).toHaveBeenCalledWith('/tenants', { params: undefined })
  })

  it('forwards plan / overage_state / invoice_status filters', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({ data: { items: [], total: 0, page: 2, page_size: 50 } })
    await billingInspectorApi.listTenants({
      page: 2,
      page_size: 50,
      plan: 'Growth',
      overage_state: 'any',
      invoice_status: 'paid',
    })
    expect(mockAxios.__instance.get).toHaveBeenCalledWith('/tenants', {
      params: { page: 2, page_size: 50, plan: 'Growth', overage_state: 'any', invoice_status: 'paid' },
    })
  })

  it('parses tenant row shape (plan, contacts, seats, alerts)', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        items: [
          {
            tenant_id: 't-1',
            tenant_name: 'Acme',
            plan_id: 'p-1',
            plan_name: 'Growth',
            monthly_price_gbp: 200,
            contacts_count: 1500,
            active_seats: 4,
            last_invoice_status: 'paid',
            next_billing_date: '2026-06-01T00:00:00Z',
            overage_alerts: ['seats_over_plan_limit'],
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      },
    })
    const res = await billingInspectorApi.listTenants()
    expect(res.data.items).toHaveLength(1)
    expect(res.data.items[0].overage_alerts).toContain('seats_over_plan_limit')
    expect(res.data.items[0].plan_name).toBe('Growth')
  })
})
