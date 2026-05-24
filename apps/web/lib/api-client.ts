import axios, { AxiosError, type AxiosInstance } from 'axios'

// When NEXT_PUBLIC_API_URL is unset we use a same-origin relative path. The
// Next.js rewrite in next.config.js proxies /api/v1/* to the FastAPI server,
// which means the httpOnly cookies set by the API are visible to both the
// Next.js middleware and to fetch() calls — no cross-origin SameSite issues.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? ''

// Authentication uses httpOnly cookies (access_token + refresh_token) set by
// the FastAPI auth endpoints. The browser cannot read those cookies, which
// means JWTs are inaccessible to XSS.
export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

/** Public booking pages — no auth cookies (avoids session interference). */
export const publicApiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: false,
})

publicApiClient.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => Promise.reject(normalizeApiError(error)),
)

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const activeClientId = window.localStorage.getItem('cf:freelancer:activeClientId')
    if (activeClientId) {
      config.headers.set('X-Freelancer-Client-Id', activeClientId)
    }
  }
  return config
})

// AI Scraper is mounted at `/api/superadmin/ai-scraper` (outside /api/v1),
// so it needs a dedicated client that points to `/api` with that suffix.
export const aiScraperClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api/superadmin/ai-scraper`,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

let _refreshInFlight: Promise<void> | null = null

function formatApiDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          const record = item as { loc?: unknown; msg?: unknown; type?: unknown }
          const location = Array.isArray(record.loc) ? record.loc.join('.') : ''
          const message = typeof record.msg === 'string' ? record.msg : JSON.stringify(item)
          return location ? `${location}: ${message}` : message
        }
        return String(item)
      })
      .join('\n')
  }
  if (detail && typeof detail === 'object') {
    const record = detail as { msg?: unknown; detail?: unknown; message?: unknown }
    if (typeof record.msg === 'string') return record.msg
    if (typeof record.detail === 'string') return record.detail
    if (typeof record.message === 'string') return record.message
    try {
      return JSON.stringify(detail)
    } catch {
      return 'Request failed'
    }
  }
  return detail == null ? 'Request failed' : String(detail)
}

function normalizeApiError(error: AxiosError): AxiosError {
  const data = error.response?.data
  if (data && typeof data === 'object' && 'detail' in data) {
    ;(data as { detail: unknown }).detail = formatApiDetail((data as { detail: unknown }).detail)
  }
  return error
}

async function _refresh(): Promise<void> {
  if (_refreshInFlight) return _refreshInFlight
  _refreshInFlight = (async () => {
    try {
      await axios.post(
        `${API_BASE}/api/v1/auth/refresh`,
        {},
        { withCredentials: true },
      )
    } finally {
      _refreshInFlight = null
    }
  })()
  return _refreshInFlight
}

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }

    // Don't try to refresh on auth endpoints — that's where the 401 originates.
    const url = originalRequest?.url || ''
    const isAuthEndpoint = url.startsWith('/auth/login') || url.startsWith('/auth/refresh') || url.startsWith('/auth/register')

    const detail =
      error.response?.data &&
      typeof error.response.data === 'object' &&
      'detail' in error.response.data
        ? String((error.response.data as { detail: unknown }).detail)
        : ''

    const missingTenantContext = detail.toLowerCase().includes('token missing tenant context')

    if (
      (error.response?.status === 401 || missingTenantContext) &&
      !originalRequest?._retry &&
      !isAuthEndpoint
    ) {
      originalRequest._retry = true
      try {
        await _refresh()
        return apiClient(originalRequest!)
      } catch {
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(normalizeApiError(error))
  },
)

aiScraperClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }
    if (error.response?.status === 401 && !originalRequest?._retry) {
      originalRequest._retry = true
      try {
        await _refresh()
        return aiScraperClient(originalRequest!)
      } catch {
        if (typeof window !== 'undefined') {
          window.location.href = '/login?next=/admin/ai-scraper'
        }
      }
    }
    return Promise.reject(normalizeApiError(error))
  },
)

// Typed API helpers
export const auth = {
  register: (data: object, ref?: string | null) =>
    apiClient.post('/auth/register', data, { params: ref ? { ref } : {} }),
  signupInitiate: (data: object) => apiClient.post('/auth/signup/initiate', data),
  signupVerify: (data: object, ref?: string | null) =>
    apiClient.post('/auth/signup/verify', data, { params: ref ? { ref } : {} }),
  signupResend: (pending_id: string) =>
    apiClient.post('/auth/signup/resend-code', { pending_id, channel: 'email' }),
  completeOnboarding: () => apiClient.post('/auth/onboarding/complete'),
  login: (data: object) => apiClient.post('/auth/login', data),
  logout: () => apiClient.post('/auth/logout'),
  me: () => apiClient.get('/auth/me'),
  forgotPassword: (email: string) => apiClient.post('/auth/forgot-password', { email }),
  resetPassword: (token: string, password: string) => apiClient.post('/auth/reset-password', { token, new_password: password }),
  // 2FA
  setup2FA: () => apiClient.post('/auth/2fa/setup'),
  enable2FA: (data: { code: string }) => apiClient.post('/auth/2fa/enable', data),
  verify2FA: (data: { temp_token: string; code: string }) => apiClient.post('/auth/2fa/verify', data),
  disable2FA: (data: { password: string; code: string }) => apiClient.post('/auth/2fa/disable', data),
  // Magic-link (passwordless)
  requestMagicLink: (email: string, next?: string) =>
    apiClient.post('/auth/magic-link', { email, ...(next ? { next } : {}) }),
  verifyMagicLink: (token: string) => apiClient.post('/auth/magic-link/verify', { token }),
}

export const freelancerBilling = {
  me: () => apiClient.get('/freelancer/billing/me'),
  updateClientCount: (estimated_client_count: number) =>
    apiClient.patch('/freelancer/billing/me', { estimated_client_count }),
}

export const freelancerClients = {
  list: (includeInactive = false) =>
    apiClient.get('/freelancer/clients', { params: { include_inactive: includeInactive } }),
  moduleVisibility: () => apiClient.get<{ enabled_tools: string[] }>('/freelancer/clients/module-visibility'),
  create: (data: object) => apiClient.post('/freelancer/clients', data),
  get: (id: string) => apiClient.get(`/freelancer/clients/${id}`),
  update: (id: string, data: object) => apiClient.patch(`/freelancer/clients/${id}`, data),
  remove: (id: string) => apiClient.delete(`/freelancer/clients/${id}`),
  portfolio: () => apiClient.get('/freelancer/clients/summary/portfolio'),
}

export interface ToolConfig {
  category: string
  enabled_tools: string[]
}

export interface CategoryToolConfig {
  category: string
  enabled_tools: string[]
  is_customised: boolean
  updated_at: string | null
}

export interface ToolMeta {
  href: string
  label: string
}

export const businessSite = {
  getStatus: () => apiClient.get('/tenants/me/business-site'),
  bootstrap: (template_slug?: string) =>
    apiClient.post('/tenants/me/business-site/bootstrap', null, {
      params: template_slug ? { template_slug } : undefined,
    }),
  publish: () => apiClient.post('/tenants/me/business-site/publish'),
  qrDownloadUrl: () => `${API_BASE}/api/v1/tenants/me/business-site/qr.png`,
}

export const tenants = {
  get: () => apiClient.get('/tenants/me'),
  update: (data: object) => apiClient.patch('/tenants/me', data),
  listMembers: () => apiClient.get('/tenants/me/members'),
  inviteMember: (data: object) => apiClient.post('/tenants/me/members/invite', data),
  removeMember: (userId: string) => apiClient.delete(`/tenants/me/members/${userId}`),
  listLocations: () => apiClient.get('/tenants/me/locations'),
  createLocation: (data: object) => apiClient.post('/tenants/me/locations', data),
  /** Returns the effective tool list for this tenant's business category. */
  getToolConfig: () => apiClient.get<ToolConfig>('/tenants/me/tool-config'),
}

export interface LeadQuota {
  month_year: string
  plan_quota: number
  requests_this_month: number
  remaining: number
  current_request: LeadRequestItem | null
}

export interface LeadRequestItem {
  id: string
  tenant_id: string
  month_year: string
  requested_count: number
  approved_count: number | null
  status: 'pending' | 'approved' | 'rejected' | 'fulfilled'
  tenant_notes: string | null
  admin_notes: string | null
  fulfilled_at: string | null
  created_at: string
  updated_at: string
}

export const leads = {
  list: (params?: object) => apiClient.get('/leads', { params }),
  get: (id: string) => apiClient.get(`/leads/${id}`),
  update: (id: string, data: object) => apiClient.patch(`/leads/${id}`, data),
  convert: (id: string) => apiClient.post(`/leads/${id}/convert`),
  delete: (id: string) => apiClient.delete(`/leads/${id}`),
  // Lead request system
  getQuota: () => apiClient.get<LeadQuota>('/leads/quota'),
  submitRequest: (data: { requested_count: number; tenant_notes?: string | null }) =>
    apiClient.post<LeadRequestItem>('/leads/request', data),
  listRequests: () => apiClient.get<LeadRequestItem[]>('/leads/requests'),
  trialStatus: () => apiClient.get<TrialLeadStatus>('/leads/trial-status'),
  sourceCatalog: () => apiClient.get<LeadSourceCatalog>('/leads/source-catalog'),
}

export interface TrialLeadStatus {
  in_trial: boolean
  trial_days_total: number
  trial_day: number
  trial_ends_at: string
  leads_per_day: number
  delivered_today: number
  remaining_today: number
  total_delivered: number
  reminder_sent: boolean
}

export interface LeadSourceCatalog {
  business_type: string
  trade_label: string
  postcode: string
  sources: {
    id: string | null
    name: string
    url_pattern: string
    scraping_type: string
    source_platform: string
    postcode_prefix?: string | null
    region_label?: string | null
    is_catalog_default: boolean
    notes?: string | null
  }[]
}

export const crm = {
  pipeline: () => apiClient.get('/crm/pipeline'),
  listCustomers: (params?: object) => apiClient.get('/crm/customers', { params }),
  getCustomer: (id: string) => apiClient.get(`/crm/customers/${id}`),
  createCustomer: (data: object) => apiClient.post('/crm/customers', data),
  updateCustomer: (id: string, data: object) => apiClient.patch(`/crm/customers/${id}`, data),
  deleteCustomer: (id: string) => apiClient.delete(`/crm/customers/${id}`),
  createDeal: (data: object) => apiClient.post('/crm/deals', data),
  getDeal: (id: string) => apiClient.get(`/crm/deals/${id}`),
  updateDeal: (id: string, data: object) => apiClient.patch(`/crm/deals/${id}`, data),
  moveDeal: (id: string, data: object) => apiClient.post(`/crm/deals/${id}/move`, data),
  moveDealStage: (id: string, data: object) => apiClient.post(`/crm/deals/${id}/move-stage`, data),
  addNote: (id: string, note: string) => apiClient.post(`/crm/deals/${id}/notes`, { note }),

  // Enterprise
  dashboard: () => apiClient.get('/crm/dashboard'),
  listPipelines: () => apiClient.get('/crm/pipelines'),
  createPipeline: (data: object) => apiClient.post('/crm/pipelines', data),
  updatePipeline: (id: string, data: object) => apiClient.patch(`/crm/pipelines/${id}`, data),
  createStage: (pipelineId: string, data: object) =>
    apiClient.post(`/crm/pipelines/${pipelineId}/stages`, data),
  getBoard: (pipelineId?: string) =>
    apiClient.get('/crm/board', { params: pipelineId ? { pipeline_id: pipelineId } : {} }),
  moveBoardCard: (data: object) => apiClient.post('/crm/board/move', data),
  listActivities: (entityType: string, entityId: string) =>
    apiClient.get('/crm/activities', { params: { entity_type: entityType, entity_id: entityId } }),
  getTimeline: (entityType: string, entityId: string) =>
    apiClient.get('/crm/timeline', { params: { entity_type: entityType, entity_id: entityId } }),
  createActivity: (data: object) => apiClient.post('/crm/activities', data),
  listTags: () => apiClient.get('/crm/tags'),
  createTag: (data: object) => apiClient.post('/crm/tags', data),
  assignTags: (data: object) => apiClient.post('/crm/tags/assign', data),
  listCustomFields: (entityType?: string) =>
    apiClient.get('/crm/custom-fields', { params: entityType ? { entity_type: entityType } : {} }),
  createCustomField: (data: object) => apiClient.post('/crm/custom-fields', data),
  setCustomFieldValue: (data: object) => apiClient.put('/crm/custom-fields/values', data),
  listFilters: (entityType?: string) =>
    apiClient.get('/crm/filters', { params: entityType ? { entity_type: entityType } : {} }),
  createFilter: (data: object) => apiClient.post('/crm/filters', data),
  listScoreRules: () => apiClient.get('/crm/score-rules'),
  createScoreRule: (data: object) => apiClient.post('/crm/score-rules', data),
  applyLeadScores: (leadId: string) => apiClient.post(`/crm/leads/${leadId}/apply-scores`),
  enrichLead: (leadId: string) => apiClient.post(`/crm/leads/${leadId}/enrich`),
  bulkUpdate: (data: object) => apiClient.post('/crm/bulk', data),
  scanDuplicates: () => apiClient.post('/crm/duplicates/scan'),
  merge: (data: object) => apiClient.post('/crm/merge', data),
  customerBookings: (customerId: string) => apiClient.get(`/crm/customers/${customerId}/bookings`),
  dealBookings: (dealId: string) => apiClient.get(`/crm/deals/${dealId}/bookings`),
  leadBookings: (leadId: string) => apiClient.get(`/crm/leads/${leadId}/bookings`),
  exportLeadsCsv: () => apiClient.get('/crm/export/leads', { responseType: 'text' }),
  importLeadsCsv: (csv: string) => apiClient.post('/crm/import/leads', { csv }),
}

export const bookings = {
  list: (params?: object) => apiClient.get('/bookings', { params }),
  create: (data: object) => apiClient.post('/bookings', data),
  get: (id: string) => apiClient.get(`/bookings/${id}`),
  update: (id: string, data: object) => apiClient.patch(`/bookings/${id}`, data),
  delete: (id: string) => apiClient.delete(`/bookings/${id}`),
  upcoming: (limit?: number) => apiClient.get('/bookings/upcoming', { params: { limit } }),
  getLinks: () => apiClient.get('/bookings/links'),
  restoreBookingSlug: () => apiClient.post('/bookings/links/restore-slug'),
  getForm: () => apiClient.get('/bookings/form'),
  updateForm: (data: { schema: object; name?: string }) => apiClient.put('/bookings/form', data),
  requestFeedback: (id: string, channels: string[]) =>
    apiClient.post(`/bookings/${id}/request-feedback`, { channels }),
  getSettings: () => apiClient.get('/bookings/settings'),
  updateSettings: (data: object) => apiClient.patch('/bookings/settings', data),
  getLink: () => apiClient.get('/bookings/link'),
  listServices: () => apiClient.get('/bookings/services'),
  createService: (data: object) => apiClient.post('/bookings/services', data),
  updateService: (id: string, data: object) => apiClient.patch(`/bookings/services/${id}`, data),
  listResources: () => apiClient.get('/bookings/resources'),
  createResource: (data: object) => apiClient.post('/bookings/resources', data),
  listStaff: () => apiClient.get('/bookings/staff'),
  createStaff: (data: object) => apiClient.post('/bookings/staff', data),
  updateStaff: (id: string, data: object) => apiClient.patch(`/bookings/staff/${id}`, data),
  deleteStaff: (id: string) => apiClient.delete(`/bookings/staff/${id}`),
  listShifts: (params?: object) => apiClient.get('/bookings/staff/shifts', { params }),
  createShift: (data: object) => apiClient.post('/bookings/staff/shifts', data),
  listBlackouts: () => apiClient.get('/bookings/staff/blackouts'),
  createBlackout: (data: object) => apiClient.post('/bookings/staff/blackouts', data),
  listSlots: (params?: object) => apiClient.get('/bookings/slots', { params }),
  generateSlots: (data: object) => apiClient.post('/bookings/slots/generate', data),
  getAnalytics: (params?: object) => apiClient.get('/bookings/analytics', { params }),
  createPaymentIntent: (data: object) => apiClient.post('/bookings/payments/intent', data),
  refund: (id: string, data: object) => apiClient.post(`/bookings/${id}/refund`, data),
  getTimeline: (id: string) => apiClient.get(`/bookings/${id}/timeline`),
  listPackages: () => apiClient.get('/bookings/packages'),
  createPackage: (data: object) => apiClient.post('/bookings/packages', data),
  createPromo: (data: object) => apiClient.post('/bookings/promo-codes', data),
  exportIcal: () => apiClient.get('/bookings/export/ical', { responseType: 'text' }),
  sendClientReminder: (bookingId: string, channel: 'email' | 'sms') =>
    apiClient.post(`/bookings/${bookingId}/remind`, { channel }),
}

export const publicBooking = {
  widget: (slug: string) => publicApiClient.get(`/public/booking/${slug}/widget`),
  availability: (slug: string, params?: object) =>
    publicApiClient.get(`/public/booking/${slug}/availability`, { params }),
  create: (slug: string, data: object) => publicApiClient.post(`/public/booking/${slug}`, data),
  submitRefer: (slug: string, data: object) => publicApiClient.post(`/public/booking/${slug}/refer`, data),
  getReviewUrl: (slug: string) => publicApiClient.get(`/public/booking/${slug}/review-url`),
  manage: (token: string, data: object) => publicApiClient.post(`/public/booking/manage/${token}`, data),
}

export const quotes = {
  list: (params?: object) => apiClient.get('/quotes', { params }),
  create: (data: object) => apiClient.post('/quotes', data),
  get: (id: string) => apiClient.get(`/quotes/${id}`),
  update: (id: string, data: object) => apiClient.patch(`/quotes/${id}`, data),
  delete: (id: string) => apiClient.delete(`/quotes/${id}`),
  send: (id: string) => apiClient.post(`/quotes/${id}/send`),
  sendInvoice: (id: string) => apiClient.post(`/quotes/${id}/send-invoice`),
}

export const invoices = {
  list: (params?: object) => apiClient.get('/invoices', { params }),
  create: (data: object) => apiClient.post('/invoices', data),
  get: (id: string) => apiClient.get(`/invoices/${id}`),
  update: (id: string, data: object) => apiClient.patch(`/invoices/${id}`, data),
  send: (id: string) => apiClient.post(`/invoices/${id}/send`),
  recordPayment: (id: string, data?: { payment_channel?: 'online' | 'cash_deposit' }) =>
    apiClient.post(`/invoices/${id}/record-payment`, data ?? {}),
  delete: (id: string) => apiClient.delete(`/invoices/${id}`),
}

export const publicFeedback = {
  get: (token: string) => apiClient.get(`/public/booking/feedback/${token}`),
  submit: (token: string, data: { rating: number; feedback_text?: string }) =>
    apiClient.post(`/public/booking/feedback/${token}`, data),
}

export const automations = {
  list: () => apiClient.get('/automations'),
  create: (data: object) => apiClient.post('/automations', data),
  update: (id: string, data: object) => apiClient.patch(`/automations/${id}`, data),
  delete: (id: string) => apiClient.delete(`/automations/${id}`),
  listTemplates: () => apiClient.get('/automations/templates'),
  createTemplate: (data: object) => apiClient.post('/automations/templates', data),
}

export const messaging = {
  conversations: (params?: object) => apiClient.get('/messages/conversations', { params }),
  getConversation: (id: string) => apiClient.get(`/messages/conversations/${id}`),
  send: (data: object) => apiClient.post('/messages/send', data),
}

export const reputation = {
  dashboard: () => apiClient.get('/reputation/dashboard'),
  reviews: (params?: object) => apiClient.get('/reputation/reviews', { params }),
}

export const integrations = {
  googleStatus: () => apiClient.get('/integrations/google/status'),
  googleConnectUrl: () => `${API_BASE}/api/v1/integrations/google/connect`,
  googleDisconnect: () => apiClient.post('/integrations/google/disconnect'),
  googleSelectLocation: (location_name: string) =>
    apiClient.post('/integrations/google/select-location', { location_name }),
  googleSync: () => apiClient.post('/integrations/google/sync'),
  googleReviews: () => apiClient.get('/integrations/google/reviews'),
  googleReply: (reviewId: string, comment: string) =>
    apiClient.post(`/integrations/google/reviews/${reviewId}/reply`, { comment }),

  // Tenant-owned Google OAuth
  googleCredentials: () => apiClient.get('/integrations/google/credentials'),
  googleRegisterCredentials: (data: { google_client_id: string; google_client_secret: string }) =>
    apiClient.post('/integrations/google/register-credentials', data),
  googleAuthUrl: () => apiClient.get('/integrations/google/auth-url'),
  googleRefreshToken: () => apiClient.post('/integrations/google/refresh-token'),
  googleReviewsSync: () => apiClient.get('/integrations/google/reviews/sync'),
  googleMessagesSync: () => apiClient.get('/integrations/google/messages/sync'),
  googlePostsSync: () => apiClient.get('/integrations/google/posts/sync'),
  googlePhotosSync: () => apiClient.get('/integrations/google/photos/sync'),
  googleAnalyticsSync: () => apiClient.get('/integrations/google/analytics/sync'),

  // Social (Zapier/Make)
  socialChannels: () => apiClient.get('/integrations/social/channels'),
  provisionSocialChannel: (platform: string) =>
    apiClient.post(`/integrations/social/channels/${platform}`),
  socialPost: (data: { platform: string; content: string; media_url?: string }) =>
    apiClient.post('/integrations/social/post', data),

  // Onboarding
  integrationsOnboarding: () => apiClient.get('/integrations/onboarding'),
  saveIntegrationsOnboarding: (data: {
    google_connected?: boolean
    social_connected?: boolean
    skipped?: boolean
  }) => apiClient.post('/integrations/onboarding', data),
}

export const social = {
  posts: (params?: object) => apiClient.get('/social/posts', { params }),
  getPost: (id: string) => apiClient.get(`/social/posts/${id}`),
  updatePost: (id: string, data: object) => apiClient.patch(`/social/posts/${id}`, data),
  approvePost: (id: string) => apiClient.post(`/social/posts/${id}/approve`),
  accounts: () => apiClient.get('/social/accounts'),

  // ── AI Social module (Step 2 endpoints) ────────────────────────────────
  setBrandIdentity: (body: {
    brand_colors?: Record<string, string>
    brand_fonts?: Record<string, string>
    tone_of_voice?: string
    logo_url?: string
  }) => apiClient.post('/social/brand-identity/set', body),
  uploadSample: (body: { file_url: string; file_type: 'IMAGE' | 'VIDEO' | 'PDF' }) =>
    apiClient.post('/social/samples/upload', body),
  setPrefs: (body: {
    posts_per_week: number
    preferred_days: string[]
    preferred_time_range?: string
  }) => apiClient.post('/social/prefs/set', body),
  generateDrafts: (body: { count: number; topic_hints?: string[] }) =>
    apiClient.post('/social/generate-drafts', body),
  sendForApproval: (body: {
    draft_id: string
    delivery_channel: 'EMAIL' | 'WHATSAPP'
    recipient_email?: string
    recipient_whatsapp?: string
  }) => apiClient.post('/social/send-for-approval', body),
  approvalWebhook: (body: { draft_id: string; response_text: string; approved: boolean }) =>
    apiClient.post('/social/approval/webhook', body),
  schedule: (body: { draft_id: string; platform: string; scheduled_time?: string }) =>
    apiClient.post('/social/schedule', body),
  publish: (body: { draft_id: string; platform: string }) =>
    apiClient.post('/social/publish', body),
}

export const marketer = {
  createFunnel: (body: { funnel_type?: string; steps_json?: unknown[]; ai_notes?: string }) =>
    apiClient.post('/marketer/funnel/create', body),
  generateAudience: (body: { industry?: string }) =>
    apiClient.post('/marketer/audience-research/generate', body),
  scanCompetitor: (body: { competitor_name?: string; website?: string }) =>
    apiClient.post('/marketer/competitor/scan', body),
  quotas: () => apiClient.get('/marketer/quotas'),
}

export const billing = {
  plans: () => apiClient.get('/billing/plans'),
  subscription: () => apiClient.get('/billing/subscription'),
  checkout: (data: object) => apiClient.post('/billing/checkout', data),
  portal: () => apiClient.post('/billing/portal'),
  invoices: () => apiClient.get('/billing/invoices'),
}

export const tasks = {
  list: (params?: object) => apiClient.get('/tasks', { params }),
  board: () => apiClient.get('/tasks/board'),
  create: (data: object) => apiClient.post('/tasks', data),
  get: (id: string) => apiClient.get(`/tasks/${id}`),
  update: (id: string, data: object) => apiClient.patch(`/tasks/${id}`, data),
  move: (id: string, status: string, position: number) =>
    apiClient.post(`/tasks/${id}/move`, { status, position }),
  delete: (id: string) => apiClient.delete(`/tasks/${id}`),
}

export const notifications = {
  list: (params?: { page?: number; page_size?: number; unread_only?: boolean; include_archived?: boolean }) =>
    apiClient.get('/notifications', { params }),
  markRead: (id: string) => apiClient.post(`/notifications/${id}/read`),
  markAllRead: () => apiClient.post('/notifications/read-all'),
  archive: (id: string) => apiClient.post(`/notifications/${id}/archive`),
  pushPublicKey: () => apiClient.get<{ public_key: string; configured: boolean }>('/notifications/push/public-key'),
  upsertPushSubscription: (body: { endpoint: string; keys: { p256dh: string; auth: string }; user_agent?: string }) =>
    apiClient.post('/notifications/push/subscriptions', body),
  deletePushSubscription: (endpoint: string) =>
    apiClient.delete('/notifications/push/subscriptions', { params: { endpoint } }),
  listPreferences: () => apiClient.get<Array<{ kind: string; label: string; in_app_enabled: boolean; push_enabled: boolean }>>('/notifications/preferences'),
  updatePreferences: (preferences: Array<{ kind: string; in_app_enabled: boolean; push_enabled: boolean }>) =>
    apiClient.put('/notifications/preferences', { preferences }),
}

export const apiKeys = {
  list: () => apiClient.get('/api-keys'),
  create: (data: { name: string; scopes: string[]; expires_at?: string; is_live?: boolean }) =>
    apiClient.post('/api-keys', data),
  revoke: (id: string) => apiClient.delete(`/api-keys/${id}`),
}

export const rbac = {
  catalogue: () => apiClient.get('/rbac/catalogue'),
  me: () => apiClient.get('/rbac/me'),
  listTemplates: () => apiClient.get('/rbac/templates'),
  updateTemplate: (role: string, permissions: string[]) =>
    apiClient.put(`/rbac/templates/${role}`, { permissions }),
  listOverrides: () => apiClient.get('/rbac/overrides'),
  createOverride: (data: { role: string; permission: string; effect: 'grant' | 'revoke' }) =>
    apiClient.post('/rbac/overrides', data),
  deleteOverride: (id: string) => apiClient.delete(`/rbac/overrides/${id}`),
}

export const search = {
  query: (q: string, params?: { types?: string[]; limit_per_type?: number }) =>
    apiClient.get('/search', { params: { q, ...params } }),
}

export const ai = {
  generateReviewReply: (review_id: string, tone?: string) =>
    apiClient.post('/ai/review-reply', { review_id, tone: tone || 'warm and professional' }),
  scoreLead: (lead_id: string) => apiClient.post(`/ai/lead-score/${lead_id}`),
  generateAds: (data: {
    platform: 'google' | 'facebook' | 'instagram' | 'tiktok'
    objective?: 'leads' | 'sales' | 'awareness'
    audience: string
    offer: string
    tone?: string
    variant_count?: number
  }) => apiClient.post('/ai/ads', data),
  seoAudit: (data: {
    page_url: string
    page_title: string
    meta_description?: string
    body_excerpt?: string
    target_keywords?: string[]
    local_area?: string
  }) => apiClient.post('/ai/seo/audit', data),
  onboardingAsk: (question: string, current_screen?: string) =>
    apiClient.post('/ai/onboarding/ask', { question, current_screen }),
}

export const aiAssistant = {
  listThreads: (params?: { include_archived?: boolean }) =>
    apiClient.get('/ai/assistant/threads', { params }),
  createThread: (title?: string) =>
    apiClient.post('/ai/assistant/threads', title ? { title } : {}),
  saveThread: (thread_id: string) => apiClient.post(`/ai/assistant/threads/${thread_id}/save`),
  listMessages: (thread_id: string) =>
    apiClient.get(`/ai/assistant/threads/${thread_id}/messages`),
  sendMessage: (thread_id: string, content: string) =>
    apiClient.post(`/ai/assistant/threads/${thread_id}/messages`, { content }),
}

export const money = {
  dashboard: (days?: number) => apiClient.get('/money/dashboard', { params: { days } }),
}

export const accounts = {
  dashboard: (days?: number) => apiClient.get('/accounts/dashboard', { params: { days } }),
  cashSaved: (params?: object) => apiClient.get('/accounts/cash-saved', { params }),
  reports: (params: { category: string; date_from?: string; date_to?: string }) =>
    apiClient.get('/accounts/reports', { params, responseType: 'blob' }),
}

export type AddonStatusResponse = {
  vertical: 'salon' | 'realtor' | 'garage'
  industry_booking: boolean
  industry_billing: boolean
  industry_crm: boolean
  membership_rewards: boolean
  items: { feature_code: string; active: boolean }[]
}

export const industryAddons = {
  status: () => apiClient.get<AddonStatusResponse>('/addons/status'),
  setVertical: (vertical: 'salon' | 'realtor' | 'garage') =>
    apiClient.patch<AddonStatusResponse>('/addons/vertical', { vertical }),
}

export type MembershipTrialStatus = {
  on_trial: boolean
  trial_expired: boolean
  converted: boolean
  days_remaining: number
  trial_ends_at: string | null
  trial_started_at: string | null
  show_urgency_modal: boolean
  show_winback_banner: boolean
  winback_discount_percent: number
  upgrade_url: string
  setup_url: string
  reminders: Record<string, string | null>
}

export type MembershipRewardsStatus = {
  has_membership_rewards: boolean
  feature_code: string
  status: string | null
  expires_at: string | null
  trial_ends_at: string | null
  landing_url: string | null
  trial?: MembershipTrialStatus | null
  stripe_configured?: boolean
  is_trial?: boolean
  is_paid?: boolean
  billing_source?: 'trial' | 'stripe' | 'grant' | null
}

export type MembershipPlan = {
  id: string
  tenant_id: string
  name: string
  description: string | null
  billing_cycle: string
  price_pence: number
  included_services: string[]
  discount_percent: number
  rollover_enabled: boolean
  rollover_max_periods: number
  cancellation_notice_days: number
  is_active: boolean
  sort_order: number
}

export type MembershipSubscription = {
  id: string
  tenant_id: string
  customer_id: string
  plan_id: string
  status: string
  started_at: string | null
  current_period_end: string | null
  canceled_at: string | null
}

export type RewardCatalogItem = {
  id: string
  name: string
  description: string | null
  points_cost: number
  reward_type: string
  config: Record<string, unknown>
  is_active: boolean
  stock_remaining: number | null
}

export type MembershipTierSummary = {
  code: string
  name: string
  min_points_lifetime: number
  benefits: unknown[]
}

export type MembershipAnalytics = {
  points_by_source: Record<string, number>
  tier_distribution: Record<string, number>
  members_total: number
  members_with_balance: number
  redemptions_total: number
  redemptions_30d: number
  redemption_rate_percent: number
  points_issued_30d: number
  points_redeemed_30d: number
  expiring_points_soon: number
  top_customers: {
    customer_id: string
    customer_name: string | null
    points_balance: number
    points_lifetime: number
    tier_code: string
  }[]
  recent_redemptions: {
    id: string
    customer_id: string
    customer_name: string | null
    reward_name: string
    points_spent: number
    status: string
    created_at: string | null
  }[]
}

export type LoyaltyCustomerRow = {
  customer_id: string
  customer_name: string | null
  email: string | null
  phone: string | null
  points_balance: number
  points_lifetime: number
  tier_code: string
}

export type MembershipLandingConfig = {
  title: string
  meta_description: string | null
  hero: Record<string, unknown>
  benefits: { title?: string; body?: string }[]
  cta_label: string
  cta_href: string | null
  published: boolean
  auto_generated?: boolean
  public_url?: string | null
  preview_path?: string | null
  booking_cta_url?: string | null
  plans: MembershipPlan[]
  tiers?: MembershipTierSummary[]
}

export const membershipRewards = {
  status: () => apiClient.get<MembershipRewardsStatus>('/membership-rewards/status'),
  trialStatus: () => apiClient.get<MembershipTrialStatus>('/membership-rewards/trial'),
  checkout: (data: { success_url: string; cancel_url: string }) =>
    apiClient.post<{ checkout_url: string }>('/membership-rewards/checkout', data),
  dashboard: () =>
    apiClient.get<{
      active_subscriptions: number
      members_with_points: number
      points_issued_lifetime: number
      redemptions_count: number
      active_plans: number
      landing_published: boolean
    }>('/membership-rewards/dashboard'),
  analytics: () => apiClient.get<MembershipAnalytics>('/membership-rewards/analytics'),
  listLoyaltyCustomers: (params?: { search?: string; limit?: number; offset?: number }) =>
    apiClient.get<{ items: LoyaltyCustomerRow[]; total: number; limit: number; offset: number }>(
      '/membership-rewards/loyalty/customers',
      { params },
    ),
  listRedemptions: (params?: { status?: string; limit?: number }) =>
    apiClient.get<{
      items: MembershipAnalytics['recent_redemptions']
    }>('/membership-rewards/redemptions', { params }),
  leaderboard: (limit = 20) =>
    apiClient.get<{
      items: {
        customer_id: string
        customer_name: string | null
        points_balance: number
        points_lifetime: number
        tier_code: string
      }[]
    }>('/membership-rewards/loyalty/leaderboard', { params: { limit } }),
  settings: () => apiClient.get('/membership-rewards/settings'),
  updateSettings: (data: { earn_rules?: Record<string, unknown>; points_expire_days?: number | null }) =>
    apiClient.patch('/membership-rewards/settings', data),
  listPlans: (activeOnly = false) =>
    apiClient.get<{ items: MembershipPlan[] }>('/membership-rewards/plans', {
      params: { active_only: activeOnly },
    }),
  createPlan: (data: object) => apiClient.post<MembershipPlan>('/membership-rewards/plans', data),
  updatePlan: (id: string, data: object) =>
    apiClient.patch<MembershipPlan>(`/membership-rewards/plans/${id}`, data),
  deletePlan: (id: string) => apiClient.delete(`/membership-rewards/plans/${id}`),
  listSubscriptions: (params?: { customer_id?: string; status?: string }) =>
    apiClient.get<{ items: MembershipSubscription[] }>('/membership-rewards/subscriptions', { params }),
  createSubscription: (data: { customer_id: string; plan_id: string; started_at?: string }) =>
    apiClient.post<MembershipSubscription>('/membership-rewards/subscriptions', data),
  cancelSubscription: (id: string) =>
    apiClient.post<MembershipSubscription>(`/membership-rewards/subscriptions/${id}/cancel`),
  listCatalog: () => apiClient.get<{ items: RewardCatalogItem[] }>('/membership-rewards/catalog'),
  createCatalogItem: (data: object) =>
    apiClient.post<RewardCatalogItem>('/membership-rewards/catalog', data),
  updateCatalogItem: (id: string, data: object) =>
    apiClient.patch<RewardCatalogItem>(`/membership-rewards/catalog/${id}`, data),
  deleteCatalogItem: (id: string) => apiClient.delete(`/membership-rewards/catalog/${id}`),
  previewCustomerBroadcast: () =>
    apiClient.get<{ customers: number; push_subscribers: number; email_opted_in: number }>(
      '/membership-rewards/customers/broadcast/preview',
    ),
  sendCustomerBroadcast: (data: {
    title: string
    body: string
    send_push?: boolean
    send_email?: boolean
    path?: string
  }) =>
    apiClient.post<{ customers: number; push_sent: number; email_sent: number }>(
      '/membership-rewards/customers/broadcast',
      data,
    ),
  customerLoyalty: (customerId: string) =>
    apiClient.get<{
      customer_id: string
      points_balance: number
      points_lifetime: number
      tier_code: string
    }>(`/membership-rewards/customers/${customerId}/loyalty`),
  customerLedger: (customerId: string, limit = 50) =>
    apiClient.get<
      {
        id: string
        amount: number
        balance_after: number
        source: string
        description: string | null
        created_at: string
      }[]
    >(`/membership-rewards/customers/${customerId}/ledger`, { params: { limit } }),
  adjustPoints: (data: {
    customer_id: string
    amount: number
    source?: string
    description?: string
  }) => apiClient.post('/membership-rewards/points/adjust', data),
  redeemReward: (customerId: string, catalogItemId: string) =>
    apiClient.post(`/membership-rewards/customers/${customerId}/redeem/${catalogItemId}`),
  getLanding: () => apiClient.get<MembershipLandingConfig>('/membership-rewards/landing'),
  updateLanding: (data: object) => apiClient.patch<MembershipLandingConfig>('/membership-rewards/landing', data),
  publishLanding: () => apiClient.post<MembershipLandingConfig>('/membership-rewards/landing/publish'),
  regenerateLanding: () =>
    apiClient.post<MembershipLandingConfig>('/membership-rewards/landing/regenerate'),
  listTiers: () =>
    apiClient.get<{
      items: {
        id: string
        code: string
        name: string
        min_points_lifetime: number
        benefits: unknown[]
        sort_order: number
      }[]
    }>('/membership-rewards/tiers'),
  updateTier: (
    id: string,
    data: { name?: string; min_points_lifetime?: number; benefits?: unknown[]; sort_order?: number },
  ) => apiClient.patch(`/membership-rewards/tiers/${id}`, data),
  scanQr: (payload: string) =>
    apiClient.post<{
      scan_id: string
      customer_id: string
      customer_name: string | null
      points_awarded: number
      points_balance: number
      tier_code: string
      message: string
    }>('/membership-rewards/qr/scan', { payload }),
  fulfillRedemption: (fulfillmentCode: string) =>
    apiClient.post<{
      id: string
      status: string
      reward_name: string | null
      customer_name: string | null
      points_spent: number
      message: string
    }>('/membership-rewards/redemptions/fulfill', { fulfillment_code: fulfillmentCode }),
  submitInterest: (
    tenantSlug: string,
    data: {
      first_name: string
      last_name?: string
      email?: string
      phone?: string
      message?: string
      plan_id?: string
    },
  ) => publicApiClient.post(`/public/memberships/${tenantSlug}/interest`, data),
  submitLoyaltyEnroll: (
    tenantSlug: string,
    data: { name: string; email: string; phone?: string; tier_code: string },
  ) =>
    publicApiClient.post<{
      message: string
      tier_code: string
      tier_name: string
      signup_bonus_points: number
      points_balance: number
      portal_account_created?: boolean
      rewards_email_sent?: boolean
    }>(`/public/memberships/${tenantSlug}/loyalty-enroll`, data),
}

export type LoyaltyPortalBranding = {
  tenant_slug: string
  tenant_name: string
  logo_url: string | null
  primary_color: string
  rewards_portal_url: string
  loyalty_enabled: boolean
}

export type LoyaltyPortalProfile = {
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
  next_tier_code: string | null
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

export type LoyaltyPortalPreferences = {
  date_of_birth: string | null
  marketing_email: boolean
  marketing_sms: boolean
  birthday_participation: boolean
  expiring_points_reminders: boolean
}

export type LoyaltyPortalUpsell = {
  memberships_url: string
  refer_win_url: string
  booking_url: string
  google_review_url: string | null
  google_review_available: boolean
  has_membership_plans: boolean
  active_subscription: {
    plan_id: string
    plan_name: string
    plan_description: string | null
    billing_cycle: string
    price_pence: number
    discount_percent: number
    benefits: string[]
    status: string
    current_period_end: string | null
  } | null
  targeted_offers: {
    type: string
    title: string
    body: string
    cta_label: string
    cta_url: string
  }[]
  affordable_rewards_count: number
}

export type LoyaltyRewardItem = {
  id: string
  name: string
  description: string | null
  points_cost: number
  reward_type: string
  stock_remaining: number | null
}

export type LoyaltyLedgerEntry = {
  id: string
  amount: number
  balance_after: number
  source: string
  description: string | null
  created_at: string
  expires_at?: string | null
}

export type LoyaltyPendingRedemption = {
  id: string
  reward_name: string
  points_spent: number
  fulfillment_code: string
  code_expires_at: string | null
  status: string
}

function loyaltyAuthHeaders(tenant: string) {
  if (typeof window === 'undefined') return {}
  const token = localStorage.getItem(`loyalty:${tenant}:token`)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/** Customer-facing rewards wallet API (no dashboard session cookies). */
export const loyaltyPortalCustomer = {
  branding: (tenant: string) =>
    publicApiClient.get<LoyaltyPortalBranding>(
      `/loyalty-portal/public/branding/${encodeURIComponent(tenant)}`,
    ),

  requestMagicLink: (tenant: string, email: string) =>
    publicApiClient.post('/loyalty-portal/auth/magic-link', { email, tenant_slug: tenant }),

  verifyMagicLink: (tenant: string, token: string) =>
    publicApiClient.post<{ access_token: string; customer_id: string }>(
      '/loyalty-portal/auth/magic-link/verify',
      { token, tenant_slug: tenant },
    ),

  login: (tenant: string, email: string, password: string) =>
    publicApiClient.post<{ access_token: string; must_change_password?: boolean }>(
      '/loyalty-portal/auth/login',
      { email, password, tenant_slug: tenant },
    ),

  setPassword: (tenant: string, newPassword: string) =>
    publicApiClient.post(
      '/loyalty-portal/auth/set-password',
      { new_password: newPassword },
      { headers: loyaltyAuthHeaders(tenant) },
    ),

  me: (tenant: string) =>
    publicApiClient.get<LoyaltyPortalProfile>('/loyalty-portal/me', {
      headers: loyaltyAuthHeaders(tenant),
    }),

  upsell: (tenant: string) =>
    publicApiClient.get<LoyaltyPortalUpsell>('/loyalty-portal/me/upsell', {
      headers: loyaltyAuthHeaders(tenant),
    }),

  rewards: (tenant: string) =>
    publicApiClient.get<{ items: LoyaltyRewardItem[] }>('/loyalty-portal/rewards', {
      headers: loyaltyAuthHeaders(tenant),
    }),

  redeem: (tenant: string, rewardId: string) =>
    publicApiClient.post<{
      reward_name?: string
      fulfillment_code?: string
      code_expires_at?: string
      status: string
      points_spent: number
    }>(`/loyalty-portal/rewards/${rewardId}/redeem`, {}, { headers: loyaltyAuthHeaders(tenant) }),

  pendingRedemptions: (tenant: string) =>
    publicApiClient.get<{ items: LoyaltyPendingRedemption[] }>(
      '/loyalty-portal/redemptions/pending',
      { headers: loyaltyAuthHeaders(tenant) },
    ),

  history: (tenant: string, limit = 50) =>
    publicApiClient.get<{ items: LoyaltyLedgerEntry[]; has_more: boolean }>(
      '/loyalty-portal/history',
      { headers: loyaltyAuthHeaders(tenant), params: { limit } },
    ),

  qr: (tenant: string) =>
    publicApiClient.get<{ qr_data_url: string; expires_at: string }>('/loyalty-portal/qr', {
      headers: loyaltyAuthHeaders(tenant),
    }),

  pushPublicKey: () =>
    publicApiClient.get<{ public_key: string; configured: boolean }>(
      '/notifications/push/public-key',
    ),

  pushSubscribe: (
    tenant: string,
    subscription: { endpoint: string; keys: { p256dh: string; auth: string } },
  ) =>
    publicApiClient.post(
      '/loyalty-portal/push/subscribe',
      subscription,
      { headers: loyaltyAuthHeaders(tenant) },
    ),

  pushUnsubscribe: (tenant: string) =>
    publicApiClient.post('/loyalty-portal/push/unsubscribe', {}, {
      headers: loyaltyAuthHeaders(tenant),
    }),

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
    publicApiClient.patch<LoyaltyPortalPreferences>(
      '/loyalty-portal/me/preferences',
      data,
      { headers: loyaltyAuthHeaders(tenant) },
    ),
}

export const accounting = {
  status: () => apiClient.get('/accounting/status'),
  checkout: (data: { success_url: string; cancel_url: string }) =>
    apiClient.post('/accounting/checkout', data),
  settings: () => apiClient.get('/accounting/settings'),
  updateSettings: (data: object) => apiClient.patch('/accounting/settings', data),
  sendInvoice: (id: string) => apiClient.post(`/accounting/invoices/${id}/send`),
  listExpenses: (page = 1) => apiClient.get('/accounting/expenses', { params: { page } }),
  createExpense: (data: object) => apiClient.post('/accounting/expenses', data),
  deleteExpense: (id: string) => apiClient.delete(`/accounting/expenses/${id}`),
  listRecurring: () => apiClient.get('/accounting/recurring'),
  createRecurring: (data: object) => apiClient.post('/accounting/recurring', data),
  deleteRecurring: (id: string) => apiClient.delete(`/accounting/recurring/${id}`),
  taxSummary: (year?: number) => apiClient.get('/accounting/tax-summary', { params: { year } }),
  exportAccountantPack: (year?: number) =>
    apiClient.get('/accounting/export/accountant-pack', { params: { year }, responseType: 'blob' }),
  customerFinancials: (customerId: string) =>
    apiClient.get(`/accounting/customers/${customerId}/financials`),
}

export const segments = {
  list: () => apiClient.get('/segments'),
  create: (data: { name: string; description?: string; rules: object }) =>
    apiClient.post('/segments', data),
  recompute: () => apiClient.post('/segments/recompute'),
}

export const autoReplies = {
  list: (status: string = 'pending') =>
    apiClient.get('/auto-replies', { params: { status } }),
  approve: (id: string, text?: string) =>
    apiClient.post(`/auto-replies/${id}/approve`, text ? { text } : {}),
  reject: (id: string) => apiClient.post(`/auto-replies/${id}/reject`),
}

export const usage = {
  me: (days?: number) => apiClient.get('/usage/me', { params: { days } }),
}

export type OutreachChannel = 'sms' | 'email' | 'whatsapp'
export type OutreachKind = 'broadcast' | 'sequence' | 'winback'
export type OutreachStepCondition = 'always' | 'no_reply' | 'replied' | 'opened'

export interface OutreachStep {
  channel: OutreachChannel
  subject?: string | null
  body: string
  delay_hours: number
  condition: OutreachStepCondition
  label?: string | null
}

export type LandingSection = {
  type: string
  props: Record<string, unknown>
}

export interface LandingPageRow {
  id: string
  tenant_id: string
  slug: string
  title: string
  meta_description: string | null
  cover_image_url: string | null
  theme: Record<string, unknown>
  sections: LandingSection[]
  is_published: boolean
  published_at: string | null
  ai_provider: string | null
  ai_model: string | null
  created_at: string
  updated_at: string
}

export const landingPages = {
  list: () => apiClient.get('/landing-pages'),
  get: (id: string) => apiClient.get(`/landing-pages/${id}`),
  create: (data: Partial<LandingPageRow>) => apiClient.post('/landing-pages', data),
  update: (id: string, data: Partial<LandingPageRow>) =>
    apiClient.patch(`/landing-pages/${id}`, data),
  remove: (id: string) => apiClient.delete(`/landing-pages/${id}`),
  generate: (data: {
    business_summary: string
    primary_offer: string
    target_audience?: string
    tone?: string
    cta_text?: string
    include_sections?: string[]
    slug?: string
    save?: boolean
  }) => apiClient.post('/landing-pages/generate', data),
}

export const outreach = {
  list: (status?: string) => apiClient.get('/outreach/campaigns', { params: { status } }),
  get: (id: string) => apiClient.get(`/outreach/campaigns/${id}`),
  stats: (id: string) => apiClient.get(`/outreach/campaigns/${id}/stats`),
  create: (data: {
    name: string
    description?: string
    kind?: OutreachKind
    channels?: OutreachChannel[]
    audience: { segment_id?: string; filter?: Record<string, unknown> }
    steps: OutreachStep[]
    scheduled_at?: string | null
  }) => apiClient.post('/outreach/campaigns', data),
  update: (id: string, data: Record<string, unknown>) =>
    apiClient.patch(`/outreach/campaigns/${id}`, data),
  remove: (id: string) => apiClient.delete(`/outreach/campaigns/${id}`),
  launch: (id: string) => apiClient.post(`/outreach/campaigns/${id}/launch`),
  pause: (id: string) => apiClient.post(`/outreach/campaigns/${id}/pause`),
  resume: (id: string) => apiClient.post(`/outreach/campaigns/${id}/resume`),
  draftStep: (data: {
    channel: OutreachChannel
    goal: string
    audience_hint?: string
    tone?: string
  }) => apiClient.post('/outreach/ai-draft-step', data),
  winback: (data: {
    inactive_days: number
    channel: OutreachChannel
    offer: string
    name?: string
  }) => apiClient.post('/outreach/winback', data),
}

export const admin = {
  me: () => apiClient.get('/admin/me'),
  stats: () => apiClient.get('/admin/stats'),
  listTenants: (params?: { q?: string; limit?: number; offset?: number }) =>
    apiClient.get('/admin/tenants', { params }),
  getTenant: (id: string) => apiClient.get(`/admin/tenants/${id}`),
  suspendTenant: (id: string) => apiClient.post(`/admin/tenants/${id}/suspend`),
  reactivateTenant: (id: string) => apiClient.post(`/admin/tenants/${id}/reactivate`),
  deleteTenant: (id: string, permanent = true) =>
    apiClient.delete(`/admin/tenants/${id}`, { params: { permanent } }),
  deleteFreelancer: (id: string, permanent = true) =>
    apiClient.delete(`/admin/freelancers/${id}`, { params: { permanent } }),
  listUsers: (params?: { q?: string; limit?: number; offset?: number }) =>
    apiClient.get('/admin/users', { params }),
  deleteUser: (id: string, permanent = true) =>
    apiClient.delete(`/admin/users/${id}`, { params: { permanent } }),
  listTenantHealth: () => apiClient.get('/admin/tenant-health'),
  remindTenant: (tenantId: string, params?: { note?: string }) =>
    apiClient.post(`/admin/tenant-health/${tenantId}/remind`, null, { params }),
  // Marketing CMS -----------------------------------------------------------
  listMarketingSections: () => apiClient.get('/admin/marketing/sections'),
  getMarketingSection: (key: string) => apiClient.get(`/admin/marketing/sections/${key}`),
  upsertMarketingSection: (body: {
    key: string
    title?: string | null
    description?: string | null
    data: Record<string, unknown>
    is_published?: boolean
    sort_order?: number
  }) => apiClient.post('/admin/marketing/sections', body),
  patchMarketingSection: (
    key: string,
    body: {
      title?: string | null
      description?: string | null
      data?: Record<string, unknown>
      is_published?: boolean
      sort_order?: number
    },
  ) => apiClient.patch(`/admin/marketing/sections/${key}`, body),
  reorderMarketingSections: (body: { keys: string[] }) =>
    apiClient.post('/admin/marketing/sections/reorder', body),
  deleteMarketingSection: (key: string) =>
    apiClient.delete(`/admin/marketing/sections/${key}`),
  listAdaptivePages: () => apiClient.get('/admin/marketing/adaptive-pages'),
  getAdaptivePage: (nicheId: string) =>
    apiClient.get(`/admin/marketing/adaptive-pages/${nicheId}`),
  upsertAdaptivePage: (body: {
    niche_id: string
    label: string
    data: Record<string, unknown>
    is_published?: boolean
  }) => apiClient.post('/admin/marketing/adaptive-pages', body),
  patchAdaptivePage: (
    nicheId: string,
    body: {
      label?: string | null
      data?: Record<string, unknown>
      is_published?: boolean
    },
  ) => apiClient.patch(`/admin/marketing/adaptive-pages/${nicheId}`, body),
  deleteAdaptivePage: (nicheId: string) =>
    apiClient.delete(`/admin/marketing/adaptive-pages/${nicheId}`),
  // Review moderation -------------------------------------------------------
  listMarketingReviews: (status_filter?: string) =>
    apiClient.get('/admin/marketing/reviews', { params: { status_filter } }),
  moderateReview: (
    id: string,
    body: {
      status?: 'approved' | 'pending' | 'hidden' | 'rejected' | null
      is_featured?: boolean | null
      is_carousel?: boolean | null
      quote?: string | null
      author_role?: string | null
      author_location?: string | null
      metric?: string | null
    },
  ) => apiClient.patch(`/admin/marketing/reviews/${id}`, body),
  pushReview: (id: string, body: { channel: 'gmb' | 'trustpilot'; target_url?: string | null }) =>
    apiClient.post(`/admin/marketing/reviews/${id}/push`, body),
  // Tool / module visibility config -----------------------------------------
  getToolConfigMeta: () =>
    apiClient.get<{ categories: string[]; tools: ToolMeta[] }>('/admin/tool-configs/meta'),
  listToolConfigs: () => apiClient.get<CategoryToolConfig[]>('/admin/tool-configs'),
  updateToolConfig: (category: string, enabled_tools: string[]) =>
    apiClient.put<CategoryToolConfig>(`/admin/tool-configs/${category}`, { enabled_tools }),
  resetToolConfig: (category: string) =>
    apiClient.post<CategoryToolConfig>(`/admin/tool-configs/${category}/reset`),
  // Booking form templates (category defaults) -----------------------------
  listBookingFormCategories: () =>
    apiClient.get<{ categories: string[] }>('/admin/booking-forms/categories'),
  listBookingFormTemplates: () => apiClient.get('/admin/booking-forms/templates'),
  getBookingFormTemplate: (category: string) =>
    apiClient.get(`/admin/booking-forms/templates/${category}`),
  updateBookingFormTemplate: (category: string, data: { name?: string; schema: object }) =>
    apiClient.put(`/admin/booking-forms/templates/${category}`, data),
  // Lead requests -----------------------------------------------------------
  listLeadRequests: (status?: string) =>
    apiClient.get<LeadRequestItem[]>('/admin/lead-requests', { params: status ? { status } : {} }),
  approveLeadRequest: (id: string, body: { approved_count?: number; admin_notes?: string }) =>
    apiClient.post<LeadRequestItem>(`/admin/lead-requests/${id}/approve`, body),
  rejectLeadRequest: (id: string, body: { admin_notes?: string }) =>
    apiClient.post<LeadRequestItem>(`/admin/lead-requests/${id}/reject`, body),
  fulfillLeadRequest: (id: string, body: { admin_notes?: string }) =>
    apiClient.post<LeadRequestItem>(`/admin/lead-requests/${id}/fulfill`, body),
  // Landing-page templates --------------------------------------------------
  listLandingTemplates: (niche?: string) =>
    apiClient.get('/admin/marketing/landing-templates', { params: { niche } }),
  getLandingTemplate: (slug: string) =>
    apiClient.get(`/admin/marketing/landing-templates/${slug}`),
}

// ── AI Scraper (super-admin /api/v1/superadmin/ai-scraper) ---------------

export type ScraperType = 'html' | 'api' | 'directory' | 'social' | 'custom'
export type AggressionLevel = 'low' | 'medium' | 'high' | 'extreme'
export type TaskStatus = 'pending' | 'running' | 'paused' | 'completed' | 'error'

export interface AiScraperCategory {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export type SourcePlatform =
  | 'directory'
  | 'search_engine'
  | 'social'
  | 'review_site'
  | 'marketplace'
  | 'other'

export interface AiScraperSource {
  id: string
  name: string
  url_pattern: string
  scraping_type: ScraperType
  source_platform?: SourcePlatform
  category_id: string
  active: boolean
  postcode_prefix?: string | null
  region_label?: string | null
  is_catalog_default?: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

export interface AiScraperTask {
  id: string
  source_id: string
  category_id: string
  aggression_level: AggressionLevel
  frequency: string
  last_run: string | null
  next_run: string | null
  status: TaskStatus
  created_at: string
  updated_at: string
}

export interface AiScraperTaskRow extends Omit<AiScraperTask, 'created_at' | 'updated_at'> {
  total_leads_extracted: number
}

export interface AiScraperResult {
  id: string
  task_id: string
  raw_payload: string | null
  cleaned_payload: Record<string, unknown>
  ai_extracted_data: Record<string, unknown>
  ai_score: number
  new_leads_created: number
  created_at: string
  updated_at: string
}

export interface AiScraperSettings {
  thread_count: number
  global_aggression_mode: AggressionLevel
  updated_at: string
}

export const aiScraper = {
  listCategories: () => aiScraperClient.get<AiScraperCategory[]>('/categories'),
  createCategory: (body: { name: string; description?: string | null }) =>
    aiScraperClient.post<AiScraperCategory>('/categories', body),
  updateCategory: (id: string, body: { name?: string; description?: string | null }) =>
    aiScraperClient.patch<AiScraperCategory>(`/categories/${id}`, body),
  deleteCategory: (id: string) => aiScraperClient.delete(`/categories/${id}`),

  listSources: (params?: { active?: boolean; category_id?: string }) =>
    aiScraperClient.get<AiScraperSource[]>('/sources', { params }),
  createSource: (body: {
    name: string
    url_pattern: string
    scraping_type: ScraperType
    source_platform?: SourcePlatform
    category_id: string
    active?: boolean
    postcode_prefix?: string | null
    region_label?: string | null
    is_catalog_default?: boolean
    notes?: string | null
  }) => aiScraperClient.post<AiScraperSource>('/sources', body),
  updateSource: (
    id: string,
    body: Partial<Omit<AiScraperSource, 'id' | 'created_at' | 'updated_at'>>,
  ) => aiScraperClient.patch<AiScraperSource>(`/sources/${id}`, body),
  deleteSource: (id: string) => aiScraperClient.delete(`/sources/${id}`),

  listTasks: (params?: { source_id?: string; status?: TaskStatus }) =>
    aiScraperClient.get<AiScraperTaskRow[]>('/tasks', { params }),
  createTask: (body: {
    source_id: string
    category_id: string
    aggression_level: AggressionLevel
    frequency: string
    status?: TaskStatus
  }) => aiScraperClient.post<AiScraperTask>('/tasks', body),
  getTask: (id: string) => aiScraperClient.get<AiScraperTask>(`/tasks/${id}`),
  updateTask: (
    id: string,
    body: Partial<
      Omit<AiScraperTask, 'id' | 'created_at' | 'updated_at' | 'last_run' | 'next_run'>
    >,
  ) => aiScraperClient.patch<AiScraperTask>(`/tasks/${id}`, body),
  deleteTask: (id: string) => aiScraperClient.delete(`/tasks/${id}`),
  runTask: (id: string) =>
    aiScraperClient.post<{ task_id: string; enqueued: boolean; message: string }>(
      `/tasks/${id}/run`,
    ),

  listResults: (params?: { task_id?: string; limit?: number }) =>
    aiScraperClient.get<AiScraperResult[]>('/results', { params }),
  getResult: (id: string) => aiScraperClient.get<AiScraperResult>(`/results/${id}`),

  getSettings: () => aiScraperClient.get<AiScraperSettings>('/settings'),
  updateSettings: (body: {
    thread_count: number
    global_aggression_mode: AggressionLevel
  }) => aiScraperClient.put<AiScraperSettings>('/settings', body),
  seedCatalog: (force = false) =>
    aiScraperClient.post<{ ok: boolean; stats: Record<string, number> }>('/seed-catalog', null, {
      params: { force },
    }),
}

// ── Tenant-scoped marketing / templates -----------------------------------

export const marketingTemplates = {
  list: (niche?: string) =>
    apiClient.get('/marketing/landing-templates', { params: { niche } }),
  get: (slug: string) => apiClient.get(`/marketing/landing-templates/${slug}`),
  apply: (body: { template_slug: string; page_title: string; page_slug?: string }) =>
    apiClient.post('/marketing/landing-templates/apply', body),
}

// ── WhatsApp CRM ---------------------------------------------------------

export const whatsapp = {
  listConversations: (params?: {
    page?: number
    page_size?: number
    status_filter?: 'open' | 'resolved' | 'all'
  }) => apiClient.get('/whatsapp/conversations', { params }),
  getConversation: (id: string) => apiClient.get(`/whatsapp/conversations/${id}`),
  resolve: (id: string, resolved: boolean) =>
    apiClient.post(`/whatsapp/conversations/${id}/resolve`, null, { params: { resolved } }),
  send: (body: { to: string; body: string; customer_id?: string; deal_id?: string }) =>
    apiClient.post('/whatsapp/send', body),
  suggestReply: (conversation_id: string) =>
    apiClient.post('/whatsapp/ai/suggest-reply', { conversation_id }),
  sentiment: (conversation_id: string) =>
    apiClient.post('/whatsapp/ai/sentiment', { conversation_id }),
  summarise: (conversation_id: string) =>
    apiClient.post('/whatsapp/ai/summarise', { conversation_id }),
}

// ── Lead Marketplace (/api/superadmin/lead-marketplace) ───────────────────────

const lmClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api/superadmin/lead-marketplace`,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})
lmClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }
    if (error.response?.status === 401 && !originalRequest?._retry) {
      originalRequest._retry = true
      try {
        await _refresh()
        return lmClient(originalRequest!)
      } catch {
        if (typeof window !== 'undefined') {
          window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname)
        }
      }
    }
    return Promise.reject(normalizeApiError(error))
  },
)

export type LMExclusivity = 'shared' | 'semi-exclusive' | 'exclusive'
export type LMStatus = 'available' | 'reserved' | 'sold' | 'expired'

export interface LMCategory { id: string; name: string; description: string | null; created_at: string; updated_at: string }
export interface LMQualityRule { id: string; name: string; min_ai_score: number; max_age_days: number; requires_phone: boolean; requires_email: boolean; apply_to_category: string | null; created_at: string; updated_at: string }
export interface LMPricing { id: string; category_id: string; base_price: number; high_quality_multiplier: number; exclusive_multiplier: number; created_at: string; updated_at: string }
export interface LMTerritory { id: string; name: string; region_code: string; country: string; created_at: string; updated_at: string }
export interface LMInventoryItem { id: string; lead_id: string; category_id: string; territory_id: string; ai_score: number; price: number; exclusivity: LMExclusivity; status: LMStatus; assigned_tenant_id: string | null; category_name?: string | null; territory_name?: string | null; created_at: string; updated_at: string }
export interface LMAssignmentRule { id: string; rule_name: string; category_id: string | null; territory_id: string | null; min_subscription_level: number; priority_weight: number; created_at: string; updated_at: string }
export interface LMDistributionResult { marketplace_id: string; assigned_tenant_id: string; priority_score: number; status: string }

export const leadMarketplace = {
  // Categories
  listCategories: () => lmClient.get<LMCategory[]>('/categories'),
  createCategory: (body: { name: string; description?: string | null }) => lmClient.post<LMCategory>('/categories', body),
  updateCategory: (id: string, body: { name?: string; description?: string | null }) => lmClient.patch<LMCategory>(`/categories/${id}`, body),
  deleteCategory: (id: string) => lmClient.delete(`/categories/${id}`),

  // Quality Rules
  listQualityRules: () => lmClient.get<LMQualityRule[]>('/quality-rules'),
  createQualityRule: (body: object) => lmClient.post<LMQualityRule>('/quality-rules', body),
  updateQualityRule: (id: string, body: object) => lmClient.patch<LMQualityRule>(`/quality-rules/${id}`, body),
  deleteQualityRule: (id: string) => lmClient.delete(`/quality-rules/${id}`),

  // Pricing
  listPricing: () => lmClient.get<LMPricing[]>('/pricing'),
  createPricing: (body: object) => lmClient.post<LMPricing>('/pricing', body),
  updatePricing: (id: string, body: object) => lmClient.patch<LMPricing>(`/pricing/${id}`, body),
  deletePricing: (id: string) => lmClient.delete(`/pricing/${id}`),

  // Territories
  listTerritories: () => lmClient.get<LMTerritory[]>('/territories'),
  createTerritory: (body: { name: string; region_code: string; country?: string }) => lmClient.post<LMTerritory>('/territories', body),
  updateTerritory: (id: string, body: object) => lmClient.patch<LMTerritory>(`/territories/${id}`, body),
  deleteTerritory: (id: string) => lmClient.delete(`/territories/${id}`),

  // Assignment Rules
  listAssignmentRules: () => lmClient.get<LMAssignmentRule[]>('/assignment-rules'),
  createAssignmentRule: (body: object) => lmClient.post<LMAssignmentRule>('/assignment-rules', body),
  updateAssignmentRule: (id: string, body: object) => lmClient.patch<LMAssignmentRule>(`/assignment-rules/${id}`, body),
  deleteAssignmentRule: (id: string) => lmClient.delete(`/assignment-rules/${id}`),

  // Inventory
  listInventory: (params?: { status?: LMStatus; category_id?: string; territory_id?: string; limit?: number; offset?: number }) =>
    lmClient.get<LMInventoryItem[]>('/inventory', { params }),
  createInventoryItem: (body: object) => lmClient.post<LMInventoryItem>('/inventory', body),
  getInventoryItem: (id: string) => lmClient.get<LMInventoryItem>(`/inventory/${id}`),
  updateInventoryItem: (id: string, body: object) => lmClient.patch<LMInventoryItem>(`/inventory/${id}`, body),
  deleteInventoryItem: (id: string) => lmClient.delete(`/inventory/${id}`),
  assignItem: (id: string, body: { tenant_id: string; status?: LMStatus }) => lmClient.post<LMInventoryItem>(`/inventory/${id}/assign`, body),
  releaseItem: (id: string) => lmClient.post<LMInventoryItem>(`/inventory/${id}/release`),
  markSold: (id: string) => lmClient.post<LMInventoryItem>(`/inventory/${id}/mark-sold`),
  distributeItem: (id: string) => lmClient.post<LMDistributionResult>(`/inventory/${id}/distribute`),
}

// ── Super Admin API (/api/admin/) ──────────────────────────────────────────
export const adminApiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api/admin`,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})
adminApiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }
    if (error.response?.status === 401 && !originalRequest?._retry) {
      originalRequest._retry = true
      try {
        await _refresh()
        return adminApiClient(originalRequest!)
      } catch {
        if (typeof window !== 'undefined') {
          window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname)
        }
      }
    }
    return Promise.reject(normalizeApiError(error))
  },
)

export interface AdminRole { id: string; name: string; permissions: string[]; description: string }
export interface AdminActivityLog { id: string; user_id: string; action: string; resource_type: string | null; resource_id: string | null; ip_address: string | null; created_at: string }
export interface CommTemplate { id: string; name: string; channel: string; subject: string | null; body: string; is_active: boolean; created_at: string }
export interface BroadcastItem { id: string; name: string; channel: string; status: string; recipient_count: number; created_at: string }
export interface SystemLog { id: string; level: string; service: string | null; message: string; metadata: Record<string, unknown>; created_at: string }
export interface BlockedIP { ip_address: string; reason: string; created_at: string }
export interface SystemSetting { key: string; value: unknown; description: string; is_secret: boolean; updated_at: string }
export interface SupportTicket { id: string; subject: string; status: string; priority: string; tenant_id: string | null; created_at: string }
export interface TicketReply { id: string; body: string; is_internal: boolean; created_at: string }
export interface AdminBillingPlan { id: string; name: string; price_gbp_monthly: number; max_users: number; max_locations: number; max_leads_per_month: number; has_ai_content: boolean; has_social_posting: boolean; ai_lead_requests_per_month: number; is_active: boolean }
export interface AdminScraper { id: string; name: string; url?: string; scraping_type?: string; is_active: boolean; created_at: string }
export interface AIEngineConfig { phone_points: number; email_points: number; service_need_points: number; location_points: number; urgency_points: number; name_points: number; intent_high_points: number; cap: number }

export const adminApi = {
  // Dashboard
  getStats: () => adminApiClient.get('/dashboard/stats'),
  getHealth: () => adminApiClient.get('/dashboard/health'),

  // Tenants
  listTenants: (p?: { search?: string; active?: boolean; limit?: number; offset?: number }) => adminApiClient.get('/tenants/', { params: p }),
  getTenant: (id: string) => adminApiClient.get(`/tenants/${id}`),
  createTenant: (body: object) => adminApiClient.post('/tenants/', body),
  updateTenant: (id: string, body: object) => adminApiClient.put(`/tenants/${id}`, body),
  deleteTenant: (id: string) => adminApiClient.delete(`/tenants/${id}`),
  impersonateTenant: (id: string) => adminApiClient.post(`/tenants/${id}/impersonate`),
  toggleTenantActive: (id: string) => adminApiClient.post(`/tenants/${id}/toggle-active`),

  // Marketplace
  listMarketplace: (p?: object) => adminApiClient.get('/marketplace/', { params: p }),
  getMarketplaceItem: (id: string) => adminApiClient.get(`/marketplace/${id}`),
  createMarketplaceItem: (body: object) => adminApiClient.post('/marketplace/', body),
  updateMarketplaceItem: (id: string, body: object) => adminApiClient.put(`/marketplace/${id}`, body),
  deleteMarketplaceItem: (id: string) => adminApiClient.delete(`/marketplace/${id}`),
  assignMarketplaceItem: (id: string, tenant_id: string) => adminApiClient.post(`/marketplace/${id}/assign`, { tenant_id }),
  releaseMarketplaceItem: (id: string) => adminApiClient.post(`/marketplace/${id}/release`),
  distributeMarketplaceItem: (id: string) => adminApiClient.post(`/marketplace/${id}/distribute`),

  // Scraper Sources
  listScraperSources: (p?: object) => adminApiClient.get('/scraper_sources/', { params: p }),
  getScraperSource: (id: string) => adminApiClient.get(`/scraper_sources/${id}`),
  createScraperSource: (body: object) => adminApiClient.post('/scraper_sources/', body),
  updateScraperSource: (id: string, body: object) => adminApiClient.put(`/scraper_sources/${id}`, body),
  deleteScraperSource: (id: string) => adminApiClient.delete(`/scraper_sources/${id}`),

  // Scraper Tasks
  listScraperTasks: (p?: object) => adminApiClient.get('/scraper_tasks/', { params: p }),
  getScraperTask: (id: string) => adminApiClient.get(`/scraper_tasks/${id}`),
  createScraperTask: (body: object) => adminApiClient.post('/scraper_tasks/', body),
  updateScraperTask: (id: string, body: object) => adminApiClient.put(`/scraper_tasks/${id}`, body),
  deleteScraperTask: (id: string) => adminApiClient.delete(`/scraper_tasks/${id}`),
  runScraperTask: (id: string) => adminApiClient.post(`/scraper_tasks/${id}/run`),

  // Scraper Results
  listScraperResults: (p?: object) => adminApiClient.get('/scraper_results/', { params: p }),
  getScraperResult: (id: string) => adminApiClient.get(`/scraper_results/${id}`),
  deleteScraperResult: (id: string) => adminApiClient.delete(`/scraper_results/${id}`),

  // AI Engine
  getExtractionPrompt: () => adminApiClient.get('/ai_engine/prompt'),
  getScoringConfig: () => adminApiClient.get<AIEngineConfig>('/ai_engine/scoring'),
  updateScoringConfig: (body: AIEngineConfig) => adminApiClient.put('/ai_engine/scoring', body),
  getDedupeConfig: () => adminApiClient.get('/ai_engine/dedupe'),
  updateDedupeConfig: (body: object) => adminApiClient.put('/ai_engine/dedupe', body),
  getFraudConfig: () => adminApiClient.get('/ai_engine/fraud'),
  updateFraudConfig: (body: object) => adminApiClient.put('/ai_engine/fraud', body),
  testScore: (body: object) => adminApiClient.post('/ai_engine/test-score', body),

  // Billing
  listBillingPlans: () => adminApiClient.get<AdminBillingPlan[]>('/billing/plans'),
  getBillingPlan: (id: string) => adminApiClient.get<AdminBillingPlan>(`/billing/plans/${id}`),
  createBillingPlan: (body: object) => adminApiClient.post('/billing/plans', body),
  updateBillingPlan: (id: string, body: object) => adminApiClient.put(`/billing/plans/${id}`, body),
  deleteBillingPlan: (id: string) => adminApiClient.delete(`/billing/plans/${id}`),
  listSubscriptions: (p?: object) => adminApiClient.get('/billing/subscriptions', { params: p }),
  listTransactions: (p?: object) => adminApiClient.get('/billing/transactions', { params: p }),

  // Users
  listAdminUsers: (p?: object) => adminApiClient.get('/users/', { params: p }),
  getAdminUser: (id: string) => adminApiClient.get(`/users/${id}`),
  createAdminUser: (body: object) => adminApiClient.post('/users/', body),
  updateAdminUser: (id: string, body: object) => adminApiClient.put(`/users/${id}`, body),
  deleteAdminUser: (id: string) => adminApiClient.delete(`/users/${id}`),
  listRoles: () => adminApiClient.get<AdminRole[]>('/users/roles'),
  createRole: (body: object) => adminApiClient.post('/users/roles', body),
  updateRole: (id: string, body: object) => adminApiClient.put(`/users/roles/${id}`, body),
  deleteRole: (id: string) => adminApiClient.delete(`/users/roles/${id}`),
  listActivityLogs: (p?: object) => adminApiClient.get<AdminActivityLog[]>('/users/activity', { params: p }),

  // Communications
  listCommTemplates: (p?: object) => adminApiClient.get<CommTemplate[]>('/communications/templates', { params: p }),
  getCommTemplate: (id: string) => adminApiClient.get<CommTemplate>(`/communications/templates/${id}`),
  createCommTemplate: (body: object) => adminApiClient.post<CommTemplate>('/communications/templates', body),
  updateCommTemplate: (id: string, body: object) => adminApiClient.put<CommTemplate>(`/communications/templates/${id}`, body),
  deleteCommTemplate: (id: string) => adminApiClient.delete(`/communications/templates/${id}`),
  listBroadcasts: (p?: object) => adminApiClient.get<BroadcastItem[]>('/communications/broadcasts', { params: p }),
  createBroadcast: (body: object) => adminApiClient.post<BroadcastItem>('/communications/broadcasts', body),
  sendBroadcast: (id: string) => adminApiClient.post<{ status: string; recipient_count: number }>(`/communications/broadcasts/${id}/send`),
  previewBroadcastRecipients: (audience: string) =>
    adminApiClient.get<{ audience: string; count: number }>('/communications/broadcasts/preview-recipients', {
      params: { audience },
    }),

  // Operations
  listSystemLogs: (p?: object) => adminApiClient.get<SystemLog[]>('/operations/logs', { params: p }),
  getMonitoring: () => adminApiClient.get('/operations/monitoring'),
  getSecurity: () => adminApiClient.get('/operations/security'),
  blockIP: (body: { ip_address: string; reason?: string }) => adminApiClient.post('/operations/security/block-ip', body),
  unblockIP: (ip: string) => adminApiClient.delete(`/operations/security/block-ip/${ip}`),

  // Settings
  listSettings: () => adminApiClient.get<SystemSetting[]>('/settings/'),
  getSetting: (key: string) => adminApiClient.get<SystemSetting>(`/settings/${key}`),
  updateSetting: (key: string, value: unknown) => adminApiClient.put(`/settings/${key}`, { value }),
  bulkUpsertSettings: (items: Array<{ key: string; value: unknown; description?: string }>) => adminApiClient.put('/settings/', items),
  deleteSetting: (key: string) => adminApiClient.delete(`/settings/${key}`),

  // Support
  listTickets: (p?: object) => adminApiClient.get<SupportTicket[]>('/support/tickets', { params: p }),
  getTicket: (id: string) => adminApiClient.get<SupportTicket & { replies: TicketReply[] }>(`/support/tickets/${id}`),
  createTicket: (body: object) => adminApiClient.post<SupportTicket>('/support/tickets', body),
  updateTicket: (id: string, body: object) => adminApiClient.put<SupportTicket>(`/support/tickets/${id}`, body),
  deleteTicket: (id: string) => adminApiClient.delete(`/support/tickets/${id}`),
  resolveTicket: (id: string) => adminApiClient.post<SupportTicket>(`/support/tickets/${id}/resolve`),
  replyTicket: (id: string, body: { body: string; is_internal?: boolean }) => adminApiClient.post(`/support/tickets/${id}/reply`, body),

  // Email Templates
  listEmailTemplates: () => adminApiClient.get('/email-templates'),
  getEmailTemplate: (name: string) => adminApiClient.get(`/email-templates/${name}`),
  updateEmailTemplate: (name: string, html: string) => adminApiClient.put(`/email-templates/${name}`, { html }),
  previewEmailTemplate: (name: string) => adminApiClient.post(`/email-templates/${name}/preview`, {}),

  // AI Social — admin
  socialGetAiConfig: () => adminApiClient.get('/social/ai-config'),
  socialSetAiConfig: (body: object) => adminApiClient.post('/social/ai-config', body),
  socialTenantOverview: () => adminApiClient.get('/social/tenant-overview'),
  socialInsights: () => adminApiClient.get('/social/insights'),
  socialScheduler: () => adminApiClient.get('/social/scheduler'),
  socialFailures: () => adminApiClient.get('/social/failures'),
  socialModels: () => adminApiClient.get('/social/models'),
  socialTenantsList: () => adminApiClient.get('/social/tenants-list'),
  socialForceGenerate: (body: { tenant_id: string; count: number; topic_hints?: string[] }) =>
    adminApiClient.post('/social/force-generate', body),

  // Marketer — admin
  marketerOverview: () => adminApiClient.get('/marketer/overview'),
  marketerPricing: () => adminApiClient.get('/marketer/pricing'),
  marketerSetPricing: (body: object) => adminApiClient.post('/marketer/set-pricing', body),
  marketerListQuotas: () => adminApiClient.get('/marketer/quotas'),
  marketerSetQuota: (body: { tenant_id: string; max_reports_per_month: number }) =>
    adminApiClient.post('/marketer/set-quotas', body),
  marketerUsage: () => adminApiClient.get('/marketer/usage'),
  marketerCompetitorQueue: () => adminApiClient.get('/marketer/competitor-queue'),
  marketerTenantsList: () => adminApiClient.get('/marketer/tenants-list'),

  // Freelancer Management → Billing Inspector
  freelancerBillings: () =>
    adminApiClient.get('/freelancer-management/billings'),
  deleteFreelancer: (userId: string) =>
    adminApiClient.delete(`/freelancer-management/freelancers/${userId}`),
  setFreelancerBillingOverride: (billingId: string, override_price: number | null) =>
    adminApiClient.patch(`/freelancer-management/billings/${billingId}`, {
      override_price,
    }),
  freelancerModuleVisibilityMeta: () =>
    adminApiClient.get('/freelancer-management/module-visibility/meta'),
  getFreelancerModuleVisibility: () =>
    adminApiClient.get('/freelancer-management/module-visibility'),
  updateFreelancerModuleVisibility: (enabled_tools: string[]) =>
    adminApiClient.put('/freelancer-management/module-visibility', { enabled_tools }),
  resetFreelancerModuleVisibility: () =>
    adminApiClient.delete('/freelancer-management/module-visibility'),
}

// ── Super Admin → Billing Inspector (/api/super-admin/billing/) ────────────
export const billingInspectorApiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api/super-admin/billing`,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

billingInspectorApiClient.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }
    if (error.response?.status === 401 && !originalRequest?._retry) {
      originalRequest._retry = true
      try {
        await _refresh()
        return billingInspectorApiClient(originalRequest!)
      } catch {
        if (typeof window !== 'undefined') {
          window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname)
        }
      }
    }
    return Promise.reject(normalizeApiError(error))
  },
)

export const billingInspectorApi = {
  overview: () => billingInspectorApiClient.get('/overview'),
  listTenants: (params?: {
    page?: number
    page_size?: number
    plan?: string
    overage_state?: 'any' | 'none'
    invoice_status?: string
  }) => billingInspectorApiClient.get('/tenants', { params }),
  listFreelancers: (params?: {
    page?: number
    page_size?: number
    plan?: '1-50' | '51-100' | '>100'
    overage_state?: 'any' | 'none'
    invoice_status?: string
  }) => billingInspectorApiClient.get('/freelancers', { params }),
  tenantProfile: (id: string) => billingInspectorApiClient.get(`/tenant/${id}`),
  freelancerProfile: (id: string) => billingInspectorApiClient.get(`/freelancer/${id}`),
  auditLogs: (params?: {
    page?: number
    page_size?: number
    type?: 'plan_change' | 'overage_flag' | 'invoice_event' | 'payment_failure'
  }) => billingInspectorApiClient.get('/audit-logs', { params }),
  invoice: (invoiceId: string) => billingInspectorApiClient.get(`/invoice/${invoiceId}`),
}
