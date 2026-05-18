'use client'

/**
 * AnnouncementTicker — rotates 5 sales & marketing messages across
 * the top announcement bar using a smooth crossfade via framer-motion.
 */

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, TrendingUp, Star, Zap, MessageSquare } from 'lucide-react'

const MESSAGES = [
  {
    icon: Sparkles,
    label: 'New',
    text: 'AI Sales Assistant — drafts replies, scores leads, predicts churn.',
    cta: 'See how it works →',
    href: '#platform',
  },
  {
    icon: TrendingUp,
    label: 'Results',
    text: 'UK tradesmen averaging 340% ROI in their first 90 days on CustomerFlow AI.',
    cta: 'Start free trial →',
    href: '/register',
  },
  {
    icon: Star,
    label: 'Reviews',
    text: 'Collect 4× more Google reviews — automatically. No chasing, no awkward asks.',
    cta: 'See review automation →',
    href: '#platform',
  },
  {
    icon: Zap,
    label: 'Speed',
    text: 'Missed-call SMS recovery in 60 seconds. Win back leads before they dial a competitor.',
    cta: 'Learn more →',
    href: '#how-it-works',
  },
  {
    icon: MessageSquare,
    label: 'Automation',
    text: '5-touch automated follow-up sequences — quotes chase themselves, deposits collected online.',
    cta: 'Explore the platform →',
    href: '#platform',
  },
]

const INTERVAL_MS = 4500

export function AnnouncementTicker() {
  const [idx, setIdx] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setIdx((i) => (i + 1) % MESSAGES.length), INTERVAL_MS)
    return () => clearInterval(t)
  }, [])

  const msg = MESSAGES[idx]
  const Icon = msg.icon

  return (
    <div className="relative overflow-hidden border-b border-brand-forest-800/30 bg-brand-forest-900">
      <div className="container flex h-9 items-center justify-center gap-3 text-[12px] font-medium text-brand-forest-foreground/90">
        <AnimatePresence mode="wait">
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
            className="flex items-center gap-3"
          >
            <span className="inline-flex items-center gap-1 text-brand-teal-300">
              <Icon className="h-3 w-3" />
              {msg.label}
            </span>
            <span className="hidden sm:inline">{msg.text}</span>
            <span className="sm:hidden truncate max-w-[200px]">{msg.text}</span>
            <a
              href={msg.href}
              className="font-semibold text-brand-teal-300 hover:underline"
            >
              {msg.cta}
            </a>
          </motion.div>
        </AnimatePresence>

        {/* Dot indicators */}
        <div className="absolute right-4 hidden items-center gap-1 sm:flex">
          {MESSAGES.map((_, i) => (
            <button
              key={i}
              onClick={() => setIdx(i)}
              aria-label={`Message ${i + 1}`}
              className={`h-1 rounded-full transition-all duration-300 ${
                i === idx ? 'w-4 bg-brand-teal-300' : 'w-1 bg-white/20 hover:bg-white/40'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
