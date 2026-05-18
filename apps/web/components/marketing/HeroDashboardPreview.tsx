'use client'

import { motion, useInView } from 'framer-motion'
import { Star } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { AnimatedCounter } from './AnimatedCounter'

const KPIS = [
  { label: 'New leads', value: 24, delta: '+12%', tone: 'forest' as const },
  { label: 'Booked jobs', value: 8, delta: '+3', tone: 'forest' as const },
  { label: 'Reviews', value: 63, delta: '+5', tone: 'teal' as const },
]

const PIPELINE = [
  { stage: 'New', h: 40 },
  { stage: 'Contacted', h: 70 },
  { stage: 'Quoted', h: 55 },
  { stage: 'Booked', h: 42 },
  { stage: 'Done', h: 64 },
]

/**
 * The dashboard preview that lives in the marketing hero. Animates:
 *
 * 1. KPI counters tick up from 0 → final value as the card scrolls into view.
 * 2. Pipeline bars grow from 0 → target height with a staggered spring.
 * 3. A "new lead" notification slides into the bottom slot every few seconds.
 * 4. The "synced" pulse on the chrome strip keeps a slow heartbeat.
 */
export function HeroDashboardPreview() {
  const containerRef = useRef<HTMLDivElement>(null)
  const inView = useInView(containerRef, { once: true, margin: '-10% 0px' })

  const leads = [
    {
      initials: 'JD',
      name: 'John Davis',
      detail: 'Emergency boiler repair · Manchester M14',
      tag: 'Auto-SMS · 38s',
    },
    {
      initials: 'PR',
      name: 'Priya Rana',
      detail: 'Salon rebook · Leeds LS1',
      tag: 'Auto-reply · 12s',
    },
    {
      initials: 'BO',
      name: "Brendan O'Connor",
      detail: 'EV charger install · Bristol BS8',
      tag: 'Auto-quote · 41s',
    },
  ]
  const [leadIdx, setLeadIdx] = useState(0)
  useEffect(() => {
    if (!inView) return
    const id = setInterval(() => setLeadIdx((i) => (i + 1) % leads.length), 4200)
    return () => clearInterval(id)
  }, [inView, leads.length])

  const lead = leads[leadIdx]

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative overflow-hidden rounded-xl border border-border bg-card shadow-elevated">
        {/* Chrome */}
        <div className="flex items-center justify-between border-b border-border bg-muted/40 px-4 py-3">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-border" />
            <span className="h-2.5 w-2.5 rounded-full bg-border" />
            <span className="h-2.5 w-2.5 rounded-full bg-border" />
          </div>
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            app.customerflow.ai · live
          </span>
          <span className="inline-flex items-center gap-1 rounded-full bg-brand-forest-50 px-2 py-0.5 text-[10px] font-semibold text-brand-forest-700">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-brand-forest-500" />
            Synced
          </span>
        </div>

        <div className="space-y-4 p-5">
          {/* KPI row */}
          <div className="grid grid-cols-3 gap-2.5">
            {KPIS.map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, y: 8 }}
                animate={inView ? { opacity: 1, y: 0 } : undefined}
                transition={{ delay: 0.08 * i, duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
                className="rounded-md border border-border bg-background p-3"
              >
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  {s.label}
                </p>
                <p className="mt-1 font-display text-2xl font-bold tabular text-foreground">
                  <AnimatedCounter value={s.value} duration={1.4} />
                </p>
                <p
                  className={`mt-0.5 text-[11px] font-semibold ${
                    s.tone === 'teal' ? 'text-brand-teal-600' : 'text-brand-forest-700'
                  }`}
                >
                  {s.delta} <span className="text-muted-foreground">vs last week</span>
                </p>
              </motion.div>
            ))}
          </div>

          {/* Pipeline bars */}
          <div className="rounded-md border border-border bg-background p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Pipeline · this month
              </p>
              <span className="font-mono text-[10px] text-muted-foreground">
                <AnimatedCounter prefix="£" value={42180} duration={1.8} />
              </span>
            </div>
            <div className="flex h-20 items-end gap-1.5">
              {PIPELINE.map((s, i) => (
                <div key={s.stage} className="flex flex-1 flex-col items-center gap-1.5">
                  <motion.div
                    initial={{ height: 0 }}
                    animate={inView ? { height: `${s.h}px` } : undefined}
                    transition={{
                      delay: 0.5 + i * 0.08,
                      duration: 0.7,
                      ease: [0.16, 1, 0.3, 1],
                    }}
                    className="w-full rounded-sm"
                    style={{
                      backgroundColor:
                        i === 4
                          ? 'hsl(var(--brand-forest))'
                          : i === 3
                          ? 'hsl(var(--brand-teal))'
                          : 'hsl(var(--brand-forest) / 0.30)',
                    }}
                  />
                  <p className="text-[9px] font-medium uppercase tracking-wide text-muted-foreground">
                    {s.stage}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Rotating "new lead" notification */}
          <motion.div
            key={lead.initials}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.35 }}
            className="flex items-center gap-3 rounded-md border border-border bg-brand-forest-50/50 p-3"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-forest-700 font-mono text-[10px] font-bold text-brand-forest-foreground">
              {lead.initials}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-foreground">
                New lead · {lead.name}
              </p>
              <p className="truncate text-[11px] text-muted-foreground">{lead.detail}</p>
            </div>
            <span className="whitespace-nowrap rounded-full bg-brand-teal-400/90 px-2 py-1 font-mono text-[9px] font-bold uppercase tracking-wider text-brand-teal-foreground">
              {lead.tag}
            </span>
          </motion.div>
        </div>
      </div>

      {/* Floating Google-review pill */}
      <motion.div
        initial={{ opacity: 0, scale: 0.92 }}
        animate={inView ? { opacity: 1, scale: 1 } : undefined}
        transition={{ delay: 1.2, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="absolute -right-4 -top-3 hidden rounded-lg border border-border bg-card p-3 shadow-elevated sm:block"
      >
        <div className="flex items-center gap-2">
          <div className="flex gap-0.5">
            {[...Array(5)].map((_, i) => (
              <Star key={i} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
            ))}
          </div>
          <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            Google · auto-collected
          </p>
        </div>
      </motion.div>
    </div>
  )
}
