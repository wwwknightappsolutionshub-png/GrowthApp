'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Award,
  Crown,
  ExternalLink,
  Gift,
  LayoutGrid,
  Loader2,
  Users,
} from 'lucide-react'
import { toast } from 'sonner'

import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'
import { MembershipLandingEditor } from '@/components/membership-rewards/MembershipLandingEditor'
import { LoyaltyTiersEditor } from '@/components/membership-rewards/LoyaltyTiersEditor'
import { MembershipTrialBanner } from '@/components/membership-rewards/MembershipTrialBanner'
import { MembershipTrialModal } from '@/components/membership-rewards/MembershipTrialModal'
import { ModuleCardGrid, type ModuleCardItem } from '@/components/modules/ModuleCardGrid'
import {
  auth,
  crm,
  membershipRewards,
  tenants,
  type MembershipPlan,
  type RewardCatalogItem,
} from '@/lib/api-client'
import { formatCurrency, formatDate } from '@/lib/utils'

const SECTIONS = [
  { id: '', label: 'Overview' },
  { id: 'plans', label: 'Plans' },
  { id: 'subscriptions', label: 'Subscriptions' },
  { id: 'rewards', label: 'Rewards catalog' },
  { id: 'loyalty', label: 'Loyalty' },
  { id: 'landing', label: 'Landing page' },
] as const

const EARN_RULE_LABELS: Record<string, string> = {
  booking_completed: 'Booking completed',
  purchase_per_pound: 'Points per £1 spent',
  membership_signup: 'Membership signup',
  refer_win: 'Refer & Win submission',
  review_left: 'Review submitted',
}

export function MembershipRewardsDashboard() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const section = searchParams.get('section') ?? ''

  useEffect(() => {
    if (searchParams.get('upgraded') === '1') {
      toast.success('Membership & Rewards is now active')
      router.replace('/dashboard/membership-rewards')
    }
  }, [searchParams, router])

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data as { full_name?: string }),
  })
  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: () =>
      tenants.get().then((r) => r.data as { id?: string; name?: string; slug?: string }),
  })
  const { data: status } = useQuery({
    queryKey: ['membership-rewards-status'],
    queryFn: async () => (await membershipRewards.status()).data,
  })
  const { data: trial } = useQuery({
    queryKey: ['membership-rewards-trial'],
    queryFn: async () => (await membershipRewards.trialStatus()).data,
  })
  const { data: dash } = useQuery({
    queryKey: ['membership-rewards-dashboard'],
    queryFn: async () => (await membershipRewards.dashboard()).data,
    enabled: !section || section === 'overview',
  })

  const moduleCards: ModuleCardItem[] = [
    {
      title: 'Membership plans',
      description: 'Create weekly, monthly, or yearly plans with included services and discounts.',
      href: '/dashboard/membership-rewards?section=plans',
      icon: Crown,
    },
    {
      title: 'Subscriptions',
      description: 'Assign customers to plans and track active memberships.',
      href: '/dashboard/membership-rewards?section=subscriptions',
      icon: Users,
    },
    {
      title: 'Rewards catalog',
      description: 'Define what members can redeem with their points.',
      href: '/dashboard/membership-rewards?section=rewards',
      icon: Gift,
    },
    {
      title: 'Loyalty leaderboard',
      description: 'View tiers, balances, and manually adjust points.',
      href: '/dashboard/membership-rewards?section=loyalty',
      icon: Award,
    },
    {
      title: 'Public landing page',
      description: 'Publish your /memberships page for customers to browse plans.',
      href: '/dashboard/membership-rewards?section=landing',
      icon: LayoutGrid,
      badge: dash?.landing_published ? 'Live' : 'Draft',
    },
  ]

  return (
    <div className="space-y-6 p-6">
      <TenantWelcomeHeader
        tenantName={tenant?.name}
        userName={me?.full_name}
        subtitle="Membership plans, loyalty points, tiers, and your public memberships page"
      />

      {trial && <MembershipTrialBanner trial={trial} />}
      {trial && tenant?.id && <MembershipTrialModal trial={trial} tenantId={tenant.id} />}

      <nav className="flex flex-wrap gap-2 border-b border-white/10 pb-3">
        {SECTIONS.map((s) => (
          <Link
            key={s.id || 'overview'}
            href={s.id ? `/dashboard/membership-rewards?section=${s.id}` : '/dashboard/membership-rewards'}
            className={
              section === s.id
                ? 'rounded-lg bg-brand-teal-600/30 px-3 py-1.5 text-sm font-medium text-brand-teal-100'
                : 'rounded-lg px-3 py-1.5 text-sm text-slate-400 hover:bg-white/5 hover:text-white'
            }
          >
            {s.label}
          </Link>
        ))}
      </nav>

      {!section && (
        <>
          {dash && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Active subscriptions" value={String(dash.active_subscriptions)} />
              <StatCard label="Members with points" value={String(dash.members_with_points)} />
              <StatCard label="Points issued" value={String(dash.points_issued_lifetime)} />
              <StatCard label="Redemptions" value={String(dash.redemptions_count)} />
            </div>
          )}
          {status?.landing_url && (
            <a
              href={status.landing_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm font-medium text-brand-teal-300 hover:text-brand-teal-200"
            >
              View public memberships page <ExternalLink className="w-4 h-4" />
            </a>
          )}
          <ModuleCardGrid items={moduleCards} />
        </>
      )}

      {section === 'plans' && <PlansSection />}
      {section === 'subscriptions' && <SubscriptionsSection />}
      {section === 'rewards' && <RewardsCatalogSection />}
      {section === 'loyalty' && <LoyaltySection />}
      {section === 'landing' && (
        <MembershipLandingEditor tenantSlug={tenant?.slug} />
      )}
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
      <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
      <p className="mt-1 text-2xl font-bold text-white">{value}</p>
    </div>
  )
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-5 space-y-4">
      <h2 className="text-lg font-semibold text-white">{title}</h2>
      {children}
    </div>
  )
}

function PlansSection() {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [price, setPrice] = useState('')
  const [cycle, setCycle] = useState('monthly')

  const plansQ = useQuery({
    queryKey: ['mr-plans'],
    queryFn: async () => (await membershipRewards.listPlans()).data.items,
  })

  const create = useMutation({
    mutationFn: () =>
      membershipRewards.createPlan({
        name,
        billing_cycle: cycle,
        price_pence: Math.round(parseFloat(price || '0') * 100),
        is_active: true,
      }),
    onSuccess: () => {
      toast.success('Plan created')
      setName('')
      setPrice('')
      qc.invalidateQueries({ queryKey: ['mr-plans'] })
      qc.invalidateQueries({ queryKey: ['membership-rewards-dashboard'] })
    },
    onError: () => toast.error('Could not create plan'),
  })

  return (
    <Panel title="Membership plans">
      <form
        className="grid gap-3 sm:grid-cols-4 items-end"
        onSubmit={(e) => {
          e.preventDefault()
          create.mutate()
        }}
      >
        <Field label="Plan name" value={name} onChange={setName} placeholder="Gold Monthly" />
        <Field label="Price (£)" value={price} onChange={setPrice} placeholder="49.99" type="number" />
        <div>
          <label className="block text-xs text-slate-400 mb-1">Billing cycle</label>
          <select
            value={cycle}
            onChange={(e) => setCycle(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
          >
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={create.isPending || !name.trim()}
          className="rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
        >
          {create.isPending ? 'Saving…' : 'Add plan'}
        </button>
      </form>

      {plansQ.isLoading ? (
        <LoaderRow />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="text-slate-400 border-b border-white/10">
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Price</th>
                <th className="py-2 pr-4">Cycle</th>
                <th className="py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {(plansQ.data ?? []).map((p: MembershipPlan) => (
                <tr key={p.id} className="border-b border-white/5 text-slate-200">
                  <td className="py-3 pr-4 font-medium">{p.name}</td>
                  <td className="py-3 pr-4">{formatCurrency(p.price_pence)}</td>
                  <td className="py-3 pr-4 capitalize">{p.billing_cycle}</td>
                  <td className="py-3">
                    <span
                      className={
                        p.is_active
                          ? 'text-emerald-300 text-xs font-medium'
                          : 'text-slate-500 text-xs'
                      }
                    >
                      {p.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!plansQ.data?.length && <p className="text-sm text-slate-500 py-4">No plans yet.</p>}
        </div>
      )}
    </Panel>
  )
}

function SubscriptionsSection() {
  const qc = useQueryClient()
  const [customerId, setCustomerId] = useState('')
  const [planId, setPlanId] = useState('')

  const subsQ = useQuery({
    queryKey: ['mr-subscriptions'],
    queryFn: async () => (await membershipRewards.listSubscriptions()).data.items,
  })
  const plansQ = useQuery({
    queryKey: ['mr-plans'],
    queryFn: async () => (await membershipRewards.listPlans(true)).data.items,
  })
  const customersQ = useQuery({
    queryKey: ['crm-customers-mr'],
    queryFn: async () =>
      (await crm.listCustomers({ page: 1, page_size: 100 })).data as {
        items: { id: string; first_name: string; last_name?: string; email?: string }[]
      },
  })

  const create = useMutation({
    mutationFn: () =>
      membershipRewards.createSubscription({ customer_id: customerId, plan_id: planId }),
    onSuccess: () => {
      toast.success('Subscription created')
      setCustomerId('')
      setPlanId('')
      qc.invalidateQueries({ queryKey: ['mr-subscriptions'] })
      qc.invalidateQueries({ queryKey: ['membership-rewards-dashboard'] })
    },
    onError: (e: unknown) => {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Could not create subscription'
      toast.error(String(msg))
    },
  })

  const cancel = useMutation({
    mutationFn: (id: string) => membershipRewards.cancelSubscription(id),
    onSuccess: () => {
      toast.success('Subscription canceled')
      qc.invalidateQueries({ queryKey: ['mr-subscriptions'] })
    },
  })

  const customerLabel = (id: string) => {
    const c = customersQ.data?.items?.find((x) => x.id === id)
    if (!c) return id.slice(0, 8)
    return `${c.first_name} ${c.last_name ?? ''}`.trim() || c.email || id.slice(0, 8)
  }
  const planLabel = (id: string) => plansQ.data?.find((p) => p.id === id)?.name ?? id.slice(0, 8)

  return (
    <Panel title="Customer subscriptions">
      <form
        className="grid gap-3 sm:grid-cols-3 items-end"
        onSubmit={(e) => {
          e.preventDefault()
          create.mutate()
        }}
      >
        <div>
          <label className="block text-xs text-slate-400 mb-1">Customer</label>
          <select
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
            required
          >
            <option value="">Select customer</option>
            {(customersQ.data?.items ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.first_name} {c.last_name ?? ''} {c.email ? `(${c.email})` : ''}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Plan</label>
          <select
            value={planId}
            onChange={(e) => setPlanId(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
            required
          >
            <option value="">Select plan</option>
            {(plansQ.data ?? []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} — {formatCurrency(p.price_pence)}/{p.billing_cycle}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={create.isPending || !customerId || !planId}
          className="rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
        >
          Assign membership
        </button>
      </form>

      {subsQ.isLoading ? (
        <LoaderRow />
      ) : (
        <div className="space-y-2">
          {(subsQ.data ?? []).map((s) => (
            <div
              key={s.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/10 bg-brand-forest-950/50 px-4 py-3"
            >
              <div>
                <p className="font-medium text-white">{customerLabel(s.customer_id)}</p>
                <p className="text-xs text-slate-400">
                  {planLabel(s.plan_id)} · {s.status}
                  {s.current_period_end ? ` · ends ${formatDate(s.current_period_end)}` : ''}
                </p>
              </div>
              {s.status === 'active' && (
                <button
                  type="button"
                  onClick={() => cancel.mutate(s.id)}
                  className="text-xs text-red-300 hover:text-red-200"
                >
                  Cancel
                </button>
              )}
            </div>
          ))}
          {!subsQ.data?.length && <p className="text-sm text-slate-500">No subscriptions yet.</p>}
        </div>
      )}
    </Panel>
  )
}

function RewardsCatalogSection() {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [cost, setCost] = useState('')

  const catalogQ = useQuery({
    queryKey: ['mr-catalog'],
    queryFn: async () => (await membershipRewards.listCatalog()).data.items,
  })

  const create = useMutation({
    mutationFn: () =>
      membershipRewards.createCatalogItem({
        name,
        points_cost: parseInt(cost || '0', 10),
        reward_type: 'discount',
        is_active: true,
      }),
    onSuccess: () => {
      toast.success('Reward added')
      setName('')
      setCost('')
      qc.invalidateQueries({ queryKey: ['mr-catalog'] })
    },
    onError: () => toast.error('Could not add reward'),
  })

  return (
    <Panel title="Rewards catalog">
      <form
        className="grid gap-3 sm:grid-cols-3 items-end"
        onSubmit={(e) => {
          e.preventDefault()
          create.mutate()
        }}
      >
        <Field label="Reward name" value={name} onChange={setName} placeholder="£10 off next visit" />
        <Field label="Points cost" value={cost} onChange={setCost} placeholder="500" type="number" />
        <button
          type="submit"
          disabled={create.isPending || !name.trim()}
          className="rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
        >
          Add reward
        </button>
      </form>
      <ul className="space-y-2">
        {(catalogQ.data ?? []).map((item: RewardCatalogItem) => (
          <li
            key={item.id}
            className="flex justify-between rounded-lg border border-white/10 px-4 py-3 text-sm"
          >
            <span className="text-white font-medium">{item.name}</span>
            <span className="text-brand-teal-300">{item.points_cost} pts</span>
          </li>
        ))}
        {!catalogQ.data?.length && <p className="text-sm text-slate-500">No rewards in catalog.</p>}
      </ul>
    </Panel>
  )
}

function LoyaltySection() {
  const qc = useQueryClient()
  const [customerId, setCustomerId] = useState('')
  const [amount, setAmount] = useState('')
  const [note, setNote] = useState('')

  const boardQ = useQuery({
    queryKey: ['mr-leaderboard'],
    queryFn: async () => (await membershipRewards.leaderboard(25)).data.items,
  })
  const customersQ = useQuery({
    queryKey: ['crm-customers-mr'],
    queryFn: async () =>
      (await crm.listCustomers({ page: 1, page_size: 100 })).data as {
        items: { id: string; first_name: string; last_name?: string }[]
      },
  })

  const adjust = useMutation({
    mutationFn: () =>
      membershipRewards.adjustPoints({
        customer_id: customerId,
        amount: parseInt(amount || '0', 10),
        source: 'adjustment',
        description: note || 'Manual adjustment',
      }),
    onSuccess: () => {
      toast.success('Points updated')
      setAmount('')
      setNote('')
      qc.invalidateQueries({ queryKey: ['mr-leaderboard'] })
    },
    onError: () => toast.error('Could not adjust points'),
  })

  return (
    <div className="space-y-6">
      <LoyaltyTiersEditor />
      <div className="grid gap-6 lg:grid-cols-2">
      <Panel title="Leaderboard">
        {boardQ.isLoading ? (
          <LoaderRow />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-white/10">
                <th className="py-2 text-left">Member</th>
                <th className="py-2 text-right">Balance</th>
                <th className="py-2 text-right">Tier</th>
              </tr>
            </thead>
            <tbody>
              {(boardQ.data ?? []).map((row) => (
                <tr key={row.customer_id} className="border-b border-white/5 text-slate-200">
                  <td className="py-2">{row.customer_name || row.customer_id.slice(0, 8)}</td>
                  <td className="py-2 text-right">{row.points_balance}</td>
                  <td className="py-2 text-right capitalize">{row.tier_code}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
      <Panel title="Adjust points">
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault()
            adjust.mutate()
          }}
        >
          <div>
            <label className="block text-xs text-slate-400 mb-1">Customer</label>
            <select
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
              required
            >
              <option value="">Select customer</option>
              {(customersQ.data?.items ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.first_name} {c.last_name ?? ''}
                </option>
              ))}
            </select>
          </div>
          <Field
            label="Amount (+ earn, − deduct)"
            value={amount}
            onChange={setAmount}
            placeholder="100"
            type="number"
          />
          <Field label="Note" value={note} onChange={setNote} placeholder="Birthday bonus" />
          <button
            type="submit"
            disabled={adjust.isPending || !customerId}
            className="rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
          >
            Apply adjustment
          </button>
        </form>
        <EarnRulesEditor />
      </Panel>
      </div>
    </div>
  )
}

function EarnRulesEditor() {
  const qc = useQueryClient()
  const settingsQ = useQuery({
    queryKey: ['mr-settings'],
    queryFn: async () => (await membershipRewards.settings()).data as {
      earn_rules: Record<string, number>
    },
  })
  const [rules, setRules] = useState<Record<string, string>>({})

  const save = useMutation({
    mutationFn: () => {
      const parsed: Record<string, number> = {}
      for (const [k, v] of Object.entries(rules)) {
        parsed[k] = parseInt(v || '0', 10)
      }
      return membershipRewards.updateSettings({ earn_rules: parsed })
    },
    onSuccess: () => {
      toast.success('Earn rules saved')
      qc.invalidateQueries({ queryKey: ['mr-settings'] })
    },
  })

  useEffect(() => {
    if (!settingsQ.data) return
    const initial: Record<string, string> = {}
    for (const [k, v] of Object.entries(settingsQ.data.earn_rules ?? {})) {
      initial[k] = String(v)
    }
    setRules(initial)
  }, [settingsQ.data])

  const keys = Object.keys(EARN_RULE_LABELS)

  return (
    <div className="mt-6 pt-6 border-t border-white/10">
      <h3 className="text-sm font-semibold text-white mb-3">Points earn rules</h3>
      <div className="space-y-2">
        {keys.map((key) => (
          <div key={key} className="flex items-center justify-between gap-2">
            <label className="text-xs text-slate-400 flex-1">{EARN_RULE_LABELS[key]}</label>
            <input
              type="number"
              value={rules[key] ?? ''}
              onChange={(e) => setRules((r) => ({ ...r, [key]: e.target.value }))}
              className="w-20 rounded border border-white/10 bg-brand-forest-950 px-2 py-1 text-sm text-white text-right"
            />
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={() => save.mutate()}
        disabled={save.isPending}
        className="mt-3 text-xs font-semibold text-brand-teal-300 hover:text-brand-teal-200"
      >
        Save earn rules
      </button>
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  type?: string
}) {
  return (
    <div>
      <label className="block text-xs text-slate-400 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white placeholder:text-slate-600"
      />
    </div>
  )
}

function LoaderRow() {
  return (
    <div className="flex justify-center py-8">
      <Loader2 className="w-6 h-6 animate-spin text-brand-teal-400" />
    </div>
  )
}
