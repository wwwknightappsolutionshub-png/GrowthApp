'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import {
  Eye,
  EyeOff,
  User,
  Users,
  Mail,
  Phone,
  Lock,
  Building2,
  Briefcase,
  Wrench,
  MapPin,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  ChevronDown,
} from 'lucide-react'
import { auth } from '@/lib/api-client'
import { cn } from '@/lib/utils'

const BUSINESS_TYPES = [
  { value: 'plumber', label: 'Plumber' },
  { value: 'electrician', label: 'Electrician' },
  { value: 'cleaner', label: 'Cleaner / Cleaning Company' },
  { value: 'roofer', label: 'Roofer' },
  { value: 'painter', label: 'Painter & Decorator' },
  { value: 'builder', label: 'Builder / General Contractor' },
  { value: 'landscaper', label: 'Landscaper / Gardener' },
  { value: 'handyman', label: 'Handyman' },
  { value: 'salon', label: 'Salon / Beauty' },
  { value: 'hvac', label: 'HVAC / Heating Engineer' },
  { value: 'locksmith', label: 'Locksmith' },
  { value: 'other', label: 'Other trade' },
]

function getPasswordStrength(pw: string): {
  score: number
  label: string
  tone: 'destructive' | 'warning' | 'success'
} {
  if (!pw) return { score: 0, label: '', tone: 'destructive' }
  let score = 0
  if (pw.length >= 8) score++
  if (pw.length >= 12) score++
  if (/[A-Z]/.test(pw)) score++
  if (/[0-9]/.test(pw)) score++
  if (/[^A-Za-z0-9]/.test(pw)) score++

  if (score <= 1) return { score, label: 'Too weak', tone: 'destructive' }
  if (score === 2) return { score, label: 'Weak', tone: 'destructive' }
  if (score === 3) return { score, label: 'Fair', tone: 'warning' }
  if (score === 4) return { score, label: 'Strong', tone: 'success' }
  return { score: 5, label: 'Very strong', tone: 'success' }
}

const schema = z
  .object({
    user_type: z.enum(['tenant', 'freelancer']),
    full_name: z.string().min(2, 'Enter your full name'),
    email: z.string().email('Enter a valid email address'),
    phone: z.string().optional(),
    password: z
      .string()
      .min(8, 'At least 8 characters required')
      .regex(/[A-Z]/, 'Must include an uppercase letter')
      .regex(/[0-9]/, 'Must include a number'),
    business_name: z.string().optional(),
    business_type: z.string().optional(),
    postcode: z.string().optional(),
    estimated_client_count: z
      .union([z.string(), z.number()])
      .optional()
      .transform((v) => (v === undefined || v === '' ? undefined : Number(v))),
    terms: z.literal(true, { errorMap: () => ({ message: 'You must agree to the terms' }) }),
  })
  .superRefine((data, ctx) => {
    if (data.user_type === 'tenant') {
      if (!data.business_name || data.business_name.trim().length < 2) {
        ctx.addIssue({
          path: ['business_name'],
          code: z.ZodIssueCode.custom,
          message: 'Enter your business name',
        })
      }
      if (!data.business_type) {
        ctx.addIssue({
          path: ['business_type'],
          code: z.ZodIssueCode.custom,
          message: 'Select your trade or industry',
        })
      }
      if (!data.postcode || data.postcode.trim().length < 2) {
        ctx.addIssue({
          path: ['postcode'],
          code: z.ZodIssueCode.custom,
          message: 'Enter your postcode',
        })
      }
    } else if (data.user_type === 'freelancer') {
      if (
        data.estimated_client_count === undefined ||
        Number.isNaN(data.estimated_client_count) ||
        (data.estimated_client_count as number) < 0
      ) {
        ctx.addIssue({
          path: ['estimated_client_count'],
          code: z.ZodIssueCode.custom,
          message: 'Enter your estimated number of clients',
        })
      }
    }
  })
type FormData = z.infer<typeof schema>

interface PendingSignup {
  pending_id: string
  email: string
}

function Field({
  label,
  required,
  error,
  children,
}: {
  label: string
  required?: boolean
  error?: string
  children: React.ReactNode
}) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-foreground/80">
        {label}
        {required && <span className="ml-0.5 text-destructive">*</span>}
      </label>
      {children}
      {error && (
        <p className="mt-1.5 inline-flex items-center gap-1.5 text-xs text-destructive">
          <AlertCircle className="h-3.5 w-3.5" />
          {error}
        </p>
      )}
    </div>
  )
}

const inputBase =
  'h-11 w-full rounded-md border border-input bg-background pl-10 pr-3 text-sm text-foreground transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2'

function inputCls(hasError: boolean) {
  return cn(
    inputBase,
    hasError
      ? 'border-destructive/60 focus:border-destructive focus:ring-destructive/20'
      : 'border-input focus:border-brand-forest-500 focus:ring-brand-forest-500/20',
  )
}

export default function RegisterPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [pending, setPending] = useState<PendingSignup | null>(null)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { user_type: 'tenant' },
  })

  const watchedPassword = watch('password', '')
  const watchedUserType = watch('user_type')
  const isFreelancer = watchedUserType === 'freelancer'
  const strength = getPasswordStrength(watchedPassword)

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    try {
      const { terms, ...rest } = data
      const payload =
        rest.user_type === 'freelancer'
          ? {
              user_type: 'freelancer' as const,
              email: rest.email,
              password: rest.password,
              full_name: rest.full_name,
              phone: rest.phone?.trim() || undefined,
              estimated_client_count: Number(rest.estimated_client_count),
            }
          : {
              user_type: 'tenant' as const,
              email: rest.email,
              password: rest.password,
              full_name: rest.full_name,
              phone: rest.phone?.trim() || undefined,
              business_name: rest.business_name,
              business_type: rest.business_type,
              postcode: rest.postcode,
            }

      const res = await auth.signupInitiate(payload)
      setPending(res.data as PendingSignup)
      toast.success('Verification code sent! Check your email.')
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Could not create your account. Please try again.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  if (pending) {
    return <VerifyOtpStep pending={pending} onCancel={() => setPending(null)} onComplete={() => router.push('/onboarding')} />
  }

  const strengthColor =
    strength.tone === 'success'
      ? 'bg-brand-forest-500'
      : strength.tone === 'warning'
      ? 'bg-warning'
      : 'bg-destructive'

  return (
    <div>
      {/* Header */}
      <div className="mb-7">
        <span className="inline-flex items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.16em] text-brand-teal-700">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-teal-500" />
          14-day free trial · No credit card required
        </span>
        <h1 className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground">
          Create your workspace.
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Set up CustomerFlow AI for your business in under 2 minutes.
        </p>
      </div>

      {/* Security badge */}
      <div className="mb-6 flex items-start gap-2 rounded-md border border-brand-forest-100 bg-brand-forest-50/60 px-4 py-3">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand-forest-700" />
        <p className="text-xs font-medium leading-relaxed text-brand-forest-800">
          GDPR compliant · 256-bit SSL · Your data stays in the UK.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {/* Account type selector */}
        <Field label="I am signing up as" required error={errors.user_type?.message}>
          <div className="grid grid-cols-2 gap-2">
            <label
              className={cn(
                'flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2.5 text-sm transition-colors',
                !isFreelancer
                  ? 'border-brand-forest-500 bg-brand-forest-50 text-brand-forest-800'
                  : 'border-input bg-background text-foreground hover:bg-muted/40',
              )}
            >
              <input
                {...register('user_type')}
                type="radio"
                value="tenant"
                className="sr-only"
              />
              <Building2 className="h-4 w-4 shrink-0" />
              <span className="font-medium">Business / Tenant</span>
            </label>
            <label
              className={cn(
                'flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2.5 text-sm transition-colors',
                isFreelancer
                  ? 'border-brand-forest-500 bg-brand-forest-50 text-brand-forest-800'
                  : 'border-input bg-background text-foreground hover:bg-muted/40',
              )}
            >
              <input
                {...register('user_type')}
                type="radio"
                value="freelancer"
                className="sr-only"
              />
              <Briefcase className="h-4 w-4 shrink-0" />
              <span className="font-medium">Freelancer</span>
            </label>
          </div>
        </Field>

        {/* Row: name + phone */}
        <div className="grid grid-cols-2 gap-3">
          <Field label="Full name" required error={errors.full_name?.message}>
            <div className="relative">
              <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                {...register('full_name')}
                type="text"
                autoComplete="name"
                placeholder="John Smith"
                className={inputCls(!!errors.full_name)}
              />
            </div>
          </Field>
          <Field label="Phone (optional)" error={errors.phone?.message}>
            <div className="relative">
              <Phone className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                {...register('phone')}
                type="tel"
                autoComplete="tel"
                placeholder="07700 000000"
                className={inputCls(!!errors.phone)}
              />
            </div>
          </Field>
        </div>

        {/* Email */}
        <Field label="Work email address" required error={errors.email?.message}>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              {...register('email')}
              type="email"
              autoComplete="email"
              placeholder="john@business.com"
              className={inputCls(!!errors.email)}
            />
          </div>
        </Field>

        {/* Password */}
        <Field label="Password" required error={errors.password?.message}>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              {...register('password')}
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Min 8 chars, uppercase + number"
              className={cn(inputCls(!!errors.password), 'pr-11')}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
              tabIndex={-1}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          {watchedPassword.length > 0 && (
            <div className="mt-2.5">
              <div className="mb-1 flex gap-1">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className={cn(
                      'h-1 flex-1 rounded-full transition-colors duration-300',
                      i <= strength.score ? strengthColor : 'bg-muted',
                    )}
                  />
                ))}
              </div>
              <div className="flex items-center justify-between">
                <p
                  className={cn(
                    'text-xs font-semibold',
                    strength.tone === 'success'
                      ? 'text-brand-forest-700'
                      : strength.tone === 'warning'
                      ? 'text-warning'
                      : 'text-destructive',
                  )}
                >
                  {strength.label}
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  {[
                    { ok: watchedPassword.length >= 8, label: '8+ chars' },
                    { ok: /[A-Z]/.test(watchedPassword), label: 'A-Z' },
                    { ok: /[0-9]/.test(watchedPassword), label: '0-9' },
                  ].map(({ ok, label }) => (
                    <span
                      key={label}
                      className={cn(
                        'inline-flex items-center gap-0.5',
                        ok ? 'text-brand-forest-700' : 'text-muted-foreground/60',
                      )}
                    >
                      <CheckCircle2 className={cn('h-3 w-3', ok ? 'opacity-100' : 'opacity-40')} />
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </Field>

        {!isFreelancer && (
          <>
            {/* Business name */}
            <Field label="Business name" required error={errors.business_name?.message}>
              <div className="relative">
                <Building2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  {...register('business_name')}
                  type="text"
                  placeholder="Smith's Plumbing Ltd"
                  className={inputCls(!!errors.business_name)}
                />
              </div>
            </Field>

            {/* Row: trade + postcode */}
            <div className="grid grid-cols-2 gap-3">
              <Field label="Trade / Industry" required error={errors.business_type?.message}>
                <div className="relative">
                  <Wrench className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <select
                    {...register('business_type')}
                    className={cn(inputCls(!!errors.business_type), 'cursor-pointer appearance-none pr-10')}
                  >
                    <option value="">Select trade…</option>
                    {BUSINESS_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>
              </Field>
              <Field label="Postcode" required error={errors.postcode?.message}>
                <div className="relative">
                  <MapPin className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <input
                    {...register('postcode')}
                    type="text"
                    placeholder="SW1A 1AA"
                    className={cn(inputCls(!!errors.postcode), 'uppercase')}
                  />
                </div>
              </Field>
            </div>
          </>
        )}

        {isFreelancer && (
          <>
            <Field
              label="Estimated number of clients you'll service"
              required
              error={errors.estimated_client_count?.message as string | undefined}
            >
              <div className="relative">
                <Users className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  {...register('estimated_client_count')}
                  type="number"
                  inputMode="numeric"
                  min={0}
                  step={1}
                  placeholder="e.g. 25"
                  className={inputCls(!!errors.estimated_client_count)}
                />
              </div>
            </Field>

            {/* Why we ask — pricing transparency for freelancers */}
            <div className="rounded-md border border-brand-teal-200 bg-brand-teal-50/60 p-3.5 text-xs text-brand-teal-900">
              <p className="mb-1.5 font-semibold uppercase tracking-[0.12em] text-brand-teal-700">
                Why we ask
              </p>
              <p className="leading-relaxed">
                Your plan price is calculated from the number of clients you&apos;ll manage on
                CustomerFlow &mdash; <strong>not the number of users on your team</strong>. This lets
                us bill fairly: small portfolios pay a flat fee, larger portfolios get volume pricing
                with no surprises.
              </p>
              <ul className="mt-2 space-y-0.5 text-[11px] text-brand-teal-800">
                <li>&bull; 1&ndash;50 clients &mdash; <strong>&pound;50/month</strong> flat</li>
                <li>&bull; 51&ndash;100 clients &mdash; <strong>&pound;40/month</strong> flat (better rate)</li>
                <li>
                  &bull; 100+ clients &mdash; <strong>&pound;40 + &pound;5 per extra client</strong>
                </li>
              </ul>
              <p className="mt-2 text-[11px] text-brand-teal-700">
                You can update this estimate anytime from your dashboard &mdash; we&apos;ll recalculate
                automatically.
              </p>
            </div>
          </>
        )}

        {/* Terms */}
        <div>
          <div className="flex items-start gap-3">
            <input
              {...register('terms')}
              id="terms"
              type="checkbox"
              className="mt-0.5 h-4 w-4 cursor-pointer rounded border-input text-brand-forest-700 accent-brand-forest-700 focus:ring-brand-forest-500"
            />
            <label
              htmlFor="terms"
              className="cursor-pointer text-sm leading-relaxed text-muted-foreground"
            >
              I agree to the{' '}
              <Link
                href="#"
                className="font-medium text-brand-teal-600 underline-offset-2 hover:underline"
              >
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link
                href="#"
                className="font-medium text-brand-teal-600 underline-offset-2 hover:underline"
              >
                Privacy Policy
              </Link>
              . I understand that my data will be stored securely in the UK.
            </label>
          </div>
          {errors.terms && (
            <p className="ml-7 mt-1.5 inline-flex items-center gap-1.5 text-xs text-destructive">
              <AlertCircle className="h-3.5 w-3.5" />
              {errors.terms.message}
            </p>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="mt-2 inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-brand-forest-700 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <>
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Creating your workspace…
            </>
          ) : (
            'Start free 14-day trial →'
          )}
        </button>

        {/* What you get */}
        <div className="rounded-md border border-border bg-muted/30 p-4">
          <p className="mb-3 font-mono text-[11px] font-semibold uppercase tracking-[0.16em] text-foreground/80">
            What you get instantly
          </p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2">
            {[
              'Lead capture pages',
              'CRM pipeline',
              'Quote builder',
              'Booking calendar',
              'Review automation',
              'SMS follow-ups',
            ].map((item) => (
              <div key={item} className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-brand-forest-700" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link
          href="/login"
          className="font-semibold text-brand-teal-600 transition-colors hover:text-brand-teal-700"
        >
          Sign in
        </Link>
      </p>
    </div>
  )
}


// ── OTP verification step ────────────────────────────────────────────────────

function VerifyOtpStep({
  pending,
  onCancel,
  onComplete,
}: {
  pending: PendingSignup
  onCancel: () => void
  onComplete: () => void
}) {
  const [emailCode, setEmailCode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [resending, setResending] = useState(false)

  const submit = async () => {
    if (emailCode.length !== 6) {
      toast.error('Enter the 6-digit code from your email')
      return
    }
    setSubmitting(true)
    try {
      const ref =
        typeof window !== 'undefined'
          ? new URLSearchParams(window.location.search).get('ref')
          : null
      await auth.signupVerify(
        {
          pending_id: pending.pending_id,
          email_code: emailCode,
        },
        ref || undefined,
      )
      toast.success('Verified! Welcome to CustomerFlow AI.')
      onComplete()
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Verification failed. Try again.'
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  const resend = async () => {
    setResending(true)
    try {
      await auth.signupResend(pending.pending_id)
      toast.success('Code re-sent to your email')
    } catch {
      toast.error('Could not resend code')
    } finally {
      setResending(false)
    }
  }

  return (
    <div>
      <div className="mb-7">
        <span className="inline-flex items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.16em] text-brand-teal-700">
          <ShieldCheck className="h-3 w-3" />
          Step 2 of 2 · Verify your identity
        </span>
        <h1 className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground">
          Verify your email.
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          We sent a 6-digit code to <strong>{pending.email}</strong>. Enter it below to finish
          creating your account.
        </p>
      </div>

      <div className="space-y-5">
        <Field label="Email code" required>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={emailCode}
              onChange={(e) => setEmailCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              placeholder="123456"
              className={cn(inputCls(false), 'font-mono tracking-[0.4em] text-center')}
            />
          </div>
          <button
            type="button"
            onClick={resend}
            disabled={resending}
            className="mt-1.5 text-xs text-brand-teal-700 hover:underline disabled:opacity-50"
          >
            {resending ? 'Sending…' : 'Resend email code'}
          </button>
        </Field>

        <button
          type="button"
          onClick={submit}
          disabled={submitting}
          className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-brand-forest-700 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? 'Verifying…' : 'Verify & create account →'}
        </button>

        <button
          type="button"
          onClick={onCancel}
          className="block w-full text-center text-xs text-muted-foreground hover:text-foreground"
        >
          ← Back to signup form
        </button>
      </div>
    </div>
  )
}
