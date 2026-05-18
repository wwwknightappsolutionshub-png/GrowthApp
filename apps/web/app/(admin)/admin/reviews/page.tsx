'use client'

import { useEffect, useState } from 'react'
import {
  CheckCircle2,
  Copy,
  ExternalLink,
  EyeOff,
  Globe,
  Loader2,
  Pin,
  Send,
  Star,
  Trash2,
} from 'lucide-react'
import { toast } from 'sonner'

import { admin } from '@/lib/api-client'

interface AdminReview {
  id: string
  author_name: string
  author_role: string | null
  author_location: string | null
  author_email: string | null
  author_company: string | null
  rating: number
  quote: string
  quote_raw: string
  metric: string | null
  status: string
  is_featured: boolean
  is_carousel: boolean
  sanitised: boolean
  gmb_status: string
  gmb_pushed_at: string | null
  gmb_url: string | null
  trustpilot_status: string
  trustpilot_pushed_at: string | null
  trustpilot_url: string | null
  capture_source: string
  created_at: string
}

type StatusFilter = 'all' | 'approved' | 'pending' | 'hidden' | 'rejected'

const FILTERS: { key: StatusFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'approved', label: 'On the site' },
  { key: 'pending', label: 'Needs review' },
  { key: 'hidden', label: 'Hidden' },
  { key: 'rejected', label: 'Rejected' },
]

export default function AdminReviewsPage() {
  const [reviews, setReviews] = useState<AdminReview[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<StatusFilter>('all')

  async function refresh(opts?: { quiet?: boolean }) {
    if (!opts?.quiet) setLoading(true)
    try {
      const status_filter = filter === 'all' ? undefined : filter
      const res = await admin.listMarketingReviews(status_filter)
      setReviews(res.data as AdminReview[])
    } catch (err) {
      console.error(err)
      toast.error('Failed to load reviews')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter])

  async function moderate(
    id: string,
    body: Parameters<typeof admin.moderateReview>[1],
  ) {
    await admin.moderateReview(id, body)
    void refresh({ quiet: true })
  }

  async function push(id: string, channel: 'gmb' | 'trustpilot') {
    try {
      await admin.pushReview(id, { channel })
      toast.success(`Queued for ${channel === 'gmb' ? 'Google Business Profile' : 'Trustpilot'}`)
      void refresh({ quiet: true })
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e.response?.data?.detail || 'Could not queue the push')
    }
  }

  return (
    <div>
      <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Reviews moderation</h1>
          <p className="mt-1 text-sm text-gray-400">
            Visitor stories captured via the marketing site. Approved 4-5★ reviews
            auto-publish to the carousel &mdash; everything else queues here.
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5 rounded-md border border-gray-800 bg-gray-900/60 p-1">
          {FILTERS.map((f) => (
            <button
              type="button"
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                filter === f.key
                  ? 'bg-amber-500/15 text-amber-200'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </header>

      {loading && reviews.length === 0 ? (
        <p className="text-sm text-gray-400">Loading…</p>
      ) : reviews.length === 0 ? (
        <p className="rounded-lg border border-dashed border-gray-800 bg-gray-900/40 p-10 text-center text-sm text-gray-500">
          No reviews in this state.
        </p>
      ) : (
        <ul className="space-y-3">
          {reviews.map((r) => (
            <ReviewCard
              key={r.id}
              review={r}
              onModerate={moderate}
              onPush={push}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

function ReviewCard({
  review,
  onModerate,
  onPush,
}: {
  review: AdminReview
  onModerate: (id: string, body: Parameters<typeof admin.moderateReview>[1]) => Promise<void>
  onPush: (id: string, channel: 'gmb' | 'trustpilot') => Promise<void>
}) {
  const [busy, setBusy] = useState<string | null>(null)

  async function call(action: string, fn: () => Promise<void>) {
    setBusy(action)
    try {
      await fn()
    } finally {
      setBusy(null)
    }
  }

  function copyToClipboard() {
    const block = [
      `${review.author_name}${review.author_role ? ` · ${review.author_role}` : ''}${
        review.author_location ? ` · ${review.author_location}` : ''
      }`,
      `Rating: ${'★'.repeat(review.rating)}`,
      '',
      review.quote,
    ].join('\n')
    void navigator.clipboard.writeText(block)
    toast.success('Review copied to clipboard')
  }

  return (
    <li className="rounded-lg border border-gray-800 bg-gray-900/60 p-5 transition-colors hover:bg-gray-900/80">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-500/15 font-mono text-xs font-bold text-amber-300">
            {review.author_name.slice(0, 2).toUpperCase()}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white">{review.author_name}</p>
            <p className="text-xs text-gray-500">
              {[review.author_role, review.author_location, review.author_email]
                .filter(Boolean)
                .join(' · ')}
            </p>
            <p className="mt-0.5 font-mono text-[10px] text-gray-600">
              {new Date(review.created_at).toLocaleString('en-GB')} · {review.capture_source}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex gap-px">
            {[...Array(review.rating)].map((_, i) => (
              <Star key={i} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
            ))}
          </div>
          <StatusPill status={review.status} />
          {review.is_featured && <Pill tone="brand">Featured</Pill>}
          {review.sanitised && <Pill tone="warn">Sanitised</Pill>}
        </div>
      </div>

      <blockquote className="mt-4 rounded-md border border-gray-800 bg-gray-950/50 p-4 text-sm leading-relaxed text-gray-200">
        &ldquo;{review.quote}&rdquo;
      </blockquote>

      {review.sanitised && review.quote !== review.quote_raw && (
        <details className="mt-2 rounded-md border border-gray-800 bg-gray-950/30 px-3 py-2 text-[11px] text-gray-500">
          <summary className="cursor-pointer select-none font-semibold uppercase tracking-wider">
            Original text (before sanitisation)
          </summary>
          <p className="mt-2 whitespace-pre-wrap text-gray-400">{review.quote_raw}</p>
        </details>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {review.status !== 'approved' && (
          <Action
            icon={CheckCircle2}
            label="Approve & show"
            color="emerald"
            disabled={busy !== null}
            loading={busy === 'approve'}
            onClick={() =>
              call('approve', async () =>
                onModerate(review.id, { status: 'approved', is_carousel: true }),
              )
            }
          />
        )}
        {review.status === 'approved' && (
          <Action
            icon={EyeOff}
            label="Hide"
            color="slate"
            disabled={busy !== null}
            loading={busy === 'hide'}
            onClick={() =>
              call('hide', async () => onModerate(review.id, { status: 'hidden' }))
            }
          />
        )}
        <Action
          icon={Pin}
          label={review.is_featured ? 'Unfeature' : 'Feature'}
          color="brand"
          disabled={busy !== null}
          loading={busy === 'feature'}
          onClick={() =>
            call('feature', async () =>
              onModerate(review.id, { is_featured: !review.is_featured }),
            )
          }
        />
        <Action
          icon={Trash2}
          label="Reject"
          color="rose"
          disabled={busy !== null}
          loading={busy === 'reject'}
          onClick={() =>
            call('reject', async () =>
              onModerate(review.id, { status: 'rejected', is_carousel: false }),
            )
          }
        />
        <span className="mx-2 hidden h-5 border-l border-gray-700 sm:inline-block" />
        <Action
          icon={Globe}
          label={`Push to Google · ${review.gmb_status}`}
          color="brand"
          disabled={busy !== null || review.gmb_status === 'pushed'}
          loading={busy === 'gmb'}
          onClick={() => call('gmb', () => onPush(review.id, 'gmb'))}
        />
        <Action
          icon={Send}
          label={`Push to Trustpilot · ${review.trustpilot_status}`}
          color="brand"
          disabled={busy !== null || review.trustpilot_status === 'pushed'}
          loading={busy === 'trustpilot'}
          onClick={() => call('trustpilot', () => onPush(review.id, 'trustpilot'))}
        />
        <Action
          icon={Copy}
          label="Copy text"
          color="slate"
          onClick={copyToClipboard}
        />
      </div>

      {(review.gmb_url || review.trustpilot_url) && (
        <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px] text-gray-500">
          {review.gmb_url && (
            <a
              href={review.gmb_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-gray-400 hover:text-white"
            >
              GMB <ExternalLink className="h-3 w-3" />
            </a>
          )}
          {review.trustpilot_url && (
            <a
              href={review.trustpilot_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-gray-400 hover:text-white"
            >
              Trustpilot <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      )}
    </li>
  )
}

interface ActionProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  color: 'emerald' | 'rose' | 'brand' | 'slate'
  onClick: () => void | Promise<void>
  disabled?: boolean
  loading?: boolean
}

function Action({ icon: Icon, label, color, onClick, disabled, loading }: ActionProps) {
  const colors: Record<ActionProps['color'], string> = {
    emerald: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20',
    rose: 'border-rose-500/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20',
    brand: 'border-amber-500/30 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20',
    slate: 'border-gray-700 bg-gray-800/60 text-gray-300 hover:bg-gray-800',
  }
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${colors[color]}`}
    >
      {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Icon className="h-3 w-3" />}
      {label}
    </button>
  )
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, string> = {
    approved: 'bg-emerald-500/15 text-emerald-300',
    pending: 'bg-amber-500/15 text-amber-300',
    hidden: 'bg-gray-700/50 text-gray-300',
    rejected: 'bg-rose-500/15 text-rose-300',
  }
  return (
    <span
      className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider ${
        map[status] || 'bg-gray-700/40 text-gray-300'
      }`}
    >
      {status}
    </span>
  )
}

function Pill({
  children,
  tone,
}: {
  children: React.ReactNode
  tone: 'brand' | 'warn'
}) {
  const cls =
    tone === 'brand'
      ? 'bg-amber-500/15 text-amber-300'
      : 'bg-yellow-500/15 text-yellow-300'
  return (
    <span
      className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider ${cls}`}
    >
      {children}
    </span>
  )
}
