'use client'

/**
 * Animated "growth loop" step cards.
 * Each card fans in sequentially when it enters the viewport.
 */

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { Target, MessageSquare, Calendar, Award, TrendingUp, type LucideIcon } from 'lucide-react'

interface Step {
  step: string
  icon: LucideIcon
  title: string
  desc: string
}

const steps: Step[] = [
  {
    step: '01',
    icon: Target,
    title: 'Capture',
    desc: 'Form, missed call, referral or social — every touchpoint becomes a tracked lead.',
  },
  {
    step: '02',
    icon: MessageSquare,
    title: 'Nurture',
    desc: 'AI sequences chase at the right cadence — no manual follow-up, no leads going cold.',
  },
  {
    step: '03',
    icon: Calendar,
    title: 'Book',
    desc: 'Quote sent, accepted online, Stripe deposit collected, booking confirmed automatically.',
  },
  {
    step: '04',
    icon: Award,
    title: 'Delight',
    desc: 'Job done. Review request auto-sent. Happy customers go public, unhappy stay private.',
  },
  {
    step: '05',
    icon: TrendingUp,
    title: 'Grow',
    desc: 'Reviews attract new customers. AI posts build authority. The loop repeats — hands-free.',
  },
]

const cardVariants = {
  hidden: { opacity: 0, y: 28, scale: 0.96 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: i * 0.1,
      duration: 0.55,
      ease: [0.22, 1, 0.36, 1],
    },
  }),
}

const iconVariants = {
  hidden: { rotate: -12, opacity: 0 },
  visible: (i: number) => ({
    rotate: 0,
    opacity: 0.6,
    transition: { delay: i * 0.1 + 0.25, duration: 0.4, ease: 'easeOut' },
  }),
}

const connectorVariants = {
  hidden: { scaleX: 0 },
  visible: (i: number) => ({
    scaleX: 1,
    transition: { delay: i * 0.1 + 0.35, duration: 0.4, ease: 'easeOut' },
  }),
}

export function GrowthLoopCards() {
  const ref = useRef<HTMLOListElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <ol
      ref={ref}
      className="mt-16 grid gap-px overflow-hidden rounded-xl border border-white/10 bg-white/10 md:grid-cols-5"
    >
      {steps.map((step, i) => {
        const Icon = step.icon
        return (
          <motion.li
            key={step.step}
            custom={i}
            initial="hidden"
            animate={inView ? 'visible' : 'hidden'}
            variants={cardVariants}
            className="group relative flex flex-col gap-4 bg-brand-forest-950 p-6 lg:p-7"
          >
            {/* Animated connector line (hidden on last card) */}
            {i < steps.length - 1 && (
              <motion.span
                custom={i}
                initial="hidden"
                animate={inView ? 'visible' : 'hidden'}
                variants={connectorVariants}
                aria-hidden
                className="absolute right-0 top-10 hidden h-px w-full origin-left bg-brand-teal-300/20 md:block"
                style={{ width: '1px', height: '2px', right: '-1px', top: '2.5rem' }}
              />
            )}

            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-brand-teal-300">
                {step.step}
              </span>
              <motion.span
                custom={i}
                initial="hidden"
                animate={inView ? 'visible' : 'hidden'}
                variants={iconVariants}
              >
                <Icon className="h-4 w-4 text-white/60 transition-colors group-hover:text-brand-teal-300" strokeWidth={2} />
              </motion.span>
            </div>

            <motion.h3
              custom={i}
              initial={{ opacity: 0 }}
              animate={inView ? { opacity: 1 } : { opacity: 0 }}
              transition={{ delay: i * 0.1 + 0.3, duration: 0.4 }}
              className="font-display text-lg font-bold text-white"
            >
              {step.title}
            </motion.h3>

            <motion.p
              custom={i}
              initial={{ opacity: 0 }}
              animate={inView ? { opacity: 1 } : { opacity: 0 }}
              transition={{ delay: i * 0.1 + 0.4, duration: 0.45 }}
              className="text-sm leading-relaxed text-white/60"
            >
              {step.desc}
            </motion.p>

            {/* Hover glow accent */}
            <span
              aria-hidden
              className="pointer-events-none absolute inset-0 rounded-none opacity-0 transition-opacity duration-300 group-hover:opacity-100"
              style={{
                background:
                  'radial-gradient(ellipse 80% 50% at 50% 100%, hsl(var(--brand-teal)/0.08), transparent 70%)',
              }}
            />
          </motion.li>
        )
      })}
    </ol>
  )
}
