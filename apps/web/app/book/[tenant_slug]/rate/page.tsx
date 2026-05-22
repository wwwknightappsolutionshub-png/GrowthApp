'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Star } from 'lucide-react'
import { publicBooking } from '@/lib/api-client'
import { PublicBookShell } from '@/components/bookings/PublicBookShell'

export default function PublicRateInfoPage() {
  const { tenant_slug: slug } = useParams<{ tenant_slug: string }>()
  const { data: widget } = useQuery({
    queryKey: ['public-booking-widget', slug],
    queryFn: () => publicBooking.widget(slug).then((r) => r.data),
    enabled: !!slug,
  })

  const accent = widget?.widget_primary_color || '#166534'
  const name = widget?.tenant_name || 'Our business'

  return (
    <PublicBookShell
      tenantName={name}
      subtitle="Rate your experience"
      accent={accent}
    >
      <div className="text-center space-y-4">
        <Star className="w-12 h-12 mx-auto text-amber-500 fill-amber-400" />
        <h2 className="text-xl font-bold text-slate-900">Feedback after your visit</h2>
        <p className="text-sm text-slate-600 leading-relaxed">
          {name} sends a private rating link by email or in-app notification once your appointment is marked
          completed. This page is for QR signage — customers cannot rate from here without their personal link.
        </p>
        <Link
          href={`/book/${slug}`}
          className="inline-block w-full py-3 rounded-xl text-white font-semibold text-sm"
          style={{ backgroundColor: accent }}
        >
          Book a new appointment
        </Link>
      </div>
    </PublicBookShell>
  )
}
