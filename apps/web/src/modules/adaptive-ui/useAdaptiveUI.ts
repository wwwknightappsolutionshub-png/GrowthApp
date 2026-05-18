'use client'

import { useMemo } from 'react'
import {
  type AdaptiveGoal,
  type AdaptiveNicheConfig,
  type AdaptivePainPoint,
  ADAPTIVE_NICHES,
  getAdaptiveNiche,
} from '@/lib/adaptive-ui-config'

export type UseAdaptiveUIInput = {
  businessType: string | null | undefined
  painPoints: string[]
  goal: AdaptiveGoal | null | undefined
  niches?: AdaptiveNicheConfig[]
}

export type AdaptiveUIResult = {
  nicheId: string
  nicheName: string
  hero: {
    eyebrow: string
    headline: string
    subheadline: string
    primaryCta: string
    secondaryCta: string
  }
  painPointBlocks: AdaptivePainPoint[]
  goalBlock: { title: string; body: string }
  testimonial: { quote: string; name: string; role: string } | null
  testimonialBlock: { quote: string; name: string; role: string }[]
  cta: { text: string; href: string }
  imageSet: { hero: string; heroAlt: string }
  whyBlock: { title: string; body: string }
} | null

export function useAdaptiveUI({
  businessType,
  painPoints,
  goal,
  niches,
}: UseAdaptiveUIInput): AdaptiveUIResult {
  return useMemo(() => {
    const source = niches ?? ADAPTIVE_NICHES
    const niche = businessType
      ? source.find((nicheConfig) => nicheConfig.id === businessType) ?? getAdaptiveNiche(businessType)
      : null
    if (!niche) return null

    const safeGoal: AdaptiveGoal = goal ?? 'grow'
    const validPainPointIds = new Set(niche.painPoints.map((painPoint) => painPoint.id))
    const safePainPoints = painPoints.filter((painPointId) => validPainPointIds.has(painPointId))

    const selectedPainPoints = niche.painPoints.filter((painPoint) => safePainPoints.includes(painPoint.id))
    const painPointBlocks = selectedPainPoints.length
      ? selectedPainPoints
      : niche.painPoints.slice(0, 3)

    return {
      nicheId: niche.id,
      nicheName: niche.label,
      hero: {
        eyebrow: niche.hero.eyebrow,
        headline: niche.hero.headline,
        subheadline: niche.hero.subheadline,
        primaryCta: niche.hero.primaryCta,
        secondaryCta: niche.hero.secondaryCta,
      },
      painPointBlocks,
      goalBlock: niche.goalBlocks[safeGoal],
      testimonial: niche.testimonials[0] ?? null,
      testimonialBlock: niche.testimonials,
      cta: { text: niche.ctaText, href: '/register' },
      imageSet: { hero: niche.hero.image, heroAlt: niche.hero.imageAlt },
      whyBlock: niche.whyBlock,
    }
  }, [businessType, goal, niches, painPoints])
}
