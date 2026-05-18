'use client'

import { useEffect, useState } from 'react'

const STORAGE_KEY = 'cf:freelancer:activeClientId'

export function useActiveClient() {
  const [activeId, setActiveIdState] = useState<string | null>(null)

  useEffect(() => {
    if (typeof window === 'undefined') return
    const stored = window.localStorage.getItem(STORAGE_KEY)
    if (stored) setActiveIdState(stored)
  }, [])

  const setActiveId = (id: string | null) => {
    setActiveIdState(id)
    if (typeof window === 'undefined') return
    if (id) {
      window.localStorage.setItem(STORAGE_KEY, id)
    } else {
      window.localStorage.removeItem(STORAGE_KEY)
    }
    window.dispatchEvent(new CustomEvent('cf:freelancer:active-client-changed', { detail: { id } }))
  }

  return { activeId, setActiveId }
}

export function getActiveClientId(): string | null {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(STORAGE_KEY)
}
