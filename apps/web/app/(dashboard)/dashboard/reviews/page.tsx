'use client'

import { useQuery } from '@tanstack/react-query'
import { reputation } from '@/lib/api-client'
import { Star } from 'lucide-react'
import { formatDate } from '@/lib/utils'

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map(i => (
        <Star key={i} className={`w-4 h-4 ${i <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-200'}`} />
      ))}
    </div>
  )
}

export default function ReviewsPage() {
  const { data: dashboard } = useQuery({ queryKey: ['reputation-dashboard'], queryFn: () => reputation.dashboard().then(r => r.data) })
  const { data: reviewsData } = useQuery({ queryKey: ['reviews'], queryFn: () => reputation.reviews().then(r => r.data) })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Reviews & Reputation</h1>
        <p className="text-muted-foreground text-sm">Monitor and grow your online reputation</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Avg Rating', value: `${dashboard?.avg_rating ?? '—'} ⭐` },
          { label: 'Total Reviews', value: dashboard?.total_reviews ?? 0 },
          { label: '5-Star Reviews', value: dashboard?.five_star_count ?? 0 },
          { label: 'Sent to Google', value: dashboard?.routed_to_google ?? 0 },
        ].map(s => (
          <div key={s.label} className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-5 text-center shadow-sm">
            <p className="text-2xl font-bold text-white">{s.value}</p>
            <p className="text-xs text-brand-teal-100/75 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Reviews list */}
      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 shadow-sm">
        <div className="p-6 border-b border-brand-forest-800">
          <h2 className="font-semibold text-white">All Reviews</h2>
        </div>
        <div className="divide-y divide-brand-forest-800">
          {reviewsData?.items?.length === 0 && (
            <div className="p-8 text-center text-brand-teal-100/70 text-sm">No reviews yet. Mark a job as complete to trigger the first review request.</div>
          )}
          {reviewsData?.items?.map((review: any) => (
            <div key={review.id} className="p-5">
              <div className="flex items-start justify-between">
                <StarRating rating={review.rating} />
                <div className="flex gap-2">
                  {review.routed_to_google && <span className="text-xs bg-brand-teal-400/20 text-brand-teal-100 ring-1 ring-brand-teal-300/30 px-2 py-0.5 rounded-full">Sent to Google</span>}
                  {!review.is_public && <span className="text-xs bg-orange-400/20 text-orange-100 ring-1 ring-orange-300/30 px-2 py-0.5 rounded-full">Private feedback</span>}
                </div>
              </div>
              {review.feedback && <p className="mt-2 text-sm text-brand-teal-50/90">{review.feedback}</p>}
              <p className="mt-2 text-xs text-brand-teal-100/60">{formatDate(review.created_at)}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
