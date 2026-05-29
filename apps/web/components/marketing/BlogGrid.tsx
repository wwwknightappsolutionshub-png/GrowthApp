'use client'

/**
 * BlogGrid — 4-column card grid with infinite scroll and click-to-modal post viewer.
 * Fetches from /api/v1/public/blog?page=N&per_page=8 (latest first).
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Clock, Tag, ArrowRight, ChevronLeft } from 'lucide-react'
import { sanitizeHtml } from '@/lib/sanitize'

export interface BlogPostItem {
  id: string
  title: string
  slug: string
  excerpt: string | null
  content: string | null
  category: string | null
  image_url: string | null
  author_name: string | null
  read_minutes: number | null
  published_at: string | null
}

interface Props {
  initialPosts: BlogPostItem[]
  initialTotal: number
}

const CATEGORY_COLORS: Record<string, string> = {
  Trades: 'bg-amber-100 text-amber-700',
  Strategy: 'bg-blue-100 text-blue-700',
  Reviews: 'bg-green-100 text-green-700',
  Bookings: 'bg-purple-100 text-purple-700',
  'Lead Generation': 'bg-orange-100 text-orange-700',
  Hospitality: 'bg-pink-100 text-pink-700',
  Compliance: 'bg-red-100 text-red-700',
  Guide: 'bg-gray-100 text-gray-700',
}

function categoryClass(cat: string | null) {
  return CATEGORY_COLORS[cat ?? 'Guide'] ?? 'bg-gray-100 text-gray-700'
}

function formatDate(iso: string | null) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function BlogGrid({ initialPosts, initialTotal }: Props) {
  const [posts, setPosts] = useState<BlogPostItem[]>(initialPosts)
  const [total, setTotal] = useState(initialTotal)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<BlogPostItem | null>(null)
  const sentinelRef = useRef<HTMLDivElement>(null)

  const loadMore = useCallback(async () => {
    if (loading || posts.length >= total) return
    setLoading(true)
    try {
      const nextPage = page + 1
      const res = await fetch(`/api/v1/public/blog?page=${nextPage}&per_page=8`)
      if (res.ok) {
        const data = await res.json()
        setPosts((prev) => {
          const ids = new Set(prev.map((p) => p.id))
          const fresh = (data.items as BlogPostItem[]).filter((p) => !ids.has(p.id))
          return [...prev, ...fresh]
        })
        setTotal(data.total)
        setPage(nextPage)
      }
    } finally {
      setLoading(false)
    }
  }, [loading, posts.length, total, page])

  // IntersectionObserver for infinite scroll
  useEffect(() => {
    const el = sentinelRef.current
    if (!el) return
    const obs = new IntersectionObserver(
      (entries) => { if (entries[0].isIntersecting) loadMore() },
      { rootMargin: '200px' },
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [loadMore])

  // Close modal on Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setSelected(null)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])

  // Prevent body scroll when modal open
  useEffect(() => {
    document.body.style.overflow = selected ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [selected])

  return (
    <>
      {/* Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {posts.map((post, i) => (
          <motion.article
            key={post.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.05, 0.4), duration: 0.4 }}
            onClick={() => setSelected(post)}
            className="group flex cursor-pointer flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-all hover:-translate-y-1 hover:shadow-elevated"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setSelected(post) }}
            aria-label={`Read: ${post.title}`}
          >
            {/* Image */}
            <div className="relative aspect-[16/9] overflow-hidden bg-muted">
              {post.image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={post.image_url}
                  alt={post.title}
                  className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                  loading="lazy"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center bg-brand-forest-100 text-brand-forest-400 text-4xl font-bold">
                  CF
                </div>
              )}
              <span
                className={`absolute left-3 top-3 rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${categoryClass(post.category)}`}
              >
                {post.category ?? 'Guide'}
              </span>
            </div>

            {/* Body */}
            <div className="flex flex-1 flex-col p-5">
              <h3 className="font-display text-base font-bold leading-snug text-foreground transition-colors group-hover:text-brand-forest-700 line-clamp-2">
                {post.title}
              </h3>
              {post.excerpt && (
                <p className="mt-2 text-xs leading-relaxed text-muted-foreground line-clamp-3">
                  {post.excerpt}
                </p>
              )}
              <div className="mt-auto flex items-center justify-between pt-4 text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {post.read_minutes ?? 5} min read
                </span>
                <span>{formatDate(post.published_at)}</span>
              </div>
            </div>
          </motion.article>
        ))}
      </div>

      {/* Loading & sentinel */}
      {posts.length < total && (
        <div ref={sentinelRef} className="flex justify-center py-10">
          {loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-forest-700 border-t-transparent" />
              Loading more posts…
            </div>
          )}
        </div>
      )}

      {/* Post Modal */}
      <AnimatePresence>
        {selected && (
          <motion.div
            key="blog-modal-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 z-[9998] flex items-start justify-center overflow-y-auto bg-black/60 px-4 py-10 backdrop-blur-sm"
            onClick={(e) => { if (e.target === e.currentTarget) setSelected(null) }}
          >
            <motion.div
              key="blog-modal"
              initial={{ opacity: 0, y: 32, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 16, scale: 0.98 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="relative w-full max-w-3xl overflow-hidden rounded-2xl bg-card shadow-2xl"
              role="dialog"
              aria-modal="true"
              aria-label={selected.title}
            >
              {/* Close button */}
              <button
                onClick={() => setSelected(null)}
                className="absolute right-4 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-black/40 text-white backdrop-blur-sm transition-colors hover:bg-black/60"
                aria-label="Close post"
              >
                <X className="h-4 w-4" />
              </button>

              {/* Hero image */}
              {selected.image_url && (
                <div className="relative aspect-[21/9] overflow-hidden">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={selected.image_url}
                    alt={selected.title}
                    className="h-full w-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-card/80 to-transparent" />
                </div>
              )}

              {/* Content */}
              <div className="p-6 sm:p-8">
                <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                  <span className={`rounded-full px-2.5 py-0.5 font-semibold uppercase tracking-wide ${categoryClass(selected.category)}`}>
                    {selected.category ?? 'Guide'}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {selected.read_minutes ?? 5} min read
                  </span>
                  {selected.published_at && (
                    <span>{formatDate(selected.published_at)}</span>
                  )}
                  {selected.author_name && (
                    <span>by {selected.author_name}</span>
                  )}
                </div>

                <h1 className="mt-4 font-display text-2xl font-bold leading-tight text-foreground sm:text-3xl">
                  {selected.title}
                </h1>

                {selected.excerpt && (
                  <p className="mt-3 text-base leading-relaxed text-muted-foreground">
                    {selected.excerpt}
                  </p>
                )}

                {selected.content ? (
                  <div
                    className="prose prose-sm mt-6 max-w-none prose-headings:font-display prose-headings:text-foreground prose-p:text-foreground/80 prose-li:text-foreground/80 prose-strong:text-foreground prose-a:text-brand-teal-500"
                    dangerouslySetInnerHTML={{ __html: sanitizeHtml(selected.content) }}
                  />
                ) : (
                  <p className="mt-6 text-sm text-muted-foreground italic">Full post content coming soon.</p>
                )}

                <div className="mt-8 flex items-center gap-4 border-t border-border pt-6">
                  <button
                    onClick={() => setSelected(null)}
                    className="flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Back to blog
                  </button>
                  <a
                    href="/register"
                    className="ml-auto inline-flex items-center gap-2 rounded-md bg-brand-forest-700 px-5 py-2.5 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800"
                  >
                    Start free trial
                    <ArrowRight className="h-3.5 w-3.5" />
                  </a>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
