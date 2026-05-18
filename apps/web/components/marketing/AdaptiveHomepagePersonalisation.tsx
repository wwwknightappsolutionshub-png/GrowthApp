'use client'

import { useEffect, useState } from 'react'
import {
  ADAPTIVE_NICHES,
  ADAPTIVE_UI_EVENT,
  ADAPTIVE_UI_STORAGE_KEY,
  type AdaptiveDemoSelection,
  type AdaptiveNicheConfig,
} from '@/lib/adaptive-ui-config'
import { AdaptiveUIRenderer } from '@/src/modules/adaptive-ui/AdaptiveUIRenderer'
import { useAdaptiveUI } from '@/src/modules/adaptive-ui/useAdaptiveUI'

function readSelection(): AdaptiveDemoSelection | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(ADAPTIVE_UI_STORAGE_KEY)
    return raw ? (JSON.parse(raw) as AdaptiveDemoSelection) : null
  } catch {
    return null
  }
}

function useAdaptiveSelection() {
  const [selection, setSelection] = useState<AdaptiveDemoSelection | null>(null)

  useEffect(() => {
    setSelection(readSelection())
    const update = () => setSelection(readSelection())
    window.addEventListener('storage', update)
    window.addEventListener(ADAPTIVE_UI_EVENT, update)
    return () => {
      window.removeEventListener('storage', update)
      window.removeEventListener(ADAPTIVE_UI_EVENT, update)
    }
  }, [])

  return selection
}

type PublicAdaptivePage = {
  niche_id: string
  data: AdaptiveNicheConfig
  is_published: boolean
}

function isAdaptiveNicheConfig(value: unknown): value is AdaptiveNicheConfig {
  if (!value || typeof value !== 'object') return false
  const data = value as Partial<AdaptiveNicheConfig>
  return (
    typeof data.id === 'string' &&
    typeof data.label === 'string' &&
    !!data.hero &&
    Array.isArray(data.painPoints) &&
    !!data.goalBlocks
  )
}

function useAdaptiveNiches() {
  const [niches, setNiches] = useState<AdaptiveNicheConfig[]>(ADAPTIVE_NICHES)

  useEffect(() => {
    let cancelled = false
    async function loadOverrides() {
      try {
        const res = await fetch('/api/v1/public/marketing/adaptive-pages', {
          credentials: 'include',
          cache: 'no-store',
        })
        if (!res.ok) return
        const rows = (await res.json()) as PublicAdaptivePage[]
        const overrides = new Map<string, AdaptiveNicheConfig>()
        rows.forEach((row) => {
          if (row.is_published && isAdaptiveNicheConfig(row.data)) {
            overrides.set(row.niche_id, row.data)
          }
        })
        if (!cancelled) {
          setNiches(ADAPTIVE_NICHES.map((niche) => overrides.get(niche.id) ?? niche))
        }
      } catch {
        // Static config remains the safe fallback when the CMS API is unavailable.
      }
    }
    void loadOverrides()
    return () => {
      cancelled = true
    }
  }, [])

  return niches
}

export function AdaptiveHeroContent({ fallback }: { fallback: React.ReactNode }) {
  const selection = useAdaptiveSelection()
  const niches = useAdaptiveNiches()
  const adaptive = useAdaptiveUI({
    businessType: selection?.nicheId,
    painPoints: selection?.painPointIds ?? [],
    goal: selection?.goal,
    niches,
  })

  return <AdaptiveUIRenderer adaptive={adaptive} mode="hero" fallback={fallback} />
}

export function AdaptiveHeroVisual({ fallback }: { fallback: React.ReactNode }) {
  const selection = useAdaptiveSelection()
  const niches = useAdaptiveNiches()
  const adaptive = useAdaptiveUI({
    businessType: selection?.nicheId,
    painPoints: selection?.painPointIds ?? [],
    goal: selection?.goal,
    niches,
  })

  return <AdaptiveUIRenderer adaptive={adaptive} mode="visual" fallback={fallback} />
}

export function AdaptiveHomepageSections() {
  const selection = useAdaptiveSelection()
  const niches = useAdaptiveNiches()
  const adaptive = useAdaptiveUI({
    businessType: selection?.nicheId,
    painPoints: selection?.painPointIds ?? [],
    goal: selection?.goal,
    niches,
  })

  return <AdaptiveUIRenderer adaptive={adaptive} mode="sections" />
}
