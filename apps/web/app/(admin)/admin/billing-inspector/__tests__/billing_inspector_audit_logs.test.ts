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

describe('billing_inspector_audit_logs', () => {
  beforeEach(() => {
    mockAxios.__instance.get.mockReset()
  })

  it('calls GET /audit-logs', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: { items: [], total: 0, page: 1, page_size: 50 },
    })
    await billingInspectorApi.auditLogs()
    expect(mockAxios.__instance.get).toHaveBeenCalledWith('/audit-logs', { params: undefined })
  })

  it('forwards type filter', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({ data: { items: [], total: 0, page: 1, page_size: 50 } })
    await billingInspectorApi.auditLogs({ page: 1, page_size: 50, type: 'payment_failure' })
    expect(mockAxios.__instance.get).toHaveBeenCalledWith('/audit-logs', {
      params: { page: 1, page_size: 50, type: 'payment_failure' },
    })
  })

  it('parses items with classified type + entity + metadata JSON', async () => {
    mockAxios.__instance.get.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'a-1',
            timestamp: '2026-05-12T10:00:00Z',
            type: 'plan_change',
            entity_type: 'tenant',
            entity_id: 't-1',
            entity_name: 'Acme',
            description: 'plan_change on subscription',
            metadata: { from: 'starter', to: 'growth' },
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      },
    })
    const res = await billingInspectorApi.auditLogs()
    expect(res.data.items[0].type).toBe('plan_change')
    expect(res.data.items[0].metadata.to).toBe('growth')
  })
})
