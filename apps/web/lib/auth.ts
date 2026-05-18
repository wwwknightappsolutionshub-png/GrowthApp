/**
 * Auth state on the client.
 *
 * We no longer touch localStorage — access + refresh tokens live in httpOnly
 * cookies set by the API. The dashboard layout calls `auth.me()` once to
 * confirm the session before rendering protected pages, and the server-side
 * middleware in `middleware.ts` does the cookie-presence check on every
 * request.
 *
 * For convenience, this module also exposes a tiny helper to call `/auth/me`
 * so client components can show the current user without round-tripping
 * through useEffect each time.
 */

import { auth } from '@/lib/api-client'

export interface MeResponse {
  id: string
  email: string
  full_name: string
  phone?: string | null
  avatar_url?: string | null
  is_superadmin?: boolean
  totp_enabled?: boolean
  user_type?: 'tenant' | 'freelancer'
  estimated_client_count?: number | null
  onboarding_completed?: boolean
  phone_verified_at?: string | null
}

export async function fetchMe(): Promise<MeResponse | null> {
  try {
    const res = await auth.me()
    return res.data as MeResponse
  } catch {
    return null
  }
}

export async function logout(): Promise<void> {
  try {
    await auth.logout()
  } catch {
    // best-effort
  } finally {
    if (typeof window !== 'undefined') {
      window.location.href = '/login'
    }
  }
}
