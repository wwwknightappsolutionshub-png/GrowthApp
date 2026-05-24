'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  BarChart3,
  Award,
  Crown,
  ExternalLink,
  Gift,
  LayoutGrid,
  Loader2,
  QrCode,
  Settings,
  Users,
} from 'lucide-react'
import { toast } from 'sonner'

import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'
import { MembershipLandingEditor } from '@/components/membership-rewards/MembershipLandingEditor'
import { LoyaltyTiersEditor } from '@/components/membership-rewards/LoyaltyTiersEditor'
import { MembershipAnalyticsSection } from '@/components/membership-rewards/MembershipAnalyticsSection'
import { MembershipCustomersSection } from '@/components/membership-rewards/MembershipCustomersSection'
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
  { id: 'analytics', label: 'Analytics' },
  { id: 'customers', label: 'Customers' },
  { id: 'plans', label: 'Plans' },
  { id: 'subscriptions', label: 'Subscriptions' },
  { id: 'rewards', label: 'Rewards' },
  { id: 'loyalty', label: 'Tiers' },
  { id: 'settings', label: 'Settings' },
  { id: 'landing', label: 'Landing page' },
] as const

const EARN_RULE_LABELS: Record<string, string> = {
  booking_completed: 'Booking completed',
  purchase_per_pound: 'Points per £1 spent',
  membership_signup: 'Membership signup',
  refer_win: 'Refer & Win submission',
  review_left: 'Review submitted',
  qr_checkin: 'In-store QR check-in',
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
      title: 'Analytics',
      description: 'Points trends, tier mix, top customers, and redemption rate.',
      href: '/dashboard/membership-rewards?section=analytics',
      icon: BarChart3,
    },
    {
      title: 'Loyalty customers',
      description: 'Search members, adjust points, and redeem rewards.',
      href: '/dashboard/membership-rewards?section=customers',
      icon: Users,
    },
    {
      title: 'Scan member QR',
      description: 'Check in customers in-store and award visit points.',
      href: '/dashboard/membership-rewards/scan',
      icon: QrCode,
    },
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
      description: 'Define what members can redeem and view redemption history.',
      href: '/dashboard/membership-rewards?section=rewards',
      icon: Gift,
    },
    {
      title: 'Loyalty tiers',
      description: 'Configure Bronze–Platinum thresholds and benefits.',
      href: '/dashboard/membership-rewards?section=loyalty',
      icon: Award,
    },
    {
      title: 'Program settings',
      description: 'Earn rules and points expiration policy.',
      href: '/dashboard/membership-rewards?section=settings',
      icon: Settings,
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
      {section === 'analytics' && <MembershipAnalyticsSection />}
      {section === 'customers' && <MembershipCustomersSection />}
      {section === 'subscriptions' && <SubscriptionsSection />}
      {section === 'rewards' && <RewardsCatalogSection />}
      {section === 'loyalty' && <LoyaltySection />}
      {section === 'settings' && <SettingsSection />}
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
  const [editingId, setEditingId] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [price, setPrice] = useState('')
  const [cycle, setCycle] = useState('monthly')
  const [discount, setDiscount] = useState('0')
  const [isActive, setIsActive] = useState(true)

  const plansQ = useQuery({
    queryKey: ['mr-plans'],
    queryFn: async () => (await membershipRewards.listPlans()).data.items,
  })

  function resetForm() {
    setEditingId(null)
    setName('')
    setDescription('')
    setPrice('')
    setCycle('monthly')
    setDiscount('0')
    setIsActive(true)
  }

  function startEdit(plan: MembershipPlan) {
    setEditingId(plan.id)
    setName(plan.name)
    setDescription(plan.description ?? '')
    setPrice(String(plan.price_pence / 100))
    setCycle(plan.billing_cycle)
    setDiscount(String(plan.discount_percent))
    setIsActive(plan.is_active)
  }

  const planPayload = () => ({
    name,
    description: description.trim() || null,
    billing_cycle: cycle,
    price_pence: Math.round(parseFloat(price || '0') * 100),
    discount_percent: parseInt(discount || '0', 10),
    is_active: isActive,
  })

  const save = useMutation({
    mutationFn: () =>
      editingId
        ? membershipRewards.updatePlan(editingId, planPayload())
        : membershipRewards.createPlan(planPayload()),
    onSuccess: () => {
      toast.success(editingId ? 'Plan updated' : 'Plan created')
      resetForm()
      qc.invalidateQueries({ queryKey: ['mr-plans'] })
      qc.invalidateQueries({ queryKey: ['mr-landing'] })
      qc.invalidateQueries({ queryKey: ['membership-rewards-dashboard'] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Could not save plan'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => membershipRewards.deletePlan(id),
    onSuccess: () => {
      toast.success('Plan deleted')
      if (editingId) resetForm()
      qc.invalidateQueries({ queryKey: ['mr-plans'] })
      qc.invalidateQueries({ queryKey: ['mr-landing'] })
      qc.invalidateQueries({ queryKey: ['membership-rewards-dashboard'] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Could not delete plan'),
  })

  return (
    <Panel title="Membership plans">
      <form
        className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 items-end mb-6"
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
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
        <Field label="Description" value={description} onChange={setDescription} placeholder="Optional summary" />
        <Field label="Member discount (%)" value={discount} onChange={setDiscount} placeholder="10" type="number" />
        <label className="flex items-center gap-2 text-sm text-slate-300 pb-2">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="rounded border-white/20"
          />
          Active on public page
        </label>
        <div className="flex gap-2 sm:col-span-2 lg:col-span-3">
          <button
            type="submit"
            disabled={save.isPending || !name.trim()}
            className="rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
          >
            {save.isPending ? 'Saving…' : editingId ? 'Update plan' : 'Add plan'}
          </button>
          {editingId ? (
            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg border border-white/20 px-4 py-2 text-sm text-slate-300 hover:bg-white/5"
            >
              Cancel edit
            </button>
          ) : null}
        </div>
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
                <th className="py-2 pr-4">Discount</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(plansQ.data ?? []).map((p: MembershipPlan) => (
                <tr key={p.id} className="border-b border-white/5 text-slate-200">
                  <td className="py-3 pr-4">
                    <p className="font-medium">{p.name}</p>
                    {p.description ? (
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{p.description}</p>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4">{formatCurrency(p.price_pence)}</td>
                  <td className="py-3 pr-4 capitalize">{p.billing_cycle}</td>
                  <td className="py-3 pr-4">{p.discount_percent}%</td>
                  <td className="py-3 pr-4">
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
                  <td className="py-3 text-right space-x-2 whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => startEdit(p)}
                      className="text-xs text-brand-teal-300 hover:text-brand-teal-200"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (window.confirm(`Delete plan "${p.name}"?`)) remove.mutate(p.id)
                      }}
                      disabled={remove.isPending}
                      className="text-xs text-red-400 hover:text-red-300"
                    >
                      Delete
                    </button>
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

  const redemptionsQ = useQuery({
    queryKey: ['mr-redemptions'],
    queryFn: async () => (await membershipRewards.listRedemptions({ limit: 30 })).data.items,
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
    <div className="space-y-6">
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
        <ul className="space-y-2 mt-4">
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

      <Panel title="Redemption history">
        {redemptionsQ.isLoading ? (
          <LoaderRow />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-white/10">
                  <th className="py-2 text-left">Customer</th>
                  <th className="py-2 text-left">Reward</th>
                  <th className="py-2 text-right">Points</th>
                  <th className="py-2 text-right">Status</th>
                </tr>
              </thead>
              <tbody>
                {(redemptionsQ.data ?? []).map((r) => (
                  <tr key={r.id} className="border-b border-white/5 text-slate-200">
                    <td className="py-2">{r.customer_name || r.customer_id.slice(0, 8)}</td>
                    <td className="py-2">{r.reward_name}</td>
                    <td className="py-2 text-right">{r.points_spent}</td>
                    <td className="py-2 text-right capitalize text-xs">{r.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!redemptionsQ.data?.length && (
              <p className="text-sm text-slate-500 py-4">No redemptions yet.</p>
            )}
          </div>
        )}
      </Panel>
    </div>
  )
}

function LoyaltySection() {
  const boardQ = useQuery({
    queryKey: ['mr-leaderboard'],
    queryFn: async () => (await membershipRewards.leaderboard(25)).data.items,
  })

  return (
    <div className="space-y-6">
      <LoyaltyTiersEditor />
      <Panel title="Leaderboard preview">
        {boardQ.isLoading ? (
          <LoaderRow />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-white/10">
                <th className="py-2 text-left">Member</th>
                <th className="py-2 text-right">Balance</th>
                <th className="py-2 text-right">Lifetime</th>
                <th className="py-2 text-right">Tier</th>
              </tr>
            </thead>
            <tbody>
              {(boardQ.data ?? []).map((row) => (
                <tr key={row.customer_id} className="border-b border-white/5 text-slate-200">
                  <td className="py-2">{row.customer_name || row.customer_id.slice(0, 8)}</td>
                  <td className="py-2 text-right">{row.points_balance}</td>
                  <td className="py-2 text-right">{row.points_lifetime}</td>
                  <td className="py-2 text-right capitalize">{row.tier_code}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <Link
          href="/dashboard/membership-rewards?section=customers"
          className="inline-block mt-4 text-xs font-medium text-brand-teal-300 hover:text-brand-teal-200"
        >
          Manage all customers →
        </Link>
      </Panel>
    </div>
  )
}

function SettingsSection() {
  return (
    <Panel title="Program settings">
      <EarnRulesEditor />
    </Panel>
  )
}

function EarnRulesEditor() {
  const qc = useQueryClient()
  const settingsQ = useQuery({
    queryKey: ['mr-settings'],
    queryFn: async () => (await membershipRewards.settings()).data as {
      earn_rules: Record<string, number>
      points_expire_days: number | null
    },
  })
  const [rules, setRules] = useState<Record<string, string>>({})
  const [expireDays, setExpireDays] = useState('')

  const save = useMutation({
    mutationFn: () => {
      const parsed: Record<string, number> = {}
      for (const [k, v] of Object.entries(rules)) {
        parsed[k] = parseInt(v || '0', 10)
      }
      const days = expireDays.trim() === '' ? null : parseInt(expireDays, 10)
      return membershipRewards.updateSettings({
        earn_rules: parsed,
        points_expire_days: days,
      })
    },
    onSuccess: () => {
      toast.success('Settings saved')
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
    setExpireDays(
      settingsQ.data.points_expire_days != null ? String(settingsQ.data.points_expire_days) : '',
    )
  }, [settingsQ.data])

  const keys = Object.keys(EARN_RULE_LABELS)

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-white mb-3">Points earn rules</h3>
        <div className="space-y-2 max-w-md">
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
      </div>
      <div className="max-w-md">
        <label className="block text-xs text-slate-400 mb-1">Points expire after (days)</label>
        <input
          type="number"
          value={expireDays}
          onChange={(e) => setExpireDays(e.target.value)}
          placeholder="Leave empty for no expiration"
          className="w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
        />
        <p className="text-xs text-slate-500 mt-1">Expired points are swept nightly from customer balances.</p>
      </div>
      <button
        type="button"
        onClick={() => save.mutate()}
        disabled={save.isPending}
        className="rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
      >
        Save settings
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
