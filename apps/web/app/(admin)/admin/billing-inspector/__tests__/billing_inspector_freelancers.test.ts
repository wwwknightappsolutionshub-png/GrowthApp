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

describe('billing_inspector_freelancers', () => {
  beforeEach(() => {
    mockAxios.__instance.get.mockReset()
  })

  it('calls GET /freelancers and forwards tier filter', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: { items: [], total: 0, page: 1, page_size: 20 },
    })
    await billingInspectorApi.listFreelancers({ page: 1, page_size: 20, plan: '51-100' })
    expect(mockAxios.__instance.get).toHaveBeenCalledWith('/freelancers', {
      params: { page: 1, page_size: 20, plan: '51-100' },
    })
  })

  it('parses freelancer row including override / source / tier', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        items: [
          {
            user_id: 'u-1',
            freelancer_name: 'Jane Doe',
            email: 'jane@example.com',
            managed_clients: 120,
            auto_plan_tier: '>100',
            calculated_price_gbp: 140,
            override_price_gbp: 200,
            monthly_price_gbp: 200,
            calculation_source: 'manual',
            last_invoice_status: null,
            next_billing_date: null,
            overage_alerts: ['manual_override_above_auto'],
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      },
    })
    const res = await billingInspectorApi.listFreelancers()
    expect(res.data.items[0].auto_plan_tier).toBe('>100')
    expect(res.data.items[0].calculation_source).toBe('manual')
    expect(res.data.items[0].monthly_price_gbp).toBe(200)
  })
})
