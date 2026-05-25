'use client'

import { AnimatePresence, motion, useInView } from 'framer-motion'
import {
  ArrowRight,
  Calendar,
  CheckCircle2,
  CreditCard,
  Megaphone,
  PoundSterling,
  Star,
  Target,
  Users,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { cn } from '@/lib/utils'

type SceneId = 'leads' | 'bookings' | 'crm' | 'accounts' | 'retarget'

const SCENES: Array<{
  id: SceneId
  label: string
  caption: string
  durationMs: number
}> = [
  { id: 'leads', label: 'Lead', caption: 'Capture & respond', durationMs: 3800 },
  { id: 'bookings', label: 'Bookings', caption: 'Diary & slots', durationMs: 3800 },
  { id: 'crm', label: 'CRM', caption: 'Pipeline & quotes', durationMs: 3800 },
  { id: 'accounts', label: 'Accounts', caption: 'Invoice & pay', durationMs: 3800 },
  { id: 'retarget', label: 'Retarget', caption: 'Reviews & win-back', durationMs: 3800 },
]

function SceneChrome({ active, progress }: { active: SceneId; progress: number }) {
  const scene = SCENES.find((s) => s.id === active)!
  return (
    <div className="relative shrink-0 border-b border-border bg-muted/50 px-2 py-1.5 sm:px-3 sm:py-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex shrink-0 items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-red-400/80 sm:h-2 sm:w-2" />
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400/80 sm:h-2 sm:w-2" />
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400/80 sm:h-2 sm:w-2" />
        </div>
        <div className="flex min-w-0 flex-1 flex-wrap justify-center gap-0.5 sm:gap-1">
          {SCENES.map((s) => (
            <span
              key={s.id}
              className={cn(
                'rounded px-1 py-px text-[7px] font-semibold uppercase tracking-wide sm:px-1.5 sm:py-0.5 sm:text-[8px]',
                s.id === active
                  ? 'bg-brand-forest-700 text-brand-forest-foreground'
                  : 'text-muted-foreground',
              )}
            >
              {s.label}
            </span>
          ))}
        </div>
        <span className="hidden shrink-0 font-mono text-[8px] text-muted-foreground lg:inline">
          {scene.caption}
        </span>
      </div>
      <div className="absolute inset-x-0 bottom-0 h-0.5 bg-border">
        <motion.div className="h-full bg-brand-teal-500" style={{ width: `${progress * 100}%` }} />
      </div>
    </div>
  )
}

function LeadsScene() {
  const rows = [
    { initials: 'JD', name: 'John Davis', detail: 'Boiler repair · M14', tag: 'Hot', hot: true },
    { initials: 'PR', name: 'Priya Rana', detail: 'Salon rebook · LS1', tag: 'New', hot: false },
    { initials: 'MK', name: 'Mike Kerr', detail: 'EV install · BS8', tag: 'Warm', hot: false },
  ]
  return (
    <div className="flex h-full flex-col gap-1.5 p-2 sm:p-2.5">
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold text-foreground sm:text-xs">Leads · inbox</p>
        <span className="rounded-full bg-brand-teal-400/20 px-1.5 py-px text-[8px] font-bold text-brand-teal-700">
          7 today
        </span>
      </div>
      <div className="min-h-0 flex-1 space-y-1 overflow-hidden">
        {rows.map((row, i) => (
          <motion.div
            key={row.initials}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15 + i * 0.12 }}
            className={cn(
              'flex items-center gap-2 rounded-md border p-1.5 sm:p-2',
              row.hot ? 'border-brand-forest-200 bg-brand-forest-50/90' : 'border-border bg-card',
            )}
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-forest-700 text-[9px] font-bold text-white">
              {row.initials}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[10px] font-semibold sm:text-[11px]">{row.name}</p>
              <p className="truncate text-[8px] text-muted-foreground sm:text-[9px]">{row.detail}</p>
            </div>
            <span
              className={cn(
                'shrink-0 rounded px-1 py-px text-[7px] font-bold uppercase',
                row.hot ? 'bg-amber-100 text-amber-800' : 'bg-muted text-muted-foreground',
              )}
            >
              {row.tag}
            </span>
          </motion.div>
        ))}
      </div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.55 }}
        className="flex items-center gap-1.5 rounded-md border border-border bg-background p-1.5"
      >
        <Target className="h-3 w-3 shrink-0 text-brand-forest-700" />
        <p className="flex-1 text-[8px] leading-tight sm:text-[9px]">
          <span className="font-semibold">Auto-SMS</span> → John · replied in 38s
        </p>
      </motion.div>
      <div className="grid grid-cols-3 gap-1">
        {[['Response', '47s'], ['Quoted', '4'], ['Booked', '3']].map(([l, v]) => (
          <div key={l} className="rounded border border-border bg-muted/40 px-1 py-1 text-center">
            <p className="text-[7px] uppercase text-muted-foreground">{l}</p>
            <p className="text-[11px] font-bold tabular text-foreground">{v}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function BookingsScene() {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
  const slots = [
    ['09:00', '—', 'Service', '—', 'Quote'],
    ['11:00', 'Boiler', '—', 'EV job', '—'],
    ['14:00', '—', 'Colour', 'Boiler', '—'],
  ]
  return (
    <div className="flex h-full flex-col gap-1.5 p-2 sm:p-2.5">
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold sm:text-xs">Bookings · this week</p>
        <span className="text-[8px] text-muted-foreground">12 jobs scheduled</span>
      </div>
      <div className="min-h-0 flex-1 overflow-hidden rounded-md border border-border">
        <div className="grid grid-cols-6 border-b border-border bg-muted/40 text-[7px] font-semibold uppercase text-muted-foreground">
          <div className="px-1 py-1" />
          {days.map((d) => (
            <div key={d} className="border-l border-border px-0.5 py-1 text-center">
              {d}
            </div>
          ))}
        </div>
        {slots.map(([time, ...cells]) => (
          <div key={time} className="grid grid-cols-6 border-b border-border last:border-0">
            <div className="px-1 py-1 text-[8px] text-muted-foreground">{time}</div>
            {cells.map((cell, i) => (
              <div key={`${time}-${i}`} className="border-l border-border p-0.5">
                {cell !== '—' ? (
                  <motion.span
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.2 + i * 0.15 }}
                    className={cn(
                      'block truncate rounded px-0.5 py-px text-[7px] font-medium sm:text-[8px]',
                      cell === 'Boiler'
                        ? 'bg-brand-forest-700 text-brand-forest-foreground'
                        : 'bg-brand-teal-400/25 text-brand-teal-800',
                    )}
                  >
                    {cell}
                  </motion.span>
                ) : null}
              </div>
            ))}
          </div>
        ))}
      </div>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="flex items-center gap-1.5 rounded-md border border-violet-200 bg-violet-50 px-2 py-1.5"
      >
        <Calendar className="h-3 w-3 text-violet-700" />
        <p className="text-[8px] sm:text-[9px]">
          <span className="font-semibold">John Davis</span> booked · Tue 11:00 · confirmation sent
        </p>
      </motion.div>
      <div className="grid grid-cols-3 gap-1">
        {[['Today', '3'], ['Tomorrow', '2'], ['Open slots', '5']].map(([l, v]) => (
          <div key={l} className="rounded border border-border bg-muted/40 py-1 text-center">
            <p className="text-[7px] text-muted-foreground">{l}</p>
            <p className="text-[11px] font-bold">{v}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function CrmScene() {
  const cols = [
    { name: 'New', items: ['Leak call'] },
    { name: 'Quoted', items: ['Boiler £840', 'Rewire £2.1k'] },
    { name: 'Won', items: ['EV charger'] },
    { name: 'Done', items: ['Service x2'] },
  ]
  return (
    <div className="flex h-full flex-col gap-1.5 p-2 sm:p-2.5">
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold sm:text-xs">CRM · pipeline</p>
        <span className="text-[8px] font-medium text-brand-forest-700">£42k weighted</span>
      </div>
      <div className="grid min-h-0 flex-1 grid-cols-4 gap-1">
        {cols.map((col) => (
          <div key={col.name} className="flex flex-col rounded border border-border bg-muted/20 p-1">
            <p className="mb-1 text-[7px] font-semibold uppercase text-muted-foreground">{col.name}</p>
            <div className="flex flex-1 flex-col gap-0.5">
              {col.items.map((item) => (
                <div
                  key={item}
                  className="rounded border border-border bg-card px-1 py-0.5 text-[7px] font-medium leading-tight sm:text-[8px]"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="flex items-center gap-1.5 rounded-md border border-border p-1.5"
      >
        <Users className="h-3 w-3 text-brand-forest-700" />
        <p className="text-[8px] sm:text-[9px]">
          Quote <strong>#Q-1042</strong> sent to John · follow-up in 2 days
        </p>
      </motion.div>
      <div className="grid grid-cols-4 gap-1 text-center">
        {[['Deals', '18'], ['Win rate', '34%'], ['Avg deal', '£680'], ['Tasks', '6']].map(([l, v]) => (
          <div key={l} className="rounded border border-border bg-muted/30 py-1">
            <p className="text-[7px] text-muted-foreground">{l}</p>
            <p className="text-[10px] font-bold">{v}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function AccountsScene() {
  const [paid, setPaid] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setPaid(true), 1600)
    return () => clearTimeout(t)
  }, [])

  const invoices = [
    { id: '#1041', who: 'Priya Rana', amt: '£120', status: 'Paid' },
    { id: '#1042', who: 'John Davis', amt: '£840', status: paid ? 'Paid' : 'Sent' },
    { id: '#1043', who: 'Mike Kerr', amt: '£2,400', status: 'Draft' },
  ]

  return (
    <div className="flex h-full flex-col gap-1.5 p-2 sm:p-2.5">
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold sm:text-xs">Accounts · cashflow</p>
        <span className="flex items-center gap-0.5 text-[8px] font-semibold text-emerald-600">
          <PoundSterling className="h-2.5 w-2.5" />
          +£840 today
        </span>
      </div>
      <div className="grid grid-cols-2 gap-1 rounded-md border border-border bg-muted/20 p-2">
        <div>
          <p className="text-[7px] text-muted-foreground">Outstanding</p>
          <p className="text-sm font-bold tabular">£1,240</p>
        </div>
        <div className="text-right">
          <p className="text-[7px] text-muted-foreground">Paid this week</p>
          <p className="text-sm font-bold tabular text-brand-forest-700">£6,420</p>
        </div>
      </div>
      <div className="min-h-0 flex-1 space-y-1 overflow-hidden">
        {invoices.map((inv, i) => (
          <motion.div
            key={inv.id}
            initial={{ opacity: 0, x: 8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 + i * 0.1 }}
            className="flex items-center justify-between rounded border border-border bg-card px-2 py-1"
          >
            <div>
              <p className="text-[9px] font-semibold">
                Invoice {inv.id} · {inv.who}
              </p>
              <p className="text-[8px] text-muted-foreground">{inv.amt}</p>
            </div>
            <span
              className={cn(
                'rounded-full px-1.5 py-px text-[7px] font-bold uppercase',
                inv.status === 'Paid'
                  ? 'bg-emerald-100 text-emerald-800'
                  : inv.status === 'Sent'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-muted text-muted-foreground',
              )}
            >
              {inv.status}
            </span>
          </motion.div>
        ))}
      </div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: paid ? 1 : 0.5 }}
        transition={{ delay: 1.8 }}
        className="flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1"
      >
        <CheckCircle2 className="h-3 w-3 text-emerald-700" />
        <p className="text-[8px] text-emerald-800">Stripe · #1042 marked paid · synced</p>
      </motion.div>
    </div>
  )
}

function RetargetScene() {
  return (
    <div className="flex h-full flex-col gap-1.5 p-2 sm:p-2.5">
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold sm:text-xs">Retarget · grow repeat revenue</p>
        <span className="text-[8px] text-muted-foreground">3 automations live</span>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-md border border-amber-200 bg-amber-50/80 p-2"
      >
        <div className="flex items-center gap-1.5">
          <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
          <p className="text-[9px] font-semibold">Review request · John Davis</p>
        </div>
        <p className="mt-1 text-[8px] text-muted-foreground">
          5★ routed to Google · 3★ to private feedback
        </p>
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="rounded-md border border-border bg-card p-2"
      >
        <div className="flex items-center gap-1.5">
          <Megaphone className="h-3 w-3 text-rose-600" />
          <p className="text-[9px] font-semibold">Win-back · inactive 90 days</p>
        </div>
        <p className="mt-1 text-[8px] text-muted-foreground">
          SMS + email offer sent to 12 customers · 3 rebooked
        </p>
      </motion.div>
      <div className="min-h-0 flex-1 space-y-1">
        {[
          ['Loyalty points issued', '+240 pts · 8 customers'],
          ['Membership renewal', 'Salon plan · due Fri'],
          ['Refer & Win', '2 new leads from referrals'],
        ].map(([title, sub], i) => (
          <motion.div
            key={title}
            initial={{ opacity: 0, x: 6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 + i * 0.12 }}
            className="flex items-center justify-between rounded border border-border bg-muted/30 px-2 py-1"
          >
            <p className="text-[8px] font-medium sm:text-[9px]">{title}</p>
            <p className="text-[7px] text-muted-foreground">{sub}</p>
          </motion.div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-1">
        {[['Reviews', '63'], ['Repeat', '41%'], ['LTV', '↑12%']].map(([l, v]) => (
          <div key={l} className="rounded border border-border bg-muted/40 py-1 text-center">
            <p className="text-[7px] text-muted-foreground">{l}</p>
            <p className="text-[10px] font-bold">{v}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export function HeroProductDemo({
  size = 'default',
  className,
}: {
  size?: 'default' | 'large'
  className?: string
}) {
  const large = size === 'large'
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-8% 0px' })
  const [sceneIdx, setSceneIdx] = useState(0)
  const [progress, setProgress] = useState(0)

  const scene = SCENES[sceneIdx]

  useEffect(() => {
    if (!inView) return
    setProgress(0)
    const start = Date.now()
    const tick = setInterval(() => {
      setProgress(Math.min((Date.now() - start) / scene.durationMs, 1))
    }, 50)
    const next = setTimeout(() => setSceneIdx((i) => (i + 1) % SCENES.length), scene.durationMs)
    return () => {
      clearInterval(tick)
      clearTimeout(next)
    }
  }, [inView, sceneIdx, scene.durationMs])

  return (
    <div ref={ref} className={cn('relative flex h-full min-h-[380px] flex-col', className)}>
      <div
        className={cn(
          'relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-border bg-card shadow-elevated',
          large && 'rounded-2xl shadow-2xl',
        )}
      >
        <SceneChrome active={scene.id} progress={progress} />
        <div className="relative min-h-0 flex-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={scene.id}
              className="absolute inset-0 flex flex-col"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.28 }}
            >
              {scene.id === 'leads' && <LeadsScene />}
              {scene.id === 'bookings' && <BookingsScene />}
              {scene.id === 'crm' && <CrmScene />}
              {scene.id === 'accounts' && <AccountsScene />}
              {scene.id === 'retarget' && <RetargetScene />}
            </motion.div>
          </AnimatePresence>
        </div>
        <div className="flex shrink-0 items-center justify-between border-t border-border bg-muted/30 px-2 py-1 sm:px-3 sm:py-1.5">
          <span className="inline-flex items-center gap-1 text-[8px] text-muted-foreground sm:text-[9px]">
            <CreditCard className="h-2.5 w-2.5" />
            Lead → Bookings → CRM → Accounts → Retarget
          </span>
          <span className="inline-flex items-center gap-0.5 text-[8px] font-medium text-brand-forest-700 sm:text-[9px]">
            Live demo
            <ArrowRight className="h-2.5 w-2.5" />
          </span>
        </div>
      </div>
    </div>
  )
}
