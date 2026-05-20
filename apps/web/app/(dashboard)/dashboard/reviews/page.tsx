'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { reputation, integrations } from '@/lib/api-client'
import { Star } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { toast } from 'sonner'

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`w-4 h-4 ${i <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-200'}`}
        />
      ))}
    </div>
  )
}

function googleStarsToNumber(star: string | null | undefined): number {
  const map: Record<string, number> = {
    ONE: 1,
    TWO: 2,
    THREE: 3,
    FOUR: 4,
    FIVE: 5,
  }
  if (!star) return 0
  return map[star] ?? Number.parseInt(star, 10) || 0
}

type Tab = 'in_app' | 'google'

export default function ReviewsPage() {
  const [tab, setTab] = useState<Tab>('in_app')
  const [replyDrafts, setReplyDrafts] = useState<Record<string, string>>({})
  const qc = useQueryClient()

  const { data: dashboard } = useQuery({
    queryKey: ['reputation-dashboard'],
    queryFn: () => reputation.dashboard().then((r) => r.data),
  })
  const { data: reviewsData } = useQuery({
    queryKey: ['reviews'],
    queryFn: () => reputation.reviews().then((r) => r.data),
  })
  const googleStatus = useQuery({
    queryKey: ['integrations', 'google', 'status'],
    queryFn: () => integrations.googleStatus().then((r) => r.data),
  })
  const { data: googleReviews, isLoading: googleLoading } = useQuery({
    queryKey: ['google-reviews'],
    queryFn: () => integrations.googleReviews().then((r) => r.data),
    enabled: tab === 'google' && !!googleStatus.data?.connected,
  })

  const syncGoogle = useMutation({
    mutationFn: () => integrations.googleSync(),
    onSuccess: () => {
      toast.success('Google reviews synced')
      qc.invalidateQueries({ queryKey: ['google-reviews'] })
    },
    onError: () => toast.error('Could not sync Google reviews'),
  })

  const replyGoogle = useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: string }) =>
      integrations.googleReply(id, comment),
    onSuccess: () => {
      toast.success('Reply posted to Google')
      qc.invalidateQueries({ queryKey: ['google-reviews'] })
    },
    onError: () => toast.error('Could not post reply'),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Reviews & Reputation</h1>
        <p className="text-muted-foreground text-sm">Monitor in-app feedback and Google Business reviews</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Avg Rating', value: `${dashboard?.avg_rating ?? '—'} ⭐` },
          { label: 'Total Reviews', value: dashboard?.total_reviews ?? 0 },
          { label: '5-Star Reviews', value: dashboard?.five_star_count ?? 0 },
          { label: 'Sent to Google', value: dashboard?.routed_to_google ?? 0 },
        ].map((s) => (
          <div
            key={s.label}
            className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-5 text-center shadow-sm"
          >
            <p className="text-2xl font-bold text-white">{s.value}</p>
            <p className="text-xs text-brand-teal-100/75 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="flex gap-2 border-b border-brand-forest-800">
        <button
          type="button"
          onClick={() => setTab('in_app')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
            tab === 'in_app'
              ? 'border-brand-teal-400 text-white'
              : 'border-transparent text-brand-teal-100/60 hover:text-white'
          }`}
        >
          In-app reviews
        </button>
        <button
          type="button"
          onClick={() => setTab('google')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
            tab === 'google'
              ? 'border-brand-teal-400 text-white'
              : 'border-transparent text-brand-teal-100/60 hover:text-white'
          }`}
        >
          Google Business
        </button>
      </div>

      {tab === 'in_app' && (
        <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 shadow-sm">
          <div className="p-6 border-b border-brand-forest-800">
            <h2 className="font-semibold text-white">All Reviews</h2>
          </div>
          <div className="divide-y divide-brand-forest-800">
            {reviewsData?.items?.length === 0 && (
              <div className="p-8 text-center text-brand-teal-100/70 text-sm">
                No reviews yet. Mark a job as complete to trigger the first review request.
              </div>
            )}
            {reviewsData?.items?.map((review: {
              id: string
              rating: number
              routed_to_google: boolean
              is_public: boolean
              feedback?: string
              created_at: string
            }) => (
              <div key={review.id} className="p-5">
                <div className="flex items-start justify-between">
                  <StarRating rating={review.rating} />
                  <div className="flex gap-2">
                    {review.routed_to_google && (
                      <span className="text-xs bg-brand-teal-400/20 text-brand-teal-100 ring-1 ring-brand-teal-300/30 px-2 py-0.5 rounded-full">
                        Sent to Google
                      </span>
                    )}
                    {!review.is_public && (
                      <span className="text-xs bg-orange-400/20 text-orange-100 ring-1 ring-orange-300/30 px-2 py-0.5 rounded-full">
                        Private feedback
                      </span>
                    )}
                  </div>
                </div>
                {review.feedback && <p className="mt-2 text-sm text-brand-teal-50/90">{review.feedback}</p>}
                <p className="mt-2 text-xs text-brand-teal-100/60">{formatDate(review.created_at)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'google' && (
        <div className="space-y-4">
          {!googleStatus.data?.connected && (
            <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-8 text-center text-sm text-brand-teal-100/70">
              Connect Google Business Profile in{' '}
              <Link href="/dashboard/integrations" className="text-brand-teal-400 hover:underline">
                Integrations
              </Link>{' '}
              to view and reply to Google reviews here.
            </div>
          )}
          {googleStatus.data?.connected && (
            <>
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => syncGoogle.mutate()}
                  disabled={syncGoogle.isPending}
                  className="text-sm rounded-lg border border-brand-forest-600 px-3 py-1.5 text-white hover:bg-brand-forest-800 disabled:opacity-50"
                >
                  {syncGoogle.isPending ? 'Syncing…' : 'Sync from Google'}
                </button>
              </div>
              <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 shadow-sm divide-y divide-brand-forest-800">
                {googleLoading && (
                  <p className="p-8 text-center text-sm text-brand-teal-100/70">Loading Google reviews…</p>
                )}
                {!googleLoading && (!googleReviews || googleReviews.length === 0) && (
                  <p className="p-8 text-center text-sm text-brand-teal-100/70">
                    No Google reviews cached yet. Click sync to pull the latest.
                  </p>
                )}
                {googleReviews?.map(
                  (review: {
                    id: string
                    reviewer_display_name: string | null
                    star_rating: string | null
                    comment: string | null
                    reply_comment: string | null
                    review_created_at: string | null
                  }) => (
                    <div key={review.id} className="p-5 space-y-3">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="font-medium text-white">
                            {review.reviewer_display_name || 'Google user'}
                          </p>
                          <StarRating rating={googleStarsToNumber(review.star_rating)} />
                        </div>
                        {review.review_created_at && (
                          <p className="text-xs text-brand-teal-100/60 shrink-0">
                            {formatDate(review.review_created_at)}
                          </p>
                        )}
                      </div>
                      {review.comment && (
                        <p className="text-sm text-brand-teal-50/90">{review.comment}</p>
                      )}
                      {review.reply_comment ? (
                        <p className="text-sm text-brand-teal-100/80 border-l-2 border-brand-teal-500/50 pl-3">
                          Your reply: {review.reply_comment}
                        </p>
                      ) : (
                        <div className="space-y-2">
                          <textarea
                            value={replyDrafts[review.id] ?? ''}
                            onChange={(e) =>
                              setReplyDrafts((d) => ({ ...d, [review.id]: e.target.value }))
                            }
                            placeholder="Write a public reply on Google…"
                            rows={2}
                            className="w-full rounded-lg border border-brand-forest-600 bg-brand-forest-900 px-3 py-2 text-sm text-white placeholder:text-brand-teal-100/40"
                          />
                          <button
                            type="button"
                            disabled={
                              !replyDrafts[review.id]?.trim() ||
                              replyGoogle.isPending
                            }
                            onClick={() =>
                              replyGoogle.mutate({
                                id: review.id,
                                comment: replyDrafts[review.id] ?? '',
                              })
                            }
                            className="text-sm rounded-lg bg-brand-teal-500 px-3 py-1.5 font-medium text-brand-forest-950 disabled:opacity-50"
                          >
                            Post reply
                          </button>
                        </div>
                      )}
                    </div>
                  ),
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
