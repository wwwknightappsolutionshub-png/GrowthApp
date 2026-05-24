'use client'

const TOKEN_PREFIX = 'loyalty:'

export function getLoyaltyToken(tenant: string): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(`${TOKEN_PREFIX}${tenant}:token`)
}

export function setLoyaltyToken(tenant: string, token: string): void {
  localStorage.setItem(`${TOKEN_PREFIX}${tenant}:token`, token)
}

export function clearLoyaltyToken(tenant: string): void {
  localStorage.removeItem(`${TOKEN_PREFIX}${tenant}:token`)
}

export function isLoyaltyAuthenticated(tenant: string): boolean {
  return Boolean(getLoyaltyToken(tenant))
}

export function rewardsPath(tenant: string, subpath = ''): string {
  const suffix = subpath ? `/${subpath.replace(/^\//, '')}` : ''
  return `/rewards/${encodeURIComponent(tenant)}${suffix}`
}
