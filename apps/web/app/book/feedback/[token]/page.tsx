'use client'

import { useParams } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { Star } from 'lucide-react'
import { toast } from 'sonner'
import { publicFeedback } from '@/lib/api-client'
import { PublicBookShell } from '@/components/bookings/PublicBookShell'

export default function FeedbackSubmitPage() {
  const { token } = useParams<{ token: string }>()
  const [rating, setRating] = useState(0)
  const [text, setText] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['public-feedback', token],
    queryFn: () => publicFeedback.get(token!).then((r) => r.data),
    enabled: !!token,
  })

  const submit = useMutation({
    mutationFn: () => publicFeedback.submit(token!, { rating, feedback_text: text || undefined }),
    onSuccess: () => toast.success('Thank you for your feedback'),
    onError: () => toast.error('Could not submit feedback'),
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin w-10 h-10 border-4 border-emerald-700 border-t-transparent rounded-full" />
      </div>
    )
  }

  const done = data?.already_submitted

  return (
    <PublicBookShell
      tenantName={data?.tenant_name ?? 'Your provider'}
      subtitle={done ? 'Feedback received' : `Hi ${data?.customer_name ?? 'there'}`}
    >
      {done ? (
        <p className="text-sm text-slate-600 text-center">
          You already rated this visit
          {data?.service_rating ? ` (${data.service_rating}/5)` : ''}. Thank you.
        </p>
      ) : (
        <div className="space-y-5">
          <p className="text-sm text-slate-600 text-center">
            Appointment on {data?.booking_date ? new Date(data.booking_date).toLocaleDateString('en-GB') : '—'}
          </p>
          <div className="flex justify-center gap-2">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                onClick={() => setRating(n)}
                className="p-1"
                aria-label={`Rate ${n} stars`}
              >
                <Star
                  className={`w-9 h-9 ${n <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-300'}`}
                />
              </button>
            ))}
          </div>
          <textarea
            className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm min-h-[100px]"
            placeholder="Tell us how it went (optional)"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <button
            type="button"
            disabled={rating < 1 || submit.isPending}
            onClick={() => submit.mutate()}
            className="w-full py-3 rounded-xl bg-emerald-800 text-white font-semibold text-sm disabled:opacity-50"
          >
            {submit.isPending ? 'Sending…' : 'Submit feedback'}
          </button>
        </div>
      )}
    </PublicBookShell>
  )
}
