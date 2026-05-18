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

describe('billing_inspector_tenant_profile', () => {
  beforeEach(() => {
    mockAxios.__instance.get.mockReset()
  })

  it('calls GET /tenant/{id}', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        tenant: { id: 't-1', name: 'Acme', slug: 'acme', business_type: 'plumber', email: null, phone: null, postcode: 'SW1A', is_active: true, created_at: null },
        current_plan: null,
        usage: { seats: { used: 0, limit: null }, contacts: { used: 0, limit: null } },
        subscription: null,
        payment_method: null,
        invoice_history: [],
        overage_details: { alerts: [], contacts: { used: 0, limit: null, over: false }, seats: { used: 0, limit: null, over: false } },
        audit_trail: [],
        plan_alignment: { current_plan_id: null, current_plan_name: null, recommended_plan_id: null, recommended_plan_name: null, aligned: false, reason: null },
      },
    })
    const res = await billingInspectorApi.tenantProfile('t-1')
    expect(mockAxios.__instance.get).toHaveBeenCalledWith('/tenant/t-1')
    expect(res.data.tenant.id).toBe('t-1')
  })

  it('parses full profile (plan, usage, alignment, audit_trail)', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        tenant: { id: 't-1', name: 'Acme', slug: 'acme', business_type: 'plumber', email: null, phone: null, postcode: 'SW1A', is_active: true, created_at: '2026-01-01' },
        current_plan: { id: 'p-1', name: 'Growth', monthly_price_gbp: 200, max_users: 5, max_leads_per_month: 1000, ai_lead_requests_per_month: 10 },
        usage: { seats: { used: 6, limit: 5 }, contacts: { used: 1200, limit: 1000 } },
        subscription: null,
        payment_method: 'stripe:cus_123',
        invoice_history: [{ id: 'inv-1', amount_pence: 20000, currency: 'gbp', status: 'paid', period_start: null, period_end: null, invoice_pdf_url: null, created_at: null }],
        overage_details: { alerts: ['seats_over_plan_limit', 'contacts_over_plan_limit'], contacts: { used: 1200, limit: 1000, over: true }, seats: { used: 6, limit: 5, over: true } },
        audit_trail: [{ id: 'a-1', action: 'plan_change', resource: 'subscription', resource_id: null, metadata: {}, created_at: null }],
        plan_alignment: { current_plan_id: 'p-1', current_plan_name: 'Growth', recommended_plan_id: 'p-2', recommended_plan_name: 'Pro', aligned: false, reason: 'current_plan_limits_exceeded_or_overpaying' },
      },
    })
    const res = await billingInspectorApi.tenantProfile('t-1')
    expect(res.data.overage_details.alerts).toContain('seats_over_plan_limit')
    expect(res.data.plan_alignment.aligned).toBe(false)
    expect(res.data.invoice_history[0].status).toBe('paid')
  })
})
