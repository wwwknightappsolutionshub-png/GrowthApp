'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Star } from 'lucide-react'

export default function ReviewPage() {
  const { tenantSlug, token } = useParams<{ tenantSlug: string; token: string }>()

  const [loading, setLoading] = useState(true)
  const [requestData, setRequestData] = useState<{ business_name: string; status: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [rating, setRating] = useState(0)
  const [hovered, setHovered] = useState(0)
  const [feedback, setFeedback] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ routed_to_google: boolean; google_review_url?: string; message: string } | null>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

  useEffect(() => {
    fetch(`${API_URL}/api/v1/public/review/${token}`)
      .then(r => r.json())
      .then(d => {
        setRequestData(d)
        setLoading(false)
      })
      .catch(() => {
        setError('This review link is invalid or has expired.')
        setLoading(false)
      })
  }, [token, API_URL])

  const handleSubmit = async () => {
    if (!rating) return
    setSubmitting(true)
    try {
      const res = await fetch(`${API_URL}/api/v1/public/review/${token}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, feedback: feedback || null }),
      })
      const data = await res.json()
      setResult(data)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
          <div className="text-4xl mb-4">😕</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Link not valid</h2>
          <p className="text-gray-500 text-sm">{error}</p>
        </div>
      </div>
    )
  }

  if (result) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
          <div className="text-5xl mb-4">{result.routed_to_google ? '🌟' : '🙏'}</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">
            {result.routed_to_google ? 'Brilliant — thank you!' : 'Thank you for your feedback'}
          </h2>
          <p className="text-gray-500 mb-6">{result.message}</p>
          {result.routed_to_google && result.google_review_url && (
            <a
              href={result.google_review_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold text-sm hover:bg-blue-700 shadow-sm"
            >
              Leave a Google Review
            </a>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">How did we do?</h2>
          <p className="text-gray-500 text-sm">
            {requestData?.business_name
              ? `Help ${requestData.business_name} improve by sharing your experience`
              : 'Share your experience to help us improve'}
          </p>
        </div>

        {/* Star rating */}
        <div className="flex justify-center gap-3 mb-6">
          {[1, 2, 3, 4, 5].map(star => (
            <button
              key={star}
              onClick={() => setRating(star)}
              onMouseEnter={() => setHovered(star)}
              onMouseLeave={() => setHovered(0)}
              className="transition-transform hover:scale-110"
            >
              <Star
                className={`w-10 h-10 transition-colors ${
                  star <= (hovered || rating)
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'text-gray-200'
                }`}
              />
            </button>
          ))}
        </div>

        {rating > 0 && (
          <p className="text-center text-sm font-medium text-gray-700 mb-5">
            {rating === 5 ? 'Excellent! 🎉' : rating === 4 ? 'Great 😊' : rating === 3 ? 'OK 😐' : rating === 2 ? 'Could be better 😕' : 'Poor experience 😞'}
          </p>
        )}

        {/* Feedback */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {rating >= 4 ? 'Anything else you loved? (optional)' : 'Tell us what went wrong (optional)'}
          </label>
          <textarea
            value={feedback}
            onChange={e => setFeedback(e.target.value)}
            rows={3}
            placeholder="Your feedback helps us improve..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={!rating || submitting}
          className="w-full bg-blue-600 text-white rounded-xl py-3 text-sm font-semibold hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? 'Submitting...' : 'Submit my review'}
        </button>
      </div>
    </div>
  )
}
