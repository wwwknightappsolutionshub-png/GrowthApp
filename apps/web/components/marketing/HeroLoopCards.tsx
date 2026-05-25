'use client'

import { motion } from 'framer-motion'
import { Calendar, CreditCard, Megaphone, Target, Users } from 'lucide-react'

const STEPS = [
  {
    step: 'Lead',
    desc: 'Capture & respond instantly',
    icon: Target,
    gradient: 'from-amber-500/20 via-orange-500/10 to-transparent',
    ring: 'ring-amber-500/30',
    iconBg: 'bg-amber-500/15 text-amber-700',
    glow: 'hover:shadow-[0_0_28px_-4px_rgba(245,158,11,0.5)]',
  },
  {
    step: 'Booking',
    desc: 'Schedule jobs & fill your diary',
    icon: Calendar,
    gradient: 'from-violet-500/15 via-purple-500/10 to-transparent',
    ring: 'ring-violet-400/30',
    iconBg: 'bg-violet-500/15 text-violet-700',
    glow: 'hover:shadow-[0_0_28px_-4px_rgba(139,92,246,0.4)]',
  },
  {
    step: 'CRM',
    desc: 'Quote, track & close every deal',
    icon: Users,
    gradient: 'from-brand-teal-400/25 via-brand-teal-500/10 to-transparent',
    ring: 'ring-brand-teal-400/35',
    iconBg: 'bg-brand-teal-400/20 text-brand-teal-700',
    glow: 'hover:shadow-[0_0_28px_-4px_rgba(32,204,206,0.45)]',
  },
  {
    step: 'Accounts',
    desc: 'Invoice, collect & track cashflow',
    icon: CreditCard,
    gradient: 'from-emerald-500/15 via-green-500/10 to-transparent',
    ring: 'ring-emerald-400/30',
    iconBg: 'bg-emerald-500/15 text-emerald-700',
    glow: 'hover:shadow-[0_0_28px_-4px_rgba(16,185,129,0.4)]',
  },
  {
    step: 'Retarget',
    desc: 'Reviews, loyalty & win-back',
    icon: Megaphone,
    gradient: 'from-rose-500/15 via-pink-500/10 to-transparent',
    ring: 'ring-rose-400/30',
    iconBg: 'bg-rose-500/15 text-rose-700',
    glow: 'hover:shadow-[0_0_28px_-4px_rgba(244,63,94,0.4)]',
  },
] as const

export function HeroLoopCards() {
  return (
    <div className="mt-6 grid gap-2 sm:grid-cols-2 lg:max-w-xl">
      {STEPS.map(({ step, desc, icon: Icon, gradient, ring, iconBg, glow }, i) => (
        <motion.div
          key={step}
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-40px' }}
          transition={{ delay: 0.08 * i, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          whileHover={{ y: -3, scale: 1.02 }}
          className={`group relative overflow-hidden rounded-xl border border-border/80 bg-card/70 p-3 text-left backdrop-blur-sm transition-all duration-300 hover:ring-1 ${ring} ${glow}`}
        >
          <div
            aria-hidden
            className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 transition-opacity duration-500 group-hover:opacity-100`}
          />
          <div className="relative flex items-start gap-2.5">
            <motion.span
              animate={{ scale: [1, 1.06, 1] }}
              transition={{ duration: 2.4, repeat: Infinity, delay: i * 0.35 }}
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${iconBg} ring-1 ring-white/50`}
            >
              <Icon className="h-4 w-4" strokeWidth={2.2} />
            </motion.span>
            <div>
              <p className="text-sm font-bold tracking-tight text-foreground">{step}</p>
              <p className="mt-0.5 text-[11px] leading-snug text-muted-foreground">{desc}</p>
            </div>
          </div>
          <motion.div
            className="absolute bottom-0 left-0 h-0.5 bg-brand-teal-500/80"
            initial={{ width: '0%' }}
            whileInView={{ width: '100%' }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 + i * 0.12, duration: 0.7 }}
          />
        </motion.div>
      ))}
    </div>
  )
}
