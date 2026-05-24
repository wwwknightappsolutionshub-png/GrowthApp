import axios, { type AxiosInstance } from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? ''

export const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

export type Branding = {
  tenant_slug: string
  tenant_name: string
  logo_url: string | null
  primary_color: string
  rewards_portal_url: string
  loyalty_enabled: boolean
}

export type CustomerProfile = {
  customer_id: string
  first_name: string
  last_name: string | null
  email: string | null
  phone: string | null
  points_balance: number
  points_lifetime: number
  tier_code: string
  tier_name: string
  tier_benefits: unknown[]
  must_change_password: boolean
  tenant_slug: string
  tenant_name: string
}

export type RewardItem = {
  id: string
  name: string
  description: string | null
  points_cost: number
  reward_type: string
  stock_remaining: number | null
}

export type LedgerEntry = {
  id: string
  amount: number
  balance_after: number
  source: string
  description: string | null
  created_at: string
}

function authHeaders(tenant: string) {
  if (typeof window === 'undefined') return {}
  const token = localStorage.getItem(`loyalty:${tenant}:token`)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const loyaltyPortal = {
  branding: (tenant: string) =>
    api.get<Branding>(`/loyalty-portal/public/branding/${encodeURIComponent(tenant)}`),

  requestMagicLink: (tenant: string, email: string) =>
    api.post('/loyalty-portal/auth/magic-link', { email, tenant_slug: tenant }),

  verifyMagicLink: (tenant: string, token: string) =>
    api.post<{ access_token: string; customer_id: string }>(
      '/loyalty-portal/auth/magic-link/verify',
      { token, tenant_slug: tenant },
    ),

  login: (tenant: string, email: string, password: string) =>
    api.post<{ access_token: string; must_change_password?: boolean }>(
      '/loyalty-portal/auth/login',
      { email, password, tenant_slug: tenant },
    ),

  setPassword: (tenant: string, newPassword: string) =>
    api.post(
      '/loyalty-portal/auth/set-password',
      { new_password: newPassword },
      { headers: authHeaders(tenant) },
    ),

  me: (tenant: string) =>
    api.get<CustomerProfile>('/loyalty-portal/me', { headers: authHeaders(tenant) }),

  rewards: (tenant: string) =>
    api.get<{ items: RewardItem[] }>('/loyalty-portal/rewards', {
      headers: authHeaders(tenant),
    }),

  redeem: (tenant: string, rewardId: string) =>
    api.post(`/loyalty-portal/rewards/${rewardId}/redeem`, {}, { headers: authHeaders(tenant) }),

  history: (tenant: string, limit = 50) =>
    api.get<{ items: LedgerEntry[]; has_more: boolean }>('/loyalty-portal/history', {
      headers: authHeaders(tenant),
      params: { limit },
    }),

  qr: (tenant: string) =>
    api.get<{ qr_data_url: string; expires_at: string }>('/loyalty-portal/qr', {
      headers: authHeaders(tenant),
    }),

  pushSubscribe: (
    tenant: string,
    subscription: { endpoint: string; keys: { p256dh: string; auth: string } },
  ) =>
    api.post('/loyalty-portal/push/subscribe', subscription, { headers: authHeaders(tenant) }),
}
