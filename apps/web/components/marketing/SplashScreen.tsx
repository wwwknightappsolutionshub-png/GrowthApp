'use client'

/**
 * Full-screen splash overlay shown on first page load.
 * Persisted via localStorage so returning visitors (same browser) never see it again.
 * Uses framer-motion for a smooth fade-out on dismiss.
 */

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import {
  ArrowRight,
  Shield,
  RefreshCw,
  Lock,
  Users,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import {
  ADAPTIVE_NICHES,
  ADAPTIVE_UI_EVENT,
  ADAPTIVE_UI_STORAGE_KEY,
  GOAL_OPTIONS,
  type AdaptiveGoal,
} from '@/lib/adaptive-ui-config'

const SPLASH_KEY = 'cf_splash_v1'

export function SplashScreen() {
  const [visible, setVisible] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [mode, setMode] = useState<'intro' | 'demo'>('intro')
  const [selectedNicheId, setSelectedNicheId] = useState(ADAPTIVE_NICHES[0]?.id ?? '')
  const [selectedPainPointIds, setSelectedPainPointIds] = useState<string[]>([])
  const [goal, setGoal] = useState<AdaptiveGoal>('grow')

  useEffect(() => {
    setMounted(true)
    try {
      if (!localStorage.getItem(SPLASH_KEY)) {
        setVisible(true)
      }
    } catch {
      // localStorage blocked (private browsing edge case) — skip splash
    }
  }, [])

  function dismiss() {
    try {
      localStorage.setItem(SPLASH_KEY, Date.now().toString())
    } catch {
      // ignore
    }
    setVisible(false)
  }

  const selectedNiche =
    ADAPTIVE_NICHES.find((niche) => niche.id === selectedNicheId) ?? ADAPTIVE_NICHES[0]

  function togglePainPoint(id: string) {
    setSelectedPainPointIds((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id)
      if (current.length >= 3) return current
      return [...current, id]
    })
  }

  function submitDemo() {
    const painPointIds = selectedPainPointIds.length
      ? selectedPainPointIds
      : selectedNiche.painPoints.slice(0, 3).map((painPoint) => painPoint.id)
    try {
      localStorage.setItem(
        ADAPTIVE_UI_STORAGE_KEY,
        JSON.stringify({ nicheId: selectedNiche.id, painPointIds, goal }),
      )
      window.dispatchEvent(new CustomEvent(ADAPTIVE_UI_EVENT))
    } catch {
      // ignore
    }
    dismiss()
  }

  // Avoid SSR flash — render nothing until client hydration
  if (!mounted) return null

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          key="splash"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 1.04 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="fixed inset-0 z-[9999] flex flex-col overflow-y-auto overscroll-contain bg-brand-forest-950"
          role="dialog"
          aria-modal="true"
          aria-label="Welcome to CustomerFlow AI"
        >
          {/* Background grid + glow */}
          <div aria-hidden className="absolute inset-0 bg-grid-forest opacity-100" />
          <div
            aria-hidden
            className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_50%,hsl(var(--brand-teal)/0.18),transparent_70%)]"
          />

          {/* Pexels background image (subtle, blended) */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg?auto=compress&cs=tinysrgb&w=1920&q=70"
            alt=""
            aria-hidden
            className="absolute inset-0 h-full w-full object-cover object-center opacity-10"
          />
          <motion.div
            aria-hidden
            className="absolute left-[8%] top-[22%] hidden rounded-2xl border border-brand-teal-300/20 bg-white/5 px-4 py-3 text-left shadow-2xl backdrop-blur lg:block"
            animate={{ y: [0, -14, 0], rotate: [-1, 1, -1] }}
            transition={{ repeat: Infinity, duration: 6, ease: 'easeInOut' }}
          >
            <p className="text-[10px] font-semibold uppercase tracking-widest text-brand-teal-300">
              Live demo
            </p>
            <p className="mt-1 text-sm font-bold text-white">+47% faster follow-up</p>
          </motion.div>
          <motion.div
            aria-hidden
            className="absolute right-[7%] top-[30%] hidden rounded-2xl border border-white/10 bg-brand-forest-900/70 px-4 py-3 text-left shadow-2xl backdrop-blur lg:block"
            animate={{ y: [0, 16, 0], rotate: [1, -1, 1] }}
            transition={{ repeat: Infinity, duration: 7, ease: 'easeInOut' }}
          >
            <p className="text-[10px] font-semibold uppercase tracking-widest text-white/45">
              Automation
            </p>
            <p className="mt-1 text-sm font-bold text-brand-teal-200">3 tasks handled</p>
          </motion.div>
          <motion.div
            aria-hidden
            className="absolute bottom-[18%] right-[18%] hidden rounded-full border border-brand-teal-300/20 bg-brand-teal-400/10 px-4 py-2 text-xs font-semibold text-brand-teal-100 shadow-2xl backdrop-blur xl:block"
            animate={{ scale: [1, 1.08, 1], opacity: [0.75, 1, 0.75] }}
            transition={{ repeat: Infinity, duration: 4, ease: 'easeInOut' }}
          >
            Personalized in 30 seconds
          </motion.div>

          {/* Top nav bar */}
          <header className="relative z-10 flex shrink-0 items-center border-b border-white/10 px-6 py-4 sm:px-10 sm:py-5">
            <span className="inline-flex items-center gap-2.5">
              <span className="relative inline-flex h-8 w-8 items-center justify-center rounded-md bg-brand-teal-400 text-brand-teal-foreground shadow-brand">
                <TrendingUp className="h-4 w-4" strokeWidth={2.5} />
                <span
                  aria-hidden
                  className="absolute -right-0.5 -bottom-0.5 h-2.5 w-2.5 rounded-full bg-white ring-2 ring-brand-forest-950"
                />
              </span>
              <span className="font-display text-[17px] font-bold tracking-tight text-white">
                CustomerFlow<span className="text-brand-teal-300">.</span>AI
              </span>
            </span>
          </header>

          {/* Main content */}
          <main className="relative z-10 flex flex-1 flex-col items-center justify-start px-6 py-8 text-center sm:justify-center sm:py-10">
            <motion.div
              initial={{ opacity: 0, y: 32 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
              className="max-w-3xl"
            >
              {mode === 'intro' ? (
                <>
                  <span className="inline-flex items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-brand-teal-300">
                    <Sparkles className="h-3 w-3" />
                    Average setup · 18 minutes
                  </span>

                  <h1 className="mt-5 font-display text-3xl font-bold leading-tight text-white sm:mt-6 sm:text-5xl lg:text-6xl xl:text-[72px] xl:leading-[1.03]">
                    More leads.
                    <br />
                    More bookings.
                    <br />
                    <span className="text-brand-teal-300">More 5-star reviews.</span>
                  </h1>

                  <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-white/70 sm:mt-6 sm:text-lg">
                    Join UK businesses already using CustomerFlow AI to grow on
                    autopilot. Your first 14 days are completely free — no credit card required.
                  </p>

                  <div className="mx-auto mt-6 grid max-w-2xl gap-3 sm:mt-8 sm:grid-cols-3">
                    {[
                      'Choose your niche',
                      'Pick your pains',
                      'Watch the page adapt',
                    ].map((label, index) => (
                      <motion.button
                        key={label}
                        type="button"
                        onClick={() => setMode('demo')}
                        whileHover={{ y: -4, scale: 1.03 }}
                        whileTap={{ scale: 0.98 }}
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.35 + index * 0.08 }}
                        className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-xs font-semibold text-white/75 backdrop-blur transition-colors hover:border-brand-teal-300/40 hover:bg-brand-teal-400/10 hover:text-white"
                      >
                        {label}
                      </motion.button>
                    ))}
                  </div>

                  <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:mt-10 sm:flex-row">
                    <motion.button
                      type="button"
                      onClick={() => setMode('demo')}
                      whileHover={{ y: -2, scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="inline-flex items-center justify-center gap-2 rounded-md bg-brand-teal-400 px-8 py-4 text-sm font-bold text-brand-teal-foreground shadow-brand transition-all hover:bg-brand-teal-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-teal-300"
                    >
                      <Sparkles className="h-4 w-4" />
                      Experience Customized Demo
                    </motion.button>
                    <Link
                      href="/register"
                      onClick={dismiss}
                      className="inline-flex items-center justify-center gap-2 rounded-md border border-white/20 px-8 py-4 text-sm font-semibold text-white transition-all hover:bg-white/5"
                    >
                      Start free trial
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>

                  {/* Trust strip */}
                  <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-white/50 sm:mt-10">
                    {[
                      { Icon: Shield, label: 'GDPR Compliant' },
                      { Icon: RefreshCw, label: 'Cancel anytime' },
                      { Icon: Lock, label: 'UK data residency' },
                      { Icon: Users, label: '14-day free trial' },
                    ].map(({ Icon, label }) => (
                      <div key={label} className="inline-flex items-center gap-2">
                        <Icon className="h-3.5 w-3.5 text-brand-teal-300" />
                        {label}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="mx-auto max-w-2xl rounded-2xl border border-white/10 bg-white/5 p-6 text-left shadow-2xl backdrop-blur">
                  <div className="text-center">
                    <span className="inline-flex items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-brand-teal-300">
                      <Sparkles className="h-3 w-3" />
                      Experience Customized Demo
                    </span>
                    <h1 className="mt-4 font-display text-3xl font-bold text-white sm:text-4xl">
                      Customeerflow Your Business In 30 Seconds
                    </h1>
                    <p className="mt-3 text-sm leading-relaxed text-white/65">
                      Choose your niche, top pain points and main goal. The homepage will adapt to your business without changing the default site.
                    </p>
                  </div>

                  <div className="mt-6 space-y-5">
                    <label className="block">
                      <span className="text-xs font-semibold uppercase tracking-widest text-brand-teal-300">
                        What is your business industry
                      </span>
                      <select
                        value={selectedNiche.id}
                        onChange={(event) => {
                          setSelectedNicheId(event.target.value)
                          setSelectedPainPointIds([])
                        }}
                        className="mt-2 w-full rounded-lg border border-white/15 bg-brand-forest-950 px-3 py-3 text-sm text-white focus:border-brand-teal-300 focus:outline-none focus:ring-2 focus:ring-brand-teal-300/20"
                      >
                        {ADAPTIVE_NICHES.map((niche) => (
                          <option key={niche.id} value={niche.id}>
                            {niche.label}
                          </option>
                        ))}
                      </select>
                    </label>

                    <div>
                      <span className="text-xs font-semibold uppercase tracking-widest text-brand-teal-300">
                        What are the 3 main paint points of your business?
                      </span>
                      <div className="mt-2 grid gap-2 sm:grid-cols-2">
                        {selectedNiche.painPoints.map((painPoint) => {
                          const checked = selectedPainPointIds.includes(painPoint.id)
                          const disabled = !checked && selectedPainPointIds.length >= 3
                          return (
                            <button
                              key={painPoint.id}
                              type="button"
                              disabled={disabled}
                              onClick={() => togglePainPoint(painPoint.id)}
                              className={`rounded-lg border px-3 py-2 text-left text-xs font-medium transition ${
                                checked
                                  ? 'border-brand-teal-300 bg-brand-teal-400/20 text-brand-teal-50'
                                  : 'border-white/10 bg-white/5 text-white/70 hover:border-brand-teal-300/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-40'
                              }`}
                            >
                              {painPoint.label}
                            </button>
                          )
                        })}
                      </div>
                    </div>

                    <label className="block">
                      <span className="text-xs font-semibold uppercase tracking-widest text-brand-teal-300">
                        What will you like to achieve quickly with Customerflow?
                      </span>
                      <select
                        value={goal}
                        onChange={(event) => setGoal(event.target.value as AdaptiveGoal)}
                        className="mt-2 w-full rounded-lg border border-white/15 bg-brand-forest-950 px-3 py-3 text-sm text-white focus:border-brand-teal-300 focus:outline-none focus:ring-2 focus:ring-brand-teal-300/20"
                      >
                        {GOAL_OPTIONS.map((goalOption) => (
                          <option key={goalOption.id} value={goalOption.id}>
                            {goalOption.label}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                    <button
                      type="button"
                      onClick={submitDemo}
                      className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-brand-teal-400 px-6 py-3.5 text-sm font-bold text-brand-teal-foreground shadow-brand transition-all hover:bg-brand-teal-300"
                    >
                      Show me more
                      <ArrowRight className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setMode('intro')}
                      className="rounded-md border border-white/20 px-6 py-3.5 text-sm font-semibold text-white transition-all hover:bg-white/5"
                    >
                      Back
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </main>

          {/* Scroll-down hint */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.5 }}
            className="relative z-10 flex shrink-0 justify-center pb-6 sm:pb-8"
          >
            <button
              onClick={dismiss}
              className="flex flex-col items-center gap-2 text-[11px] font-medium uppercase tracking-[0.18em] text-white/40 transition-colors hover:text-white/70"
              aria-label="Continue to site"
            >
              <span>Continue to site</span>
              <span className="flex h-8 w-5 items-start justify-center rounded-full border border-white/20 pt-1.5">
                <motion.span
                  className="h-2 w-0.5 rounded-full bg-white/50"
                  animate={{ y: [0, 6, 0] }}
                  transition={{ repeat: Infinity, duration: 1.4, ease: 'easeInOut' }}
                />
              </span>
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
