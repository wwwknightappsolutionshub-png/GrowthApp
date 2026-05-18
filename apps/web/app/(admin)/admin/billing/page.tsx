'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CreditCard, Plus, Pencil, Trash2, CheckCircle, XCircle } from 'lucide-react'
import { adminApi, type AdminBillingPlan } from '@/lib/api-client'

type Tab = 'plans' | 'subscriptions' | 'transactions'

const EMPTY_PLAN = { name: '', price_gbp_monthly: 0, max_users: 5, max_locations: 1, max_leads_per_month: 50, has_ai_content: false, has_social_posting: false, ai_lead_requests_per_month: 0, is_active: true }

export default function BillingPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('plans')
  const [modal, setModal] = useState<null | 'create' | AdminBillingPlan>(null)
  const [form, setForm] = useState(EMPTY_PLAN)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [toast, setToast] = useState('')

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const { data: plans = [] } = useQuery({ queryKey: ['admin', 'billing', 'plans'], queryFn: () => adminApi.listBillingPlans().then(r => r.data) })
  const { data: subs = [] } = useQuery({ queryKey: ['admin', 'billing', 'subs'], queryFn: () => adminApi.listSubscriptions().then(r => r.data as Record<string, unknown>[]) })
  const { data: txns = [] } = useQuery({ queryKey: ['admin', 'billing', 'txns'], queryFn: () => adminApi.listTransactions().then(r => r.data as Record<string, unknown>[]) })

  const saveMut = useMutation({
    mutationFn: () => modal === 'create' ? adminApi.createBillingPlan(form) : adminApi.updateBillingPlan((modal as AdminBillingPlan).id, form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'billing'] }); setModal(null); showToast('Plan saved') },
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => adminApi.deleteBillingPlan(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'billing'] }); setDeleteId(null) },
  })

  function openCreate() { setForm(EMPTY_PLAN); setModal('create') }
  function openEdit(p: AdminBillingPlan) { setForm({ name: p.name, price_gbp_monthly: p.price_gbp_monthly, max_users: p.max_users, max_locations: p.max_locations, max_leads_per_month: p.max_leads_per_month, has_ai_content: p.has_ai_content, has_social_posting: p.has_social_posting, ai_lead_requests_per_month: p.ai_lead_requests_per_month, is_active: p.is_active }); setModal(p) }

  return (
    <div className="text-white">
      {toast && <div className="fixed inset-x-4 top-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white shadow-lg sm:inset-x-auto sm:right-4">{toast}</div>}

      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2"><CreditCard className="h-6 w-6 text-amber-400" /> Billing & Monetization</h1>
        <p className="text-sm text-gray-400 mt-1">Manage subscription plans, active subscriptions and payment history</p>
      </div>

      <div className="mb-6 flex w-full gap-1 overflow-x-auto rounded-xl border border-gray-800 bg-gray-900 p-1 sm:w-fit">
        {(['plans', 'subscriptions', 'transactions'] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium capitalize transition-colors ${tab === t ? 'bg-amber-500 text-black' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'plans' && (
        <>
          <div className="mb-4 flex justify-end">
            <button onClick={openCreate} className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400">
              <Plus className="h-4 w-4" /> Add Plan
            </button>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(plans as AdminBillingPlan[]).map(p => (
              <div key={p.id} className="rounded-xl border border-gray-800 bg-gray-900 p-5">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-white">{p.name}</h3>
                    <p className="text-2xl font-bold text-amber-400 mt-1">£{p.price_gbp_monthly}<span className="text-sm text-gray-400 font-normal">/mo</span></p>
                  </div>
                  {p.is_active ? <CheckCircle className="h-5 w-5 text-green-400" /> : <XCircle className="h-5 w-5 text-gray-600" />}
                </div>
                <ul className="text-xs text-gray-400 space-y-1 mb-4">
                  <li>Users: {p.max_users}</li>
                  <li>Locations: {p.max_locations}</li>
                  <li>Leads/month: {p.max_leads_per_month}</li>
                  <li>Lead requests/mo: {p.ai_lead_requests_per_month}</li>
                  <li>AI Content: {p.has_ai_content ? '✓' : '✗'}</li>
                  <li>Social Posting: {p.has_social_posting ? '✓' : '✗'}</li>
                </ul>
                <div className="flex gap-2">
                  <button onClick={() => openEdit(p)} className="flex-1 rounded-lg border border-gray-700 py-1.5 text-xs text-gray-300 hover:bg-gray-800 flex items-center justify-center gap-1">
                    <Pencil className="h-3 w-3" /> Edit
                  </button>
                  <button onClick={() => setDeleteId(p.id)} className="rounded-lg border border-red-900 py-1.5 px-3 text-xs text-red-400 hover:bg-red-900/30 flex items-center gap-1">
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {(tab === 'subscriptions' || tab === 'transactions') && (
        <div className="overflow-x-auto rounded-xl border border-gray-800 bg-gray-900">
          <table className="min-w-[680px] w-full text-sm">
            <thead className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wider">
              <tr>{['Tenant ID', 'Plan ID', 'Status', 'Created'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {(tab === 'subscriptions' ? subs : txns).map((s: Record<string, unknown>, i) => (
                <tr key={i} className="hover:bg-gray-800/50 text-gray-300">
                  <td className="px-4 py-3 text-xs">{String(s.tenant_id ?? '—')}</td>
                  <td className="px-4 py-3 text-xs">{String(s.plan_id ?? '—')}</td>
                  <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs ${String(s.status) === 'active' ? 'bg-green-900/30 text-green-400' : 'bg-gray-700 text-gray-400'}`}>{String(s.status)}</span></td>
                  <td className="px-4 py-3 text-gray-400">{String(s.created_at ? new Date(String(s.created_at)).toLocaleDateString() : '—')}</td>
                </tr>
              ))}
              {(tab === 'subscriptions' ? subs : txns).length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-500">No records</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {modal !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md rounded-xl border border-gray-700 bg-gray-900 p-4 max-h-[90dvh] overflow-y-auto sm:p-6">
            <h2 className="mb-4 text-lg font-semibold">{modal === 'create' ? 'Add Plan' : 'Edit Plan'}</h2>
            <div className="space-y-3">
              <div><label className="mb-1 block text-xs text-gray-400">Plan Name</label><input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" /></div>
              <div><label className="mb-1 block text-xs text-gray-400">Price (£/month)</label><input type="number" min={0} value={form.price_gbp_monthly} onChange={e => setForm(f => ({ ...f, price_gbp_monthly: Number(e.target.value) }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" /></div>
              {(['max_users', 'max_locations', 'max_leads_per_month', 'ai_lead_requests_per_month'] as const).map(key => (
                <div key={key}><label className="mb-1 block text-xs text-gray-400 capitalize">{key.replace(/_/g, ' ')}</label><input type="number" min={0} value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: Number(e.target.value) }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" /></div>
              ))}
              {(['has_ai_content', 'has_social_posting', 'is_active'] as const).map(key => (
                <label key={key} className="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.checked }))} /><span className="text-sm text-gray-300 capitalize">{key.replace(/_/g, ' ')}</span></label>
              ))}
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setModal(null)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50">{saveMut.isPending ? 'Saving…' : 'Save'}</button>
            </div>
          </div>
        </div>
      )}

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-2 text-lg font-semibold">Delete Plan</h2>
            <p className="mb-5 text-sm text-gray-400">This action will deactivate the plan.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteId(null)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => deleteMut.mutate(deleteId)} disabled={deleteMut.isPending} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50">{deleteMut.isPending ? 'Deleting…' : 'Delete'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
