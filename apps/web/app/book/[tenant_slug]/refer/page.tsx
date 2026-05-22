'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Gift } from 'lucide-react'
import { publicBooking } from '@/lib/api-client'
import { PublicBookShell } from '@/components/bookings/PublicBookShell'

export default function PublicReferPage() {
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
      subtitle="Refer a friend"
      accent={accent}
    >
      <div className="text-center space-y-4">
        <Gift className="w-12 h-12 mx-auto text-emerald-700" />
        <h2 className="text-xl font-bold text-slate-900">Share {name} with someone you trust</h2>
        <p className="text-sm text-slate-600 leading-relaxed">
          Referral rewards are managed by your provider. Ask them for your personal referral link after your
          appointment, or book below and mention who referred you in the notes.
        </p>
        <Link
          href={`/book/${slug}`}
          className="inline-block w-full py-3 rounded-xl text-white font-semibold text-sm"
          style={{ backgroundColor: accent }}
        >
          Book an appointment
        </Link>
      </div>
    </PublicBookShell>
  )
}
