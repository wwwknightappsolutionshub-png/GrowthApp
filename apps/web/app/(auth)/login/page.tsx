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
  Lock,
  Mail,
  ShieldCheck,
  AlertCircle,
  Sparkles,
} from 'lucide-react'
import { auth } from '@/lib/api-client'
import { fetchMe } from '@/lib/auth'
import { cn } from '@/lib/utils'

const schema = z.object({
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
  remember: z.boolean().optional(),
})
type FormData = z.infer<typeof schema>

const inputBase =
  'h-11 w-full rounded-md border border-input bg-background px-3 pl-10 text-sm text-foreground transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-offset-0'

export default function LoginPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [magicLoading, setMagicLoading] = useState(false)
  const [magicSent, setMagicSent] = useState(false)

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  const sendMagicLink = async () => {
    const email = getValues('email')
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      toast.error('Enter your email address first')
      return
    }
    setMagicLoading(true)
    try {
      await auth.requestMagicLink(email)
      setMagicSent(true)
      toast.success('Check your inbox for a sign-in link')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Could not send sign-in link')
    } finally {
      setMagicLoading(false)
    }
  }

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    try {
      const res = await auth.login({ email: data.email, password: data.password })

      if (res.data.requires_2fa && res.data.temp_token) {
        router.push(`/verify-2fa?temp_token=${encodeURIComponent(res.data.temp_token)}`)
        return
      }

      toast.success('Welcome back!')
      const me = await fetchMe()
      router.push(me?.is_superadmin ? '/admin' : '/dashboard')
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid email or password'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-brand-teal-500">
          Sign in
        </span>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-foreground">
          Welcome back.
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Enter your credentials to access your CustomerFlow AI workspace.
        </p>
      </div>

      {/* Security badge */}
      <div className="mb-6 flex items-start gap-2 rounded-md border border-brand-forest-100 bg-brand-forest-50/60 px-4 py-3">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand-forest-700" />
        <p className="text-xs font-medium leading-relaxed text-brand-forest-800">
          Protected with 256-bit SSL and GDPR-grade auditing. Your workspace
          data stays in the UK.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        {/* Email */}
        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-foreground/80">
            Email address
          </label>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              {...register('email')}
              type="email"
              autoComplete="email"
              autoFocus
              placeholder="you@business.com"
              className={cn(
                inputBase,
                errors.email
                  ? 'border-destructive/60 focus:border-destructive focus:ring-destructive/20'
                  : 'border-input focus:border-brand-forest-500 focus:ring-brand-forest-500/20',
              )}
            />
          </div>
          {errors.email && (
            <p className="mt-1.5 inline-flex items-center gap-1.5 text-xs text-destructive">
              <AlertCircle className="h-3.5 w-3.5" />
              {errors.email.message}
            </p>
          )}
        </div>

        {/* Password */}
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label className="block text-xs font-semibold uppercase tracking-[0.12em] text-foreground/80">
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-xs font-semibold text-brand-teal-600 transition-colors hover:text-brand-teal-700"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              {...register('password')}
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              placeholder="••••••••••••"
              className={cn(
                inputBase,
                'pr-11',
                errors.password
                  ? 'border-destructive/60 focus:border-destructive focus:ring-destructive/20'
                  : 'border-input focus:border-brand-forest-500 focus:ring-brand-forest-500/20',
              )}
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
          {errors.password && (
            <p className="mt-1.5 inline-flex items-center gap-1.5 text-xs text-destructive">
              <AlertCircle className="h-3.5 w-3.5" />
              {errors.password.message}
            </p>
          )}
        </div>

        {/* Remember */}
        <div className="flex items-center gap-2.5">
          <input
            {...register('remember')}
            id="remember"
            type="checkbox"
            className="h-4 w-4 cursor-pointer rounded border-input text-brand-forest-700 accent-brand-forest-700 focus:ring-brand-forest-500"
          />
          <label htmlFor="remember" className="cursor-pointer select-none text-sm text-muted-foreground">
            Keep me signed in for 30 days
          </label>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-brand-forest-700 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800 disabled:cursor-not-allowed disabled:opacity-60"
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
              Signing in…
            </>
          ) : (
            'Sign in to dashboard'
          )}
        </button>
      </form>

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center">
          <span className="bg-background px-3 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Or passwordless
          </span>
        </div>
      </div>

      <button
        type="button"
        onClick={sendMagicLink}
        disabled={magicLoading || magicSent}
        className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md border border-input bg-background text-sm font-semibold text-foreground transition-all hover:border-brand-teal-400 hover:bg-brand-teal-50/50 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <Sparkles className="h-4 w-4 text-brand-teal-500" />
        {magicSent ? 'Sign-in link sent — check your email' : magicLoading ? 'Sending…' : 'Email me a sign-in link'}
      </button>

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center">
          <span className="bg-background px-3 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            New here?
          </span>
        </div>
      </div>

      <Link
        href="/register"
        className="inline-flex h-11 w-full items-center justify-center rounded-md border border-input text-sm font-semibold text-foreground transition-all hover:border-foreground/40 hover:bg-muted/50"
      >
        Create a free account — 14-day trial
      </Link>

      <p className="mt-6 text-center text-xs leading-relaxed text-muted-foreground">
        By signing in you agree to our{' '}
        <Link href="#" className="underline underline-offset-2 hover:text-foreground">
          Terms of Service
        </Link>{' '}
        and{' '}
        <Link href="#" className="underline underline-offset-2 hover:text-foreground">
          Privacy Policy
        </Link>
        .
        <br />
        CustomerFlow AI is GDPR compliant and UK data is stored in the UK.
      </p>
    </div>
  )
}
