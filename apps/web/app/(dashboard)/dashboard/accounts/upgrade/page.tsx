'use client'

import Link from 'next/link'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle2, Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { accounting } from '@/lib/api-client'

const FEATURES = [
  'Send invoices by email with payment links',
  'Track expenses and net cashflow',
  'Recurring invoices for retainers',
  'Auto-invoice completed bookings',
  'UK tax summary and accountant export',
  'Customer payment history in CRM',
]

export default function AccountingUpgradePage() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['accounting-status'],
    queryFn: () => accounting.status().then((r) => r.data as { has_accounting: boolean }),
  })

  const checkout = useMutation({
    mutationFn: () =>
      accounting.checkout({
        success_url: `${window.location.origin}/dashboard/accounts?upgraded=1`,
        cancel_url: `${window.location.origin}/dashboard/accounts/upgrade`,
      }),
    onSuccess: (res) => {
      const url = res.data?.checkout_url
      if (url) window.location.href = url
      else toast.error('Checkout is not configured yet. Contact support.')
    },
    onError: () => toast.error('Could not start checkout'),
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="w-8 h-8 animate-spin text-brand-teal-400" />
      </div>
    )
  }

  if (status?.has_accounting) {
    return (
      <div className="max-w-lg mx-auto text-center space-y-4 py-16">
        <CheckCircle2 className="w-12 h-12 mx-auto text-green-400" />
        <h1 className="text-2xl font-bold text-white">Accounting is active</h1>
        <p className="text-brand-teal-100/70 text-sm">You have full access to advanced finance tools.</p>
        <Link href="/dashboard/accounts" className="inline-flex text-brand-teal-300 hover:text-white font-semibold">
          Back to Accounts
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 py-6">
      <Link href="/dashboard/accounts" className="inline-flex items-center gap-1 text-sm text-brand-teal-200 hover:text-white">
        <ArrowLeft className="w-4 h-4" /> Back to Accounts
      </Link>

      <div className="rounded-2xl border border-brand-forest-800 bg-gradient-to-br from-brand-forest-950 via-brand-forest-900 to-brand-forest-950 p-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-teal-600 text-white">
            <Sparkles className="w-6 h-6" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-brand-teal-100/70">Add-on</p>
            <h1 className="text-2xl font-bold text-white">Accounting upgrade</h1>
          </div>
        </div>
        <p className="text-sm text-brand-teal-100/75 mb-6">
          Quotes and invoices are included on every plan. Upgrade to unlock payments, expenses, recurring billing, and
          UK-focused reporting.
        </p>
        <ul className="space-y-2 mb-8">
          {FEATURES.map((f) => (
            <li key={f} className="flex items-start gap-2 text-sm text-brand-teal-50">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-brand-teal-400 mt-0.5" />
              {f}
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={() => checkout.mutate()}
          disabled={checkout.isPending}
          className="w-full rounded-lg bg-brand-teal-600 px-4 py-3 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
        >
          {checkout.isPending ? 'Redirecting…' : 'Upgrade via Stripe'}
        </button>
        <p className="mt-3 text-xs text-center text-brand-teal-100/50">GBP billing · UK VAT tools included</p>
      </div>
    </div>
  )
}
