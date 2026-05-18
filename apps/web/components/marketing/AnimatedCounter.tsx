'use client'

import { motion, useInView, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { useEffect, useRef } from 'react'

interface AnimatedCounterProps {
  /** The final integer value to animate to. */
  value: number
  /** Prefix character (e.g. "£"). */
  prefix?: string
  /** Suffix character (e.g. "+", "%", "s"). */
  suffix?: string
  /** Number of decimal places to display (default 0). */
  decimals?: number
  /** Animation duration in seconds (default 1.6). */
  duration?: number
  /** Class names forwarded to the wrapping span. */
  className?: string
  /**
   * Format very large numbers as `12.4k` etc. Default false — we usually
   * want exact figures on a marketing site.
   */
  compact?: boolean
}

/**
 * KPI counter that animates from 0 → `value` the first time it scrolls into view.
 *
 * Uses `framer-motion` springs so the curve feels enterprise-y (fast first,
 * slower settle) without bouncing past the target.
 */
export function AnimatedCounter({
  value,
  prefix,
  suffix,
  decimals = 0,
  duration = 1.6,
  className,
  compact = false,
}: AnimatedCounterProps) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, margin: '-15% 0px' })
  const motionVal = useMotionValue(0)
  const spring = useSpring(motionVal, { duration: duration * 1000, bounce: 0 })
  const display = useTransform(spring, (v) => formatNumber(v, decimals, compact))

  useEffect(() => {
    if (inView) motionVal.set(value)
  }, [inView, motionVal, value])

  return (
    <span ref={ref} className={className}>
      {prefix}
      <motion.span>{display}</motion.span>
      {suffix}
    </span>
  )
}

function formatNumber(v: number, decimals: number, compact: boolean): string {
  const rounded = decimals > 0 ? Number(v.toFixed(decimals)) : Math.round(v)
  if (compact) {
    if (rounded >= 1_000_000) return `${(rounded / 1_000_000).toFixed(1)}M`
    if (rounded >= 1_000) return `${(rounded / 1_000).toFixed(rounded >= 10_000 ? 0 : 1)}k`
  }
  return rounded.toLocaleString('en-GB', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}
