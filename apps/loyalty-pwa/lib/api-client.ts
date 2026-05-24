/* eslint-disable @typescript-eslint/no-explicit-any */
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
  points_earned: number
  points_redeemed: number
  points_expiring_soon: number
  pending_redemptions: number
  tier_code: string
  tier_name: string
  tier_benefits: unknown[]
  next_tier_name: string | null
  points_to_next_tier: number
  tier_progress_percent: number
  must_change_password: boolean
  push_notifications_enabled: boolean
  date_of_birth: string | null
  marketing_email: boolean
  marketing_sms: boolean
  birthday_participation: boolean
  expiring_points_reminders: boolean
  tenant_slug: string
  tenant_name: string
}

export type PortalUpsell = {
  memberships_url: string
  refer_win_url: string
  booking_url: string
  google_review_url: string | null
  google_review_available: boolean
  has_membership_plans: boolean
  active_subscription: {
    plan_name: string
    plan_description: string | null
    price_pence: number
    billing_cycle: string
    current_period_end: string | null
    benefits: string[]
  } | null
  targeted_offers: Array<{ type: string; title: string; body: string; cta_label: string; cta_url: string }>
}

export type RewardItem = {
  id: string
  name: string
  description: string | null
  points_cost: number
  reward_type: string
  stock_remaining: number | null
}

export type PendingRedemption = {
  id: string
  reward_name: string
  fulfillment_code: string
  points_spent: number
  code_expires_at: string | null
}

export type LedgerEntry = {
  id: string
  amount: number
  balance_after: number
  source: string
  description: string | null
  created_at: string
  expires_at?: string | null
}

export type WalletNotification = {
  id: string
  kind: string
  title: string
  body: string | null
  link: string | null
  read_at: string | null
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

  upsell: (tenant: string) =>
    api.get<PortalUpsell>('/loyalty-portal/me/upsell', { headers: authHeaders(tenant) }),

  updatePreferences: (
    tenant: string,
    data: Partial<{
      date_of_birth: string | null
      marketing_email: boolean
      marketing_sms: boolean
      birthday_participation: boolean
      expiring_points_reminders: boolean
    }>,
  ) =>
    api.patch('/loyalty-portal/me/preferences', data, { headers: authHeaders(tenant) }),

  rewards: (tenant: string) =>
    api.get<{ items: RewardItem[] }>('/loyalty-portal/rewards', {
      headers: authHeaders(tenant),
    }),

  redeem: (tenant: string, rewardId: string) =>
    api.post<{
      reward_name?: string
      fulfillment_code?: string
      code_expires_at?: string
    }>(`/loyalty-portal/rewards/${rewardId}/redeem`, {}, { headers: authHeaders(tenant) }),

  pendingRedemptions: (tenant: string) =>
    api.get<{ items: PendingRedemption[] }>('/loyalty-portal/redemptions/pending', {
      headers: authHeaders(tenant),
    }),

  history: (tenant: string, limit = 50) =>
    api.get<{ items: LedgerEntry[]; has_more: boolean }>('/loyalty-portal/history', {
      headers: authHeaders(tenant),
      params: { limit },
    }),

  qr: (tenant: string) =>
    api.get<{ qr_data_url: string; expires_at: string }>('/loyalty-portal/qr', {
      headers: authHeaders(tenant),
    }),

  pushPublicKey: () =>
    api.get<{ public_key: string; configured: boolean }>('/notifications/push/public-key'),

  pushSubscribe: (
    tenant: string,
    subscription: { endpoint: string; keys: { p256dh: string; auth: string } },
  ) =>
    api.post('/loyalty-portal/push/subscribe', subscription, { headers: authHeaders(tenant) }),

  pushUnsubscribe: (tenant: string) =>
    api.post('/loyalty-portal/push/unsubscribe', {}, { headers: authHeaders(tenant) }),

  listNotifications: (tenant: string, limit = 25, offset = 0) =>
    api.get<{ items: WalletNotification[]; unread: number; limit: number; offset: number }>(
      '/loyalty-portal/notifications',
      { headers: authHeaders(tenant), params: { limit, offset } },
    ),

  unreadCount: (tenant: string) =>
    api.get<{ unread: number }>('/loyalty-portal/notifications/unread-count', {
      headers: authHeaders(tenant),
    }),

  markNotificationRead: (tenant: string, notificationId: string) =>
    api.post<WalletNotification>(
      `/loyalty-portal/notifications/${notificationId}/read`,
      {},
      { headers: authHeaders(tenant) },
    ),

  markAllNotificationsRead: (tenant: string) =>
    api.post<{ updated: number }>('/loyalty-portal/notifications/read-all', {}, {
      headers: authHeaders(tenant),
    }),
}
