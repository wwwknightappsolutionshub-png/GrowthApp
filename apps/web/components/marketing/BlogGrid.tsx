'use client'

/**
 * BlogGrid — card grid with infinite scroll. Each card links to /blog/[slug].
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Clock } from 'lucide-react'
import type { BlogPost } from '@/lib/blog'

interface Props {
  initialPosts: BlogPost[]
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
  const [posts, setPosts] = useState<BlogPost[]>(initialPosts)
  const [total, setTotal] = useState(initialTotal)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
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
          const fresh = (data.items as BlogPost[]).filter((p) => !ids.has(p.id))
          return [...prev, ...fresh]
        })
        setTotal(data.total)
        setPage(nextPage)
      }
    } finally {
      setLoading(false)
    }
  }, [loading, posts.length, total, page])

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

  return (
    <>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {posts.map((post, i) => (
          <motion.article
            key={post.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.05, 0.4), duration: 0.4 }}
          >
            <Link
              href={`/blog/${post.slug}`}
              className="group flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-all hover:-translate-y-1 hover:shadow-elevated"
              aria-label={`Read: ${post.title}`}
            >
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
                  <div className="flex h-full w-full items-center justify-center bg-brand-forest-100 text-4xl font-bold text-brand-forest-400">
                    CF
                  </div>
                )}
                <span
                  className={`absolute left-3 top-3 rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${categoryClass(post.category)}`}
                >
                  {post.category ?? 'Guide'}
                </span>
              </div>

              <div className="flex flex-1 flex-col p-5">
                <h3 className="line-clamp-2 font-display text-base font-bold leading-snug text-foreground transition-colors group-hover:text-brand-forest-700">
                  {post.title}
                </h3>
                {post.excerpt && (
                  <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-muted-foreground">
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
            </Link>
          </motion.article>
        ))}
      </div>

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
    </>
  )
}

// Re-export for pages that still import BlogPostItem
export type { BlogPost as BlogPostItem } from '@/lib/blog'
