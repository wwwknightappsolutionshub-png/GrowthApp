'use client'

import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, Loader2, Star, X } from 'lucide-react'
import { useEffect, useState } from 'react'

type CaptureSource = 'exit_intent' | 'share_button' | 'footer_form' | 'manual'

interface ShareReviewModalProps {
  open: boolean
  onClose: () => void
  source?: CaptureSource
  /**
   * Called once the review is successfully submitted. The caller can use this
   * to refresh the carousel without a full page reload.
   */
  onSubmitted?: () => void
}

interface FieldValues {
  author_name: string
  author_role: string
  author_location: string
  author_email: string
  rating: number
  quote: string
}

const EMPTY: FieldValues = {
  author_name: '',
  author_role: '',
  author_location: '',
  author_email: '',
  rating: 5,
  quote: '',
}

/**
 * The visitor-facing "Share your story" modal.
 *
 * Posts to `POST /api/v1/public/marketing/reviews` which sanitises the body
 * server-side (negative-word filter) and auto-publishes 4-5 star reviews.
 */
export function ShareReviewModal({
  open,
  onClose,
  source = 'manual',
  onSubmitted,
}: ShareReviewModalProps) {
  const [values, setValues] = useState<FieldValues>(EMPTY)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!open) {
      const reset = setTimeout(() => {
        setValues(EMPTY)
        setError(null)
        setSuccess(false)
      }, 250)
      return () => clearTimeout(reset)
    }
  }, [open])

  const set = <K extends keyof FieldValues>(key: K, v: FieldValues[K]) =>
    setValues((p) => ({ ...p, [key]: v }))

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!values.author_name.trim() || values.quote.trim().length < 12) {
      setError('Please add your name and a story of at least 12 characters.')
      return
    }
    setLoading(true)
    try {
      const res = await fetch('/api/v1/public/marketing/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          author_name: values.author_name.trim(),
          author_role: values.author_role.trim() || null,
          author_location: values.author_location.trim() || null,
          author_email: values.author_email.trim() || null,
          rating: values.rating,
          quote: values.quote.trim(),
          capture_source: source,
        }),
      })
      if (!res.ok) {
        const body = (await res.json().catch(() => null)) as { detail?: string } | null
        throw new Error(body?.detail || 'We could not save your review. Please try again.')
      }
      setSuccess(true)
      onSubmitted?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
          className="fixed inset-0 z-[100] flex items-end justify-center bg-black/55 p-4 backdrop-blur-sm sm:items-center"
          onClick={onClose}
        >
          <motion.div
            initial={{ y: 24, opacity: 0, scale: 0.98 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: 16, opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            className="relative w-full max-w-lg overflow-hidden rounded-xl border border-border bg-card shadow-elevated"
            onClick={(e) => e.stopPropagation()}
          >
            <header className="flex items-start justify-between gap-4 border-b border-border bg-brand-forest-950 px-7 py-6 text-brand-forest-foreground">
              <div>
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.22em] text-brand-teal-300">
                  Share your story
                </p>
                <h3 className="mt-1.5 font-display text-xl font-bold leading-tight">
                  {source === 'exit_intent'
                    ? 'Before you go — tell us a story?'
                    : 'How has CustomerFlow worked for you?'}
                </h3>
                <p className="mt-1 text-sm text-white/65">
                  We&rsquo;ll feature great stories on this site, with your permission, automatically.
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className="rounded-md p-1.5 text-white/60 transition-colors hover:bg-white/5 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </header>

            {success ? (
              <div className="px-7 py-10 text-center">
                <div className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-full bg-brand-forest-50 text-brand-forest-700">
                  <CheckCircle2 className="h-6 w-6" />
                </div>
                <h4 className="mt-4 font-display text-lg font-bold text-foreground">
                  Thanks — you&rsquo;re on the wall.
                </h4>
                <p className="mt-2 text-sm text-muted-foreground">
                  Your story will appear in the carousel below shortly. We may
                  reach out about featuring it on Google or Trustpilot, with
                  your permission.
                </p>
                <button
                  type="button"
                  onClick={onClose}
                  className="mt-5 inline-flex items-center justify-center rounded-md bg-brand-forest-700 px-5 py-2 text-sm font-semibold text-brand-forest-foreground transition-colors hover:bg-brand-forest-800"
                >
                  Close
                </button>
              </div>
            ) : (
              <form onSubmit={submit} className="space-y-4 px-7 py-6">
                {/* Rating */}
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    Your rating
                  </label>
                  <div className="mt-2 flex items-center gap-1.5">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        type="button"
                        key={star}
                        onClick={() => set('rating', star)}
                        aria-label={`${star} stars`}
                        className="rounded-md p-0.5 transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-brand-forest-400"
                      >
                        <Star
                          className={`h-7 w-7 ${
                            star <= values.rating
                              ? 'fill-amber-400 text-amber-400'
                              : 'text-muted-foreground/30'
                          }`}
                          strokeWidth={1.5}
                        />
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <Field
                    label="Your name"
                    required
                    value={values.author_name}
                    onChange={(v) => set('author_name', v)}
                    placeholder="Mike Thompson"
                  />
                  <Field
                    label="What you do"
                    value={values.author_role}
                    onChange={(v) => set('author_role', v)}
                    placeholder="Master Plumber"
                  />
                  <Field
                    label="Location"
                    value={values.author_location}
                    onChange={(v) => set('author_location', v)}
                    placeholder="Manchester"
                  />
                  <Field
                    type="email"
                    label="Email (optional)"
                    value={values.author_email}
                    onChange={(v) => set('author_email', v)}
                    placeholder="you@business.co.uk"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    Your story
                  </label>
                  <textarea
                    value={values.quote}
                    onChange={(e) => set('quote', e.target.value)}
                    required
                    minLength={12}
                    maxLength={1200}
                    rows={4}
                    placeholder="In 1–2 sentences — what changed since you started?"
                    className="mt-1.5 w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-brand-forest-400 focus:outline-none focus:ring-2 focus:ring-brand-forest-400/30"
                  />
                  <p className="mt-1.5 text-[11px] text-muted-foreground">
                    {values.quote.length}/1200 — we automatically tidy strong
                    language and only auto-publish 4–5 star stories.
                  </p>
                </div>

                {error && (
                  <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs font-medium text-destructive">
                    {error}
                  </p>
                )}

                <div className="flex items-center justify-between gap-3 pt-1">
                  <p className="text-[11px] text-muted-foreground">
                    By submitting you agree to our{' '}
                    <a
                      href="/privacy"
                      className="underline underline-offset-2 hover:text-foreground"
                    >
                      privacy policy
                    </a>
                    .
                  </p>
                  <button
                    type="submit"
                    disabled={loading}
                    className="inline-flex items-center justify-center gap-2 rounded-md bg-brand-forest-700 px-5 py-2 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800 disabled:opacity-60"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" /> Sending…
                      </>
                    ) : (
                      'Submit story'
                    )}
                  </button>
                </div>
              </form>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

interface FieldProps {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  required?: boolean
  type?: string
}

function Field({ label, value, onChange, placeholder, required, type = 'text' }: FieldProps) {
  return (
    <div>
      <label className="block text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
        {label} {required && <span className="text-destructive">*</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-brand-forest-400 focus:outline-none focus:ring-2 focus:ring-brand-forest-400/30"
      />
    </div>
  )
}
