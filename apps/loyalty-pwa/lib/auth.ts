'use client'

const TOKEN_PREFIX = 'loyalty:'

export function getToken(tenant: string): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(`${TOKEN_PREFIX}${tenant}:token`)
}

export function setToken(tenant: string, token: string): void {
  localStorage.setItem(`${TOKEN_PREFIX}${tenant}:token`, token)
}

export function clearToken(tenant: string): void {
  localStorage.removeItem(`${TOKEN_PREFIX}${tenant}:token`)
}

export function isAuthenticated(tenant: string): boolean {
  return Boolean(getToken(tenant))
}
