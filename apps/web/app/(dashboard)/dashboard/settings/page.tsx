'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tenants, billing, auth } from '@/lib/api-client'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { useEffect } from 'react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { TwoFactorSettings } from '@/components/settings/TwoFactorSettings'
import { Building2, CreditCard, ExternalLink, Loader2, Save, ShieldCheck, Sparkles } from 'lucide-react'

interface MeForSettings {
  user_type?: 'tenant' | 'freelancer'
}

export default function SettingsPage() {
  const qc = useQueryClient()
  const { data: tenantData, isLoading } = useQuery({ queryKey: ['tenant'], queryFn: () => tenants.get().then(r => r.data) })
  const { data: subData } = useQuery({ queryKey: ['subscription'], queryFn: () => billing.subscription().then(r => r.data).catch(() => null) })
  const { data: me } = useQuery<MeForSettings>({ queryKey: ['me'], queryFn: () => auth.me().then(r => r.data as MeForSettings).catch(() => ({})) })
  const isFreelancer = me?.user_type === 'freelancer'

  const { register, handleSubmit, reset } = useForm()
  useEffect(() => { if (tenantData) reset(tenantData) }, [tenantData, reset])

  const updateMutation = useMutation({
    mutationFn: (data: object) => tenants.update(data),
    onSuccess: () => { toast.success('Settings saved'); qc.invalidateQueries({ queryKey: ['tenant'] }) },
    onError: () => toast.error('Failed to save settings'),
  })

  const portalMutation = useMutation({
    mutationFn: () => billing.portal(),
    onSuccess: (res) => { window.location.href = res.data.portal_url },
    onError: () => toast.error('Could not open billing portal'),
  })

  if (isLoading) return (
    <div className="flex items-center justify-center py-20">
      <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
    </div>
  )

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="overflow-hidden rounded-2xl border border-brand-forest-200 bg-gradient-to-br from-brand-forest-50 via-white to-brand-teal-50 shadow-sm">
        <div className="flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <span className="inline-flex items-center gap-2 rounded-full bg-brand-forest-700 px-3 py-1 text-xs font-semibold text-brand-forest-foreground">
              <Sparkles className="h-3.5 w-3.5" />
              CustomerFlow Workspace
            </span>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-brand-forest-950">Settings</h1>
              <p className="mt-1 max-w-2xl text-sm text-brand-forest-800/80">
                Manage your business profile, security, and subscription settings from one branded control centre.
              </p>
            </div>
          </div>
          <div className="rounded-2xl border border-brand-forest-200 bg-white/80 px-4 py-3 text-sm shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-widest text-brand-forest-700/80">
              Active workspace
            </p>
            <p className="mt-1 font-semibold text-brand-forest-950">{tenantData?.name || 'Your business'}</p>
            <p className="text-xs capitalize text-muted-foreground">{tenantData?.business_type || 'Business'}</p>
          </div>
        </div>
      </div>

      {/* Business Info */}
      <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="mb-5 flex items-start gap-3">
          <div className="rounded-xl bg-brand-forest-100 p-2 text-brand-forest-700">
            <Building2 className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Business Information</h2>
            <p className="text-sm text-muted-foreground">
              Keep your customer-facing contact and web details accurate across CustomerFlow.
            </p>
          </div>
        </div>
        <form onSubmit={handleSubmit(d => updateMutation.mutate(d))} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {[
            { key: 'name', label: 'Business Name' },
            { key: 'phone', label: 'Phone Number' },
            { key: 'email', label: 'Business Email' },
            { key: 'address', label: 'Address' },
            { key: 'city', label: 'City' },
            { key: 'postcode', label: 'Postcode' },
            { key: 'website_url', label: 'Website URL' },
            { key: 'google_review_url', label: 'Google Review URL' },
            ].map(f => (
            <div key={f.key} className={f.key === 'address' ? 'md:col-span-2' : ''}>
              <label className="mb-1 block text-sm font-semibold text-foreground/80">{f.label}</label>
              <input
                {...register(f.key)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm transition focus:border-brand-forest-400 focus:outline-none focus:ring-2 focus:ring-brand-forest-400/20"
              />
            </div>
            ))}
          </div>
          <button
            type="submit"
            disabled={updateMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-forest-700 px-5 py-2 text-sm font-semibold text-brand-forest-foreground shadow-brand transition hover:bg-brand-forest-800 disabled:opacity-50"
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Save Changes
              </>
            )}
          </button>
        </form>
      </section>

      {/* Security — 2FA */}
      <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="mb-5 flex items-start gap-3">
          <div className="rounded-xl bg-brand-teal-50 p-2 text-brand-forest-700">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Security</h2>
            <p className="text-sm text-muted-foreground">
              Protect your account with secure sign-in and two-factor verification.
            </p>
          </div>
        </div>
        <TwoFactorSettings />
      </section>

      {/* Billing */}
      <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="mb-5 flex items-start gap-3">
          <div className="rounded-xl bg-brand-forest-100 p-2 text-brand-forest-700">
            <CreditCard className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Billing</h2>
            <p className="text-sm text-muted-foreground">
              Review your current subscription and billing access.
            </p>
          </div>
        </div>
        {subData ? (
          <div className="space-y-3 rounded-xl border border-border bg-background/60 p-4">
            <div className="flex items-center justify-between gap-4 py-2 border-b border-border/50">
              <span className="text-sm text-muted-foreground">Plan</span>
              <span className="text-right text-sm font-semibold text-foreground">
                {subData.plan?.name} — {formatCurrency((subData.plan?.price_gbp_monthly || 0) * 100)}/mo
              </span>
            </div>
            <div className="flex items-center justify-between gap-4 py-2 border-b border-border/50">
              <span className="text-sm text-muted-foreground">Status</span>
              <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${subData.status === 'active' ? 'bg-brand-forest-100 text-brand-forest-700' : 'bg-amber-50 text-amber-700'}`}>
                {subData.status}
              </span>
            </div>
            {subData.current_period_end && (
              <div className="flex items-center justify-between gap-4 py-2 border-b border-border/50">
                <span className="text-sm text-muted-foreground">Renews</span>
                <span className="text-sm font-medium text-foreground">{formatDate(subData.current_period_end)}</span>
              </div>
            )}
            <button
              onClick={() => portalMutation.mutate()}
              disabled={portalMutation.isPending}
              className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-brand-forest-200 bg-white px-4 py-2 text-sm font-semibold text-brand-forest-800 transition hover:bg-brand-forest-50 disabled:opacity-60"
            >
              {portalMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <ExternalLink className="h-4 w-4" />}
              Manage Subscription
            </button>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-brand-forest-300 bg-brand-forest-50/50 p-4 text-sm text-brand-forest-900">
            No active subscription.{' '}
            {isFreelancer ? (
              <a href="/dashboard/pricing" className="font-semibold text-brand-forest-700 hover:underline">
                View your freelancer plan
              </a>
            ) : (
              <a href="/pricing" className="font-semibold text-brand-forest-700 hover:underline">View plans</a>
            )}
          </div>
        )}
      </section>
    </div>
  )
}
