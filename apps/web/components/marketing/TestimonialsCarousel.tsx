'use client'

import { AnimatePresence, motion } from 'framer-motion'
import { ArrowUpRight, ChevronLeft, ChevronRight, Quote, Star } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { ShareReviewModal } from './ShareReviewModal'

export interface Review {
  id: string
  author_name: string
  author_role: string | null
  author_location: string | null
  rating: number
  quote: string
  metric: string | null
  is_featured: boolean
  created_at: string
}

interface TestimonialsCarouselProps {
  initialReviews?: Review[]
  autoRotateMs?: number
}

function initialsOf(name: string): string {
  const parts = name
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/**
 * The marketing-site testimonials carousel.
 *
 * - Fetches live reviews from `/api/v1/public/marketing/reviews` on mount and
 *   on a fresh submission.
 * - Falls back to `initialReviews` (passed by the SSR caller) if the public
 *   endpoint is unreachable.
 * - Auto-rotates every `autoRotateMs` (default 6s); pauses on hover.
 * - Includes a prominent "Share your story" CTA which opens the
 *   `ShareReviewModal`.
 */
export function TestimonialsCarousel({
  initialReviews = [],
  autoRotateMs = 6000,
}: TestimonialsCarouselProps) {
  const [reviews, setReviews] = useState<Review[]>(initialReviews)
  const [active, setActive] = useState(0)
  const [paused, setPaused] = useState(false)
  const [shareOpen, setShareOpen] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/public/marketing/reviews?limit=16', {
        cache: 'no-store',
      })
      if (!res.ok) return
      const data = (await res.json()) as Review[]
      if (data.length) setReviews(data)
    } catch {
      /* network errors are acceptable — we'll keep the initial set. */
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  useEffect(() => {
    if (paused || reviews.length <= 1) return
    const id = setInterval(() => setActive((a) => (a + 1) % reviews.length), autoRotateMs)
    return () => clearInterval(id)
  }, [autoRotateMs, paused, reviews.length])

  const current = reviews[active]
  const pageDots = useMemo(() => reviews.slice(0, Math.min(reviews.length, 8)), [reviews])

  if (reviews.length === 0) {
    return (
      <EmptyState onShareClick={() => setShareOpen(true)} />
    )
  }

  return (
    <div className="relative">
      <div
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
        className="grid gap-6 lg:grid-cols-12"
      >
        {/* Big featured card */}
        <div className="lg:col-span-8">
          <div className="relative overflow-hidden rounded-xl border border-border bg-card p-8 shadow-soft lg:p-10">
            <Quote className="absolute right-8 top-8 h-12 w-12 text-brand-forest-100" strokeWidth={1.2} />

            <AnimatePresence mode="wait">
              <motion.figure
                key={current.id}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -14 }}
                transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
              >
                <div className="flex items-center gap-0.5">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`h-4 w-4 ${
                        i < current.rating
                          ? 'fill-amber-400 text-amber-400'
                          : 'text-muted-foreground/30'
                      }`}
                    />
                  ))}
                </div>

                <blockquote className="mt-5 font-display text-2xl font-semibold leading-snug text-foreground lg:text-[28px]">
                  &ldquo;{current.quote}&rdquo;
                </blockquote>

                <figcaption className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-6">
                  <div className="flex items-center gap-3">
                    <span className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-forest-700 font-mono text-xs font-bold text-brand-forest-foreground">
                      {initialsOf(current.author_name)}
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        {current.author_name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {[current.author_role, current.author_location]
                          .filter(Boolean)
                          .join(' · ')}
                      </p>
                    </div>
                  </div>
                  {current.metric && (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-forest-50 px-3 py-1 text-xs font-semibold text-brand-forest-700">
                      <ArrowUpRight className="h-3 w-3" />
                      {current.metric}
                    </span>
                  )}
                </figcaption>
              </motion.figure>
            </AnimatePresence>

            {/* Controls */}
            <div className="mt-8 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                {pageDots.map((r, i) => (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => setActive(i)}
                    aria-label={`Show review ${i + 1}`}
                    className={`h-1.5 rounded-full transition-all ${
                      i === active
                        ? 'w-6 bg-brand-forest-700'
                        : 'w-1.5 bg-muted-foreground/30 hover:bg-muted-foreground/60'
                    }`}
                  />
                ))}
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setActive((a) => (a - 1 + reviews.length) % reviews.length)}
                  aria-label="Previous"
                  className="rounded-md border border-border bg-background p-2 text-foreground transition-colors hover:bg-muted/40"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setActive((a) => (a + 1) % reviews.length)}
                  aria-label="Next"
                  className="rounded-md border border-border bg-background p-2 text-foreground transition-colors hover:bg-muted/40"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Share CTA + recent stack */}
        <div className="flex flex-col gap-5 lg:col-span-4">
          <div className="rounded-xl border border-brand-forest-300 bg-brand-forest-950 p-7 text-brand-forest-foreground shadow-brand">
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.22em] text-brand-teal-300">
              You next?
            </p>
            <h3 className="mt-3 font-display text-2xl font-bold leading-snug">
              Share what changed for your business.
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-white/65">
              Two minutes, a couple of sentences, your name on the wall.
              Approved stories land on the carousel automatically.
            </p>
            <button
              type="button"
              onClick={() => setShareOpen(true)}
              className="mt-5 inline-flex items-center gap-2 rounded-md bg-brand-teal-400 px-5 py-2.5 text-sm font-semibold text-brand-teal-foreground transition-colors hover:bg-brand-teal-300"
            >
              Share your story
              <ArrowUpRight className="h-4 w-4" />
            </button>
          </div>

          <div className="grid gap-3">
            {reviews.slice(0, 3).map((r) => (
              <button
                type="button"
                key={`stack-${r.id}`}
                onClick={() => setActive(reviews.findIndex((x) => x.id === r.id))}
                className="group flex items-start gap-3 rounded-lg border border-border bg-card p-3.5 text-left transition-all hover:border-brand-forest-200 hover:bg-brand-forest-50/50"
              >
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-forest-700 font-mono text-[10px] font-bold text-brand-forest-foreground">
                  {initialsOf(r.author_name)}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-xs font-semibold text-foreground">
                      {r.author_name}
                    </p>
                    <div className="flex gap-px">
                      {[...Array(r.rating)].map((_, i) => (
                        <Star key={i} className="h-3 w-3 fill-amber-400 text-amber-400" />
                      ))}
                    </div>
                  </div>
                  <p className="mt-0.5 line-clamp-2 text-[11px] leading-snug text-muted-foreground">
                    &ldquo;{r.quote}&rdquo;
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <ShareReviewModal
        open={shareOpen}
        onClose={() => setShareOpen(false)}
        source="share_button"
        onSubmitted={refresh}
      />
    </div>
  )
}

function EmptyState({ onShareClick }: { onShareClick: () => void }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-card p-12 text-center">
      <h3 className="font-display text-xl font-bold text-foreground">
        Be the first to share your story
      </h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        We&rsquo;re onboarding our founding cohort. Tell us how the platform is
        working for your business and you&rsquo;ll appear here automatically.
      </p>
      <button
        type="button"
        onClick={onShareClick}
        className="mt-5 inline-flex items-center gap-2 rounded-md bg-brand-forest-700 px-5 py-2.5 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-colors hover:bg-brand-forest-800"
      >
        Share your story
        <ArrowUpRight className="h-4 w-4" />
      </button>
    </div>
  )
}
