'use client'

import { useEffect } from 'react'
import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Star, ExternalLink } from 'lucide-react'
import Link from 'next/link'
import { publicBooking } from '@/lib/api-client'
import { PublicBookShell } from '@/components/bookings/PublicBookShell'

export default function PublicRatePage() {
  const { tenant_slug: slug } = useParams<{ tenant_slug: string }>()

  const { data: widget } = useQuery({
    queryKey: ['public-booking-widget', slug],
    queryFn: () => publicBooking.widget(slug).then((r) => r.data),
    enabled: !!slug,
  })

  const {
    data: review,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['public-review-url', slug],
    queryFn: () => publicBooking.getReviewUrl(slug).then((r) => r.data),
    enabled: !!slug,
    retry: false,
  })

  const accent = widget?.widget_primary_color || '#166534'
  const name = widget?.tenant_name || 'Our business'
  const reviewUrl = review?.review_url as string | undefined

  useEffect(() => {
    if (reviewUrl) {
      window.location.href = reviewUrl
    }
  }, [reviewUrl])

  const errDetail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail

  return (
    <PublicBookShell tenantName={name} subtitle="Review & Comments" accent={accent}>
      <div className="text-center space-y-4 py-2">
        <Star className="w-12 h-12 mx-auto text-amber-500 fill-amber-400" />
        {isLoading && (
          <p className="text-sm text-slate-600">Opening Google review page…</p>
        )}
        {reviewUrl && (
          <>
            <p className="text-sm text-slate-600">Redirecting you to Google to leave a review.</p>
            <a
              href={reviewUrl}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-semibold"
              style={{ backgroundColor: accent }}
            >
              <ExternalLink className="w-4 h-4" />
              Leave a Google review
            </a>
          </>
        )}
        {isError && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-left text-sm text-slate-700">
            <p className="font-semibold text-slate-900 mb-1">Google Business not ready</p>
            <p>{errDetail || 'This business must connect Google Business Profile in CustomerFlow before review QR works.'}</p>
          </div>
        )}
        <Link href={`/book/${slug}`} className="text-sm text-emerald-800 hover:underline block">
          ← Back to booking
        </Link>
      </div>
    </PublicBookShell>
  )
}
