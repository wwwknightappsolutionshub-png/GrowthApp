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

describe('billing_inspector_freelancer_profile', () => {
  beforeEach(() => {
    mockAxios.__instance.get.mockReset()
  })

  it('calls GET /freelancer/{id}', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        freelancer: { id: 'u-1', full_name: 'Jane', email: 'j@x.com', phone: null, managed_clients_signup: 30, created_at: null },
        managed_clients_count: 30,
        auto_calculated_plan: null,
        auto_upgrade_logic: { tier_1_50_gbp: 50, tier_51_100_gbp: 40, tier_over_100_base_gbp: 40, per_extra_client_gbp: 5, notes: '' },
        invoice_history: [],
        payment_method: null,
        usage_records: [],
      },
    })
    const res = await billingInspectorApi.freelancerProfile('u-1')
    expect(mockAxios.__instance.get).toHaveBeenCalledWith('/freelancer/u-1')
    expect(res.data.freelancer.full_name).toBe('Jane')
  })

  it('parses auto-computed plan fields (tier, calculated, override, effective, source)', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        freelancer: { id: 'u-2', full_name: 'Bob', email: 'b@x.com', phone: null, managed_clients_signup: 150, created_at: null },
        managed_clients_count: 150,
        auto_calculated_plan: {
          tier: '>100',
          calculated_price_gbp: 290,
          override_price_gbp: null,
          effective_price_gbp: 290,
          calculation_source: 'auto',
        },
        auto_upgrade_logic: { tier_1_50_gbp: 50, tier_51_100_gbp: 40, tier_over_100_base_gbp: 40, per_extra_client_gbp: 5, notes: '' },
        invoice_history: [],
        payment_method: null,
        usage_records: [],
      },
    })
    const res = await billingInspectorApi.freelancerProfile('u-2')
    expect(res.data.auto_calculated_plan?.tier).toBe('>100')
    expect(res.data.auto_calculated_plan?.calculated_price_gbp).toBe(290)
    expect(res.data.auto_calculated_plan?.calculation_source).toBe('auto')
  })
})
