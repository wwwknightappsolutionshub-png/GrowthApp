'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  leadMarketplace as lm,
  type LMCategory, type LMQualityRule, type LMPricing,
  type LMTerritory, type LMAssignmentRule, type LMInventoryItem,
  type LMStatus,
} from '@/lib/api-client'
import {
  Tag, ShieldCheck, PoundSterling, MapPin, GitBranch, ShoppingBag,
  Plus, Pencil, Trash2, Check, X, ChevronDown, ChevronUp,
  Eye, UserCheck, Undo2, BadgeCheck, Zap,
  CheckCircle2, XCircle,
} from 'lucide-react'

// ── Shared primitives ─────────────────────────────────────────────────────────
const inp = 'w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none'
const lbl = 'mb-1 block text-xs font-medium text-gray-400'
const btnPrimary = 'flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-black hover:bg-amber-400 disabled:opacity-40 transition'
const btnGhost = 'flex items-center gap-1.5 rounded-lg border border-gray-700 px-3 py-1.5 text-xs text-gray-300 hover:border-gray-500 hover:text-white transition'
const btnDanger = 'flex items-center gap-1.5 rounded-lg border border-red-800 px-3 py-1.5 text-xs text-red-400 hover:bg-red-900/30 transition'

type ToastKind = 'ok' | 'err'
interface Toast { id: number; kind: ToastKind; msg: string }

function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([])
  const push = (kind: ToastKind, msg: string) => {
    const id = Date.now()
    setToasts(t => [...t, { id, kind, msg }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3200)
  }
  return { toasts, push }
}

function ToastStack({ toasts }: { toasts: Toast[] }) {
  return (
    <div className="fixed right-5 top-5 z-50 flex flex-col gap-2">
      {toasts.map(t => (
        <div key={t.id} className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm shadow-xl ${t.kind === 'ok' ? 'bg-emerald-600' : 'bg-red-600'} text-white`}>
          {t.kind === 'ok' ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
          {t.msg}
        </div>
      ))}
    </div>
  )
}

const TABS = [
  { key: 'categories',       label: 'Categories',       icon: Tag },
  { key: 'pricing',          label: 'Pricing',          icon: PoundSterling },
  { key: 'territories',      label: 'Territories',      icon: MapPin },
  { key: 'quality-rules',    label: 'Quality Rules',    icon: ShieldCheck },
  { key: 'assignment-rules', label: 'Assignment Rules', icon: GitBranch },
  { key: 'inventory',        label: 'Marketplace Inventory', icon: ShoppingBag },
] as const
type TabKey = typeof TABS[number]['key']

// ── Status pill ───────────────────────────────────────────────────────────────
const STATUS_COLORS: Record<LMStatus, string> = {
  available:  'bg-emerald-500/15 text-emerald-400',
  reserved:   'bg-blue-500/15 text-blue-400',
  sold:       'bg-gray-500/15 text-gray-400',
  expired:    'bg-red-500/15 text-red-400',
}
function StatusPill({ status }: { status: string }) {
  const cls = STATUS_COLORS[status as LMStatus] ?? 'bg-gray-700 text-gray-400'
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${cls}`}>{status}</span>
}

// ── Confirm-delete helper ─────────────────────────────────────────────────────
function ConfirmDelete({ onConfirm, onCancel }: { onConfirm: () => void; onCancel: () => void }) {
  return (
    <span className="flex items-center gap-1">
      <button onClick={onConfirm} className="rounded bg-red-600 px-2 py-0.5 text-xs text-white hover:bg-red-500">Yes</button>
      <button onClick={onCancel} className="rounded bg-gray-700 px-2 py-0.5 text-xs text-gray-300 hover:bg-gray-600">No</button>
    </span>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// CATEGORIES TAB
// ═════════════════════════════════════════════════════════════════════════════
function CategoriesTab({ push }: { push: (k: ToastKind, m: string) => void }) {
  const qc = useQueryClient()
  const { data: cats = [], isLoading } = useQuery({ queryKey: ['lm-categories'], queryFn: () => lm.listCategories().then(r => r.data) })
  const [form, setForm] = useState({ name: '', description: '' })
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ name: '', description: '' })
  const [confirmDel, setConfirmDel] = useState<string | null>(null)

  const createMut = useMutation({
    mutationFn: () => lm.createCategory({ name: form.name, description: form.description || null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-categories'] }); setForm({ name: '', description: '' }); push('ok', 'Category created') },
    onError: () => push('err', 'Failed to create category'),
  })
  const updateMut = useMutation({
    mutationFn: (id: string) => lm.updateCategory(id, { name: editForm.name, description: editForm.description || null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-categories'] }); setEditId(null); push('ok', 'Category updated') },
    onError: () => push('err', 'Failed to update category'),
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => lm.deleteCategory(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-categories'] }); push('ok', 'Category deleted') },
    onError: () => push('err', 'Failed to delete category'),
  })

  return (
    <div>
      {/* Create form */}
      <div className="mb-5 rounded-xl border border-gray-800 bg-gray-900 p-4">
        <p className="mb-3 text-sm font-semibold text-white">New Category</p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div><label className={lbl}>Name *</label><input className={inp} value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="e.g. Plumbing" /></div>
          <div><label className={lbl}>Description</label><input className={inp} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Optional" /></div>
        </div>
        <button className={`${btnPrimary} mt-3`} disabled={!form.name || createMut.isPending} onClick={() => createMut.mutate()}><Plus className="h-3.5 w-3.5" />Add Category</button>
      </div>
      {/* Table */}
      <div className="rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-900 text-xs text-gray-400"><tr><th className="px-4 py-2.5 text-left">Name</th><th className="px-4 py-2.5 text-left">Description</th><th className="px-4 py-2.5 text-left">Actions</th></tr></thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && <tr><td colSpan={3} className="px-4 py-6 text-center text-gray-500">Loading…</td></tr>}
            {!isLoading && cats.length === 0 && <tr><td colSpan={3} className="px-4 py-6 text-center text-gray-500">No categories yet.</td></tr>}
            {cats.map(c => (
              <tr key={c.id} className="bg-gray-950 hover:bg-gray-900">
                <td className="px-4 py-2.5 text-white">
                  {editId === c.id
                    ? <input className={inp} value={editForm.name} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} />
                    : c.name}
                </td>
                <td className="px-4 py-2.5 text-gray-400 max-w-xs truncate">
                  {editId === c.id
                    ? <input className={inp} value={editForm.description} onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))} />
                    : (c.description ?? '—')}
                </td>
                <td className="px-4 py-2.5">
                  {editId === c.id ? (
                    <span className="flex gap-1">
                      <button className={btnPrimary} onClick={() => updateMut.mutate(c.id)}><Check className="h-3 w-3" /></button>
                      <button className={btnGhost} onClick={() => setEditId(null)}><X className="h-3 w-3" /></button>
                    </span>
                  ) : confirmDel === c.id ? (
                    <ConfirmDelete onConfirm={() => { deleteMut.mutate(c.id); setConfirmDel(null) }} onCancel={() => setConfirmDel(null)} />
                  ) : (
                    <span className="flex gap-1">
                      <button className={btnGhost} onClick={() => { setEditId(c.id); setEditForm({ name: c.name, description: c.description ?? '' }) }}><Pencil className="h-3 w-3" /></button>
                      <button className={btnDanger} onClick={() => setConfirmDel(c.id)}><Trash2 className="h-3 w-3" /></button>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// PRICING TAB
// ═════════════════════════════════════════════════════════════════════════════
function PricingTab({ push }: { push: (k: ToastKind, m: string) => void }) {
  const qc = useQueryClient()
  const { data: cats = [] } = useQuery({ queryKey: ['lm-categories'], queryFn: () => lm.listCategories().then(r => r.data) })
  const { data: pricing = [], isLoading } = useQuery({ queryKey: ['lm-pricing'], queryFn: () => lm.listPricing().then(r => r.data) })
  const catMap = Object.fromEntries(cats.map(c => [c.id, c.name]))

  const [form, setForm] = useState({ category_id: '', base_price: '', high_quality_multiplier: '1.0', exclusive_multiplier: '1.0' })
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ base_price: '', high_quality_multiplier: '', exclusive_multiplier: '' })
  const [confirmDel, setConfirmDel] = useState<string | null>(null)

  const createMut = useMutation({
    mutationFn: () => lm.createPricing({ category_id: form.category_id, base_price: parseFloat(form.base_price), high_quality_multiplier: parseFloat(form.high_quality_multiplier), exclusive_multiplier: parseFloat(form.exclusive_multiplier) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-pricing'] }); setForm({ category_id: '', base_price: '', high_quality_multiplier: '1.0', exclusive_multiplier: '1.0' }); push('ok', 'Pricing rule created') },
    onError: () => push('err', 'Failed to create pricing rule'),
  })
  const updateMut = useMutation({
    mutationFn: (id: string) => lm.updatePricing(id, { base_price: parseFloat(editForm.base_price), high_quality_multiplier: parseFloat(editForm.high_quality_multiplier), exclusive_multiplier: parseFloat(editForm.exclusive_multiplier) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-pricing'] }); setEditId(null); push('ok', 'Pricing updated') },
    onError: () => push('err', 'Failed to update pricing'),
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => lm.deletePricing(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-pricing'] }); push('ok', 'Pricing deleted') },
    onError: () => push('err', 'Failed to delete'),
  })

  return (
    <div>
      <div className="mb-5 rounded-xl border border-gray-800 bg-gray-900 p-4">
        <p className="mb-3 text-sm font-semibold text-white">New Pricing Rule</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div><label className={lbl}>Category *</label>
            <select className={inp} value={form.category_id} onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}>
              <option value="">Select…</option>{cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div><label className={lbl}>Base Price (£)</label><input className={inp} type="number" step="0.01" value={form.base_price} onChange={e => setForm(f => ({ ...f, base_price: e.target.value }))} placeholder="0.00" /></div>
          <div><label className={lbl}>High Quality ×</label><input className={inp} type="number" step="0.01" value={form.high_quality_multiplier} onChange={e => setForm(f => ({ ...f, high_quality_multiplier: e.target.value }))} /></div>
          <div><label className={lbl}>Exclusive ×</label><input className={inp} type="number" step="0.01" value={form.exclusive_multiplier} onChange={e => setForm(f => ({ ...f, exclusive_multiplier: e.target.value }))} /></div>
        </div>
        <button className={`${btnPrimary} mt-3`} disabled={!form.category_id || !form.base_price || createMut.isPending} onClick={() => createMut.mutate()}><Plus className="h-3.5 w-3.5" />Add Pricing</button>
      </div>
      <div className="rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-900 text-xs text-gray-400"><tr><th className="px-4 py-2.5 text-left">Category</th><th className="px-4 py-2.5 text-right">Base Price</th><th className="px-4 py-2.5 text-right">HQ ×</th><th className="px-4 py-2.5 text-right">Excl ×</th><th className="px-4 py-2.5 text-left">Actions</th></tr></thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-500">Loading…</td></tr>}
            {!isLoading && pricing.length === 0 && <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-500">No pricing rules yet.</td></tr>}
            {pricing.map(p => (
              <tr key={p.id} className="bg-gray-950 hover:bg-gray-900">
                <td className="px-4 py-2.5 text-white">{catMap[p.category_id] ?? p.category_id}</td>
                {editId === p.id ? (
                  <>
                    <td className="px-4 py-2.5"><input className={inp} type="number" step="0.01" value={editForm.base_price} onChange={e => setEditForm(f => ({ ...f, base_price: e.target.value }))} /></td>
                    <td className="px-4 py-2.5"><input className={inp} type="number" step="0.001" value={editForm.high_quality_multiplier} onChange={e => setEditForm(f => ({ ...f, high_quality_multiplier: e.target.value }))} /></td>
                    <td className="px-4 py-2.5"><input className={inp} type="number" step="0.001" value={editForm.exclusive_multiplier} onChange={e => setEditForm(f => ({ ...f, exclusive_multiplier: e.target.value }))} /></td>
                    <td className="px-4 py-2.5"><span className="flex gap-1"><button className={btnPrimary} onClick={() => updateMut.mutate(p.id)}><Check className="h-3 w-3" /></button><button className={btnGhost} onClick={() => setEditId(null)}><X className="h-3 w-3" /></button></span></td>
                  </>
                ) : confirmDel === p.id ? (
                  <><td /><td /><td /><td className="px-4 py-2.5"><ConfirmDelete onConfirm={() => { deleteMut.mutate(p.id); setConfirmDel(null) }} onCancel={() => setConfirmDel(null)} /></td></>
                ) : (
                  <>
                    <td className="px-4 py-2.5 text-right text-amber-400">£{Number(p.base_price).toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-right text-gray-300">{Number(p.high_quality_multiplier).toFixed(3)}</td>
                    <td className="px-4 py-2.5 text-right text-gray-300">{Number(p.exclusive_multiplier).toFixed(3)}</td>
                    <td className="px-4 py-2.5"><span className="flex gap-1"><button className={btnGhost} onClick={() => { setEditId(p.id); setEditForm({ base_price: String(p.base_price), high_quality_multiplier: String(p.high_quality_multiplier), exclusive_multiplier: String(p.exclusive_multiplier) }) }}><Pencil className="h-3 w-3" /></button><button className={btnDanger} onClick={() => setConfirmDel(p.id)}><Trash2 className="h-3 w-3" /></button></span></td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// TERRITORIES TAB
// ═════════════════════════════════════════════════════════════════════════════
function TerritoriesTab({ push }: { push: (k: ToastKind, m: string) => void }) {
  const qc = useQueryClient()
  const { data: territories = [], isLoading } = useQuery({ queryKey: ['lm-territories'], queryFn: () => lm.listTerritories().then(r => r.data) })
  const [form, setForm] = useState({ name: '', region_code: '', country: 'GB' })
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ name: '', region_code: '', country: '' })
  const [confirmDel, setConfirmDel] = useState<string | null>(null)

  const createMut = useMutation({
    mutationFn: () => lm.createTerritory(form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-territories'] }); setForm({ name: '', region_code: '', country: 'GB' }); push('ok', 'Territory created') },
    onError: () => push('err', 'Failed to create territory'),
  })
  const updateMut = useMutation({
    mutationFn: (id: string) => lm.updateTerritory(id, editForm),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-territories'] }); setEditId(null); push('ok', 'Territory updated') },
    onError: () => push('err', 'Failed to update territory'),
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => lm.deleteTerritory(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-territories'] }); push('ok', 'Territory deleted') },
    onError: () => push('err', 'Failed to delete'),
  })

  return (
    <div>
      <div className="mb-5 rounded-xl border border-gray-800 bg-gray-900 p-4">
        <p className="mb-3 text-sm font-semibold text-white">New Territory</p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div><label className={lbl}>Name *</label><input className={inp} value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="e.g. London Central" /></div>
          <div><label className={lbl}>Region Code *</label><input className={inp} value={form.region_code} onChange={e => setForm(f => ({ ...f, region_code: e.target.value }))} placeholder="e.g. EC1" /></div>
          <div><label className={lbl}>Country</label><input className={inp} value={form.country} onChange={e => setForm(f => ({ ...f, country: e.target.value }))} /></div>
        </div>
        <button className={`${btnPrimary} mt-3`} disabled={!form.name || !form.region_code || createMut.isPending} onClick={() => createMut.mutate()}><Plus className="h-3.5 w-3.5" />Add Territory</button>
      </div>
      <div className="rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-900 text-xs text-gray-400"><tr><th className="px-4 py-2.5 text-left">Name</th><th className="px-4 py-2.5 text-left">Region Code</th><th className="px-4 py-2.5 text-left">Country</th><th className="px-4 py-2.5 text-left">Actions</th></tr></thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-500">Loading…</td></tr>}
            {!isLoading && territories.length === 0 && <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-500">No territories yet.</td></tr>}
            {territories.map(t => (
              <tr key={t.id} className="bg-gray-950 hover:bg-gray-900">
                {editId === t.id ? (
                  <>
                    <td className="px-4 py-2.5"><input className={inp} value={editForm.name} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} /></td>
                    <td className="px-4 py-2.5"><input className={inp} value={editForm.region_code} onChange={e => setEditForm(f => ({ ...f, region_code: e.target.value }))} /></td>
                    <td className="px-4 py-2.5"><input className={inp} value={editForm.country} onChange={e => setEditForm(f => ({ ...f, country: e.target.value }))} /></td>
                    <td className="px-4 py-2.5"><span className="flex gap-1"><button className={btnPrimary} onClick={() => updateMut.mutate(t.id)}><Check className="h-3 w-3" /></button><button className={btnGhost} onClick={() => setEditId(null)}><X className="h-3 w-3" /></button></span></td>
                  </>
                ) : confirmDel === t.id ? (
                  <><td /><td /><td /><td className="px-4 py-2.5"><ConfirmDelete onConfirm={() => { deleteMut.mutate(t.id); setConfirmDel(null) }} onCancel={() => setConfirmDel(null)} /></td></>
                ) : (
                  <>
                    <td className="px-4 py-2.5 text-white">{t.name}</td>
                    <td className="px-4 py-2.5 text-gray-300">{t.region_code}</td>
                    <td className="px-4 py-2.5 text-gray-300">{t.country}</td>
                    <td className="px-4 py-2.5"><span className="flex gap-1"><button className={btnGhost} onClick={() => { setEditId(t.id); setEditForm({ name: t.name, region_code: t.region_code, country: t.country }) }}><Pencil className="h-3 w-3" /></button><button className={btnDanger} onClick={() => setConfirmDel(t.id)}><Trash2 className="h-3 w-3" /></button></span></td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// QUALITY RULES TAB
// ═════════════════════════════════════════════════════════════════════════════
function QualityRulesTab({ push }: { push: (k: ToastKind, m: string) => void }) {
  const qc = useQueryClient()
  const { data: cats = [] } = useQuery({ queryKey: ['lm-categories'], queryFn: () => lm.listCategories().then(r => r.data) })
  const { data: rules = [], isLoading } = useQuery({ queryKey: ['lm-quality-rules'], queryFn: () => lm.listQualityRules().then(r => r.data) })
  const catMap = Object.fromEntries(cats.map(c => [c.id, c.name]))

  const emptyForm = { name: '', min_ai_score: '0', max_age_days: '30', requires_phone: false, requires_email: false, apply_to_category: '' }
  const [form, setForm] = useState(emptyForm)
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState(emptyForm)
  const [confirmDel, setConfirmDel] = useState<string | null>(null)

  const createMut = useMutation({
    mutationFn: () => lm.createQualityRule({ name: form.name, min_ai_score: parseInt(form.min_ai_score), max_age_days: parseInt(form.max_age_days), requires_phone: form.requires_phone, requires_email: form.requires_email, apply_to_category: form.apply_to_category || null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-quality-rules'] }); setForm(emptyForm); push('ok', 'Quality rule created') },
    onError: () => push('err', 'Failed to create rule'),
  })
  const updateMut = useMutation({
    mutationFn: (id: string) => lm.updateQualityRule(id, { name: editForm.name, min_ai_score: parseInt(editForm.min_ai_score), max_age_days: parseInt(editForm.max_age_days), requires_phone: editForm.requires_phone, requires_email: editForm.requires_email, apply_to_category: editForm.apply_to_category || null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-quality-rules'] }); setEditId(null); push('ok', 'Rule updated') },
    onError: () => push('err', 'Failed to update rule'),
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => lm.deleteQualityRule(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-quality-rules'] }); push('ok', 'Rule deleted') },
    onError: () => push('err', 'Failed to delete rule'),
  })

  const FormRow = ({ f, onChange }: { f: typeof emptyForm; onChange: (patch: Partial<typeof emptyForm>) => void }) => (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      <div className="col-span-2 sm:col-span-1"><label className={lbl}>Name *</label><input className={inp} value={f.name} onChange={e => onChange({ name: e.target.value })} /></div>
      <div><label className={lbl}>Min AI Score</label><input className={inp} type="number" min={0} max={100} value={f.min_ai_score} onChange={e => onChange({ min_ai_score: e.target.value })} /></div>
      <div><label className={lbl}>Max Age (days)</label><input className={inp} type="number" min={1} value={f.max_age_days} onChange={e => onChange({ max_age_days: e.target.value })} /></div>
      <div><label className={lbl}>Category</label>
        <select className={inp} value={f.apply_to_category} onChange={e => onChange({ apply_to_category: e.target.value })}>
          <option value="">All</option>{cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>
      <div className="flex flex-col gap-1.5 pt-4">
        <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
          <input type="checkbox" checked={f.requires_phone} onChange={e => onChange({ requires_phone: e.target.checked })} className="accent-amber-500" />Phone
        </label>
        <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
          <input type="checkbox" checked={f.requires_email} onChange={e => onChange({ requires_email: e.target.checked })} className="accent-amber-500" />Email
        </label>
      </div>
    </div>
  )

  return (
    <div>
      <div className="mb-5 rounded-xl border border-gray-800 bg-gray-900 p-4">
        <p className="mb-3 text-sm font-semibold text-white">New Quality Rule</p>
        <FormRow f={form} onChange={patch => setForm(f => ({ ...f, ...patch }))} />
        <button className={`${btnPrimary} mt-3`} disabled={!form.name || createMut.isPending} onClick={() => createMut.mutate()}><Plus className="h-3.5 w-3.5" />Add Rule</button>
      </div>
      <div className="space-y-2">
        {isLoading && <p className="py-6 text-center text-gray-500 text-sm">Loading…</p>}
        {!isLoading && rules.length === 0 && <p className="py-6 text-center text-gray-500 text-sm">No quality rules yet.</p>}
        {rules.map(r => (
          <div key={r.id} className="rounded-xl border border-gray-800 bg-gray-950 p-4">
            {editId === r.id ? (
              <>
                <FormRow f={editForm} onChange={patch => setEditForm(f => ({ ...f, ...patch }))} />
                <span className="mt-3 flex gap-2"><button className={btnPrimary} onClick={() => updateMut.mutate(r.id)}><Check className="h-3 w-3" />Save</button><button className={btnGhost} onClick={() => setEditId(null)}><X className="h-3 w-3" />Cancel</button></span>
              </>
            ) : (
              <div className="flex items-center justify-between gap-4">
                <div className="flex flex-wrap gap-4 text-sm">
                  <span className="font-semibold text-white">{r.name}</span>
                  <span className="text-gray-400">Min score: <span className="text-amber-400">{r.min_ai_score}</span></span>
                  <span className="text-gray-400">Max age: <span className="text-amber-400">{r.max_age_days}d</span></span>
                  <span className="text-gray-400">Category: <span className="text-gray-200">{r.apply_to_category ? (catMap[r.apply_to_category] ?? r.apply_to_category) : 'All'}</span></span>
                  {r.requires_phone && <span className="rounded bg-blue-900/40 px-1.5 py-0.5 text-xs text-blue-300">Phone required</span>}
                  {r.requires_email && <span className="rounded bg-purple-900/40 px-1.5 py-0.5 text-xs text-purple-300">Email required</span>}
                </div>
                {confirmDel === r.id ? (
                  <ConfirmDelete onConfirm={() => { deleteMut.mutate(r.id); setConfirmDel(null) }} onCancel={() => setConfirmDel(null)} />
                ) : (
                  <span className="flex gap-1">
                    <button className={btnGhost} onClick={() => { setEditId(r.id); setEditForm({ name: r.name, min_ai_score: String(r.min_ai_score), max_age_days: String(r.max_age_days), requires_phone: r.requires_phone, requires_email: r.requires_email, apply_to_category: r.apply_to_category ?? '' }) }}><Pencil className="h-3 w-3" /></button>
                    <button className={btnDanger} onClick={() => setConfirmDel(r.id)}><Trash2 className="h-3 w-3" /></button>
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// ASSIGNMENT RULES TAB
// ═════════════════════════════════════════════════════════════════════════════
function AssignmentRulesTab({ push }: { push: (k: ToastKind, m: string) => void }) {
  const qc = useQueryClient()
  const { data: cats = [] } = useQuery({ queryKey: ['lm-categories'], queryFn: () => lm.listCategories().then(r => r.data) })
  const { data: territories = [] } = useQuery({ queryKey: ['lm-territories'], queryFn: () => lm.listTerritories().then(r => r.data) })
  const { data: rules = [], isLoading } = useQuery({ queryKey: ['lm-assignment-rules'], queryFn: () => lm.listAssignmentRules().then(r => r.data) })
  const catMap = Object.fromEntries(cats.map(c => [c.id, c.name]))
  const terMap = Object.fromEntries(territories.map(t => [t.id, t.name]))

  const empty = { rule_name: '', category_id: '', territory_id: '', min_subscription_level: '0', priority_weight: '1' }
  const [form, setForm] = useState(empty)
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState(empty)
  const [confirmDel, setConfirmDel] = useState<string | null>(null)

  const buildPayload = (f: typeof empty) => ({ rule_name: f.rule_name, category_id: f.category_id || null, territory_id: f.territory_id || null, min_subscription_level: parseInt(f.min_subscription_level), priority_weight: parseInt(f.priority_weight) })

  const createMut = useMutation({ mutationFn: () => lm.createAssignmentRule(buildPayload(form)), onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-assignment-rules'] }); setForm(empty); push('ok', 'Assignment rule created') }, onError: () => push('err', 'Failed') })
  const updateMut = useMutation({ mutationFn: (id: string) => lm.updateAssignmentRule(id, buildPayload(editForm)), onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-assignment-rules'] }); setEditId(null); push('ok', 'Rule updated') }, onError: () => push('err', 'Failed') })
  const deleteMut = useMutation({ mutationFn: (id: string) => lm.deleteAssignmentRule(id), onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-assignment-rules'] }); push('ok', 'Rule deleted') }, onError: () => push('err', 'Failed') })

  const FormRow = ({ f, onChange }: { f: typeof empty; onChange: (p: Partial<typeof empty>) => void }) => (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <div className="col-span-2 sm:col-span-1"><label className={lbl}>Rule Name *</label><input className={inp} value={f.rule_name} onChange={e => onChange({ rule_name: e.target.value })} /></div>
      <div><label className={lbl}>Category</label><select className={inp} value={f.category_id} onChange={e => onChange({ category_id: e.target.value })}><option value="">Any</option>{cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
      <div><label className={lbl}>Territory</label><select className={inp} value={f.territory_id} onChange={e => onChange({ territory_id: e.target.value })}><option value="">Any</option>{territories.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</select></div>
      <div><label className={lbl}>Min Sub Level</label><input className={inp} type="number" min={0} value={f.min_subscription_level} onChange={e => onChange({ min_subscription_level: e.target.value })} /></div>
      <div><label className={lbl}>Priority Weight</label><input className={inp} type="number" min={1} value={f.priority_weight} onChange={e => onChange({ priority_weight: e.target.value })} /></div>
    </div>
  )

  return (
    <div>
      <div className="mb-4 rounded-lg border border-amber-800/30 bg-amber-950/20 p-3 text-xs text-amber-400">
        Priority Formula: <span className="font-mono">tenant.subscription_level × rule.priority_weight + ai_score</span>
      </div>
      <div className="mb-5 rounded-xl border border-gray-800 bg-gray-900 p-4">
        <p className="mb-3 text-sm font-semibold text-white">New Assignment Rule</p>
        <FormRow f={form} onChange={p => setForm(f => ({ ...f, ...p }))} />
        <button className={`${btnPrimary} mt-3`} disabled={!form.rule_name || createMut.isPending} onClick={() => createMut.mutate()}><Plus className="h-3.5 w-3.5" />Add Rule</button>
      </div>
      <div className="space-y-2">
        {isLoading && <p className="py-6 text-center text-gray-500 text-sm">Loading…</p>}
        {!isLoading && rules.length === 0 && <p className="py-6 text-center text-gray-500 text-sm">No assignment rules yet.</p>}
        {rules.map(r => (
          <div key={r.id} className="rounded-xl border border-gray-800 bg-gray-950 p-4">
            {editId === r.id ? (
              <>
                <FormRow f={editForm} onChange={p => setEditForm(f => ({ ...f, ...p }))} />
                <span className="mt-3 flex gap-2"><button className={btnPrimary} onClick={() => updateMut.mutate(r.id)}><Check className="h-3 w-3" />Save</button><button className={btnGhost} onClick={() => setEditId(null)}><X className="h-3 w-3" />Cancel</button></span>
              </>
            ) : (
              <div className="flex items-center justify-between gap-4">
                <div className="flex flex-wrap gap-4 text-sm">
                  <span className="font-semibold text-white">{r.rule_name}</span>
                  <span className="text-gray-400">Cat: <span className="text-gray-200">{r.category_id ? (catMap[r.category_id] ?? r.category_id) : 'Any'}</span></span>
                  <span className="text-gray-400">Territory: <span className="text-gray-200">{r.territory_id ? (terMap[r.territory_id] ?? r.territory_id) : 'Any'}</span></span>
                  <span className="text-gray-400">Min level: <span className="text-amber-400">{r.min_subscription_level}</span></span>
                  <span className="text-gray-400">Weight: <span className="text-amber-400">{r.priority_weight}</span></span>
                </div>
                {confirmDel === r.id ? (
                  <ConfirmDelete onConfirm={() => { deleteMut.mutate(r.id); setConfirmDel(null) }} onCancel={() => setConfirmDel(null)} />
                ) : (
                  <span className="flex gap-1">
                    <button className={btnGhost} onClick={() => { setEditId(r.id); setEditForm({ rule_name: r.rule_name, category_id: r.category_id ?? '', territory_id: r.territory_id ?? '', min_subscription_level: String(r.min_subscription_level), priority_weight: String(r.priority_weight) }) }}><Pencil className="h-3 w-3" /></button>
                    <button className={btnDanger} onClick={() => setConfirmDel(r.id)}><Trash2 className="h-3 w-3" /></button>
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// INVENTORY TAB
// ═════════════════════════════════════════════════════════════════════════════
function InventoryTab({ push }: { push: (k: ToastKind, m: string) => void }) {
  const qc = useQueryClient()
  const { data: cats = [] } = useQuery({ queryKey: ['lm-categories'], queryFn: () => lm.listCategories().then(r => r.data) })
  const { data: territories = [] } = useQuery({ queryKey: ['lm-territories'], queryFn: () => lm.listTerritories().then(r => r.data) })

  const [statusFilter, setStatusFilter] = useState<LMStatus | ''>('')
  const [catFilter, setCatFilter] = useState('')
  const [terFilter, setTerFilter] = useState('')

  const { data: items = [], isLoading, refetch } = useQuery({
    queryKey: ['lm-inventory', statusFilter, catFilter, terFilter],
    queryFn: () => lm.listInventory({ status: statusFilter || undefined, category_id: catFilter || undefined, territory_id: terFilter || undefined }).then(r => r.data),
  })

  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [assignForm, setAssignForm] = useState<{ id: string; tenant_id: string; status: LMStatus } | null>(null)
  const [editItem, setEditItem] = useState<{ id: string; price: string; exclusivity: string; status: LMStatus } | null>(null)
  const [confirmDel, setConfirmDel] = useState<string | null>(null)

  const assignMut = useMutation({
    mutationFn: () => lm.assignItem(assignForm!.id, { tenant_id: assignForm!.tenant_id, status: assignForm!.status }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-inventory'] }); setAssignForm(null); push('ok', 'Lead assigned') },
    onError: () => push('err', 'Assignment failed'),
  })
  const releaseMut = useMutation({
    mutationFn: (id: string) => lm.releaseItem(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-inventory'] }); push('ok', 'Lead released') },
    onError: () => push('err', 'Release failed'),
  })
  const soldMut = useMutation({
    mutationFn: (id: string) => lm.markSold(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-inventory'] }); push('ok', 'Marked as sold') },
    onError: () => push('err', 'Failed'),
  })
  const distributeMut = useMutation({
    mutationFn: (id: string) => lm.distributeItem(id),
    onSuccess: (res) => { qc.invalidateQueries({ queryKey: ['lm-inventory'] }); push('ok', `Distributed → tenant ${res.data.assigned_tenant_id.slice(0, 8)}… (priority ${res.data.priority_score})`) },
    onError: () => push('err', 'No eligible tenant found'),
  })
  const updateMut = useMutation({
    mutationFn: (id: string) => lm.updateInventoryItem(id, { price: parseFloat(editItem!.price), exclusivity: editItem!.exclusivity, status: editItem!.status }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-inventory'] }); setEditItem(null); push('ok', 'Updated') },
    onError: () => push('err', 'Update failed'),
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => lm.deleteInventoryItem(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['lm-inventory'] }); push('ok', 'Deleted') },
    onError: () => push('err', 'Delete failed'),
  })

  return (
    <div>
      {/* Filters */}
      <div className="mb-4 flex flex-wrap gap-3">
        <select className={`${inp} w-auto`} value={statusFilter} onChange={e => setStatusFilter(e.target.value as LMStatus | '')}>
          <option value="">All Statuses</option>
          {(['available', 'reserved', 'sold', 'expired'] as LMStatus[]).map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className={`${inp} w-auto`} value={catFilter} onChange={e => setCatFilter(e.target.value)}>
          <option value="">All Categories</option>
          {cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select className={`${inp} w-auto`} value={terFilter} onChange={e => setTerFilter(e.target.value)}>
          <option value="">All Territories</option>
          {territories.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
      </div>

      {/* Assign modal */}
      {assignForm && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-5">
            <p className="mb-3 text-sm font-semibold text-white">Assign Lead</p>
            <div className="mb-3"><label className={lbl}>Tenant ID *</label><input className={inp} value={assignForm.tenant_id} onChange={e => setAssignForm(f => f && { ...f, tenant_id: e.target.value })} placeholder="UUID of tenant" /></div>
            <div className="mb-4"><label className={lbl}>Status</label>
              <select className={inp} value={assignForm.status} onChange={e => setAssignForm(f => f && { ...f, status: e.target.value as LMStatus })}>
                <option value="reserved">reserved</option><option value="sold">sold</option>
              </select>
            </div>
            <div className="flex gap-2"><button className={btnPrimary} disabled={!assignForm.tenant_id || assignMut.isPending} onClick={() => assignMut.mutate()}><UserCheck className="h-3 w-3" />Assign</button><button className={btnGhost} onClick={() => setAssignForm(null)}>Cancel</button></div>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-gray-800 overflow-x-auto">
        <table className="w-full min-w-[900px] text-sm">
          <thead className="bg-gray-900 text-xs text-gray-400">
            <tr>
              <th className="px-3 py-2.5 text-left">ID</th>
              <th className="px-3 py-2.5 text-left">Category</th>
              <th className="px-3 py-2.5 text-left">Territory</th>
              <th className="px-3 py-2.5 text-right">AI Score</th>
              <th className="px-3 py-2.5 text-right">Price</th>
              <th className="px-3 py-2.5 text-left">Exclusivity</th>
              <th className="px-3 py-2.5 text-left">Status</th>
              <th className="px-3 py-2.5 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && <tr><td colSpan={8} className="px-3 py-8 text-center text-gray-500">Loading…</td></tr>}
            {!isLoading && items.length === 0 && <tr><td colSpan={8} className="px-3 py-8 text-center text-gray-500">No leads in the marketplace yet.</td></tr>}
            {items.map(item => (
              <>
                <tr key={item.id} className={`bg-gray-950 hover:bg-gray-900 ${expandedId === item.id ? 'border-b-0' : ''}`}>
                  <td className="px-3 py-2.5 font-mono text-xs text-gray-500">
                    <button onClick={() => setExpandedId(expandedId === item.id ? null : item.id)} className="flex items-center gap-1 hover:text-white">
                      {item.id.slice(0, 8)}… {expandedId === item.id ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                    </button>
                  </td>
                  <td className="px-3 py-2.5 text-white">{item.category_name ?? item.category_id.slice(0, 8)}</td>
                  <td className="px-3 py-2.5 text-gray-300">{item.territory_name ?? item.territory_id.slice(0, 8)}</td>
                  <td className="px-3 py-2.5 text-right">
                    <span className={`font-semibold ${item.ai_score >= 70 ? 'text-emerald-400' : item.ai_score >= 40 ? 'text-amber-400' : 'text-gray-400'}`}>{item.ai_score}</span>
                  </td>
                  <td className="px-3 py-2.5 text-right text-amber-400">£{Number(item.price).toFixed(2)}</td>
                  <td className="px-3 py-2.5 text-gray-300 capitalize">{item.exclusivity}</td>
                  <td className="px-3 py-2.5"><StatusPill status={item.status} /></td>
                  <td className="px-3 py-2.5">
                    {editItem?.id === item.id ? (
                      <span className="flex gap-1">
                        <button className={btnPrimary} onClick={() => updateMut.mutate(item.id)}><Check className="h-3 w-3" /></button>
                        <button className={btnGhost} onClick={() => setEditItem(null)}><X className="h-3 w-3" /></button>
                      </span>
                    ) : confirmDel === item.id ? (
                      <ConfirmDelete onConfirm={() => { deleteMut.mutate(item.id); setConfirmDel(null) }} onCancel={() => setConfirmDel(null)} />
                    ) : (
                      <span className="flex flex-wrap gap-1">
                        <button title="Expand" className={btnGhost} onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}><Eye className="h-3 w-3" /></button>
                        <button title="Edit" className={btnGhost} onClick={() => setEditItem({ id: item.id, price: String(item.price), exclusivity: item.exclusivity, status: item.status as LMStatus })}><Pencil className="h-3 w-3" /></button>
                        {item.status === 'available' && <button title="Assign to tenant" className={btnGhost} onClick={() => setAssignForm({ id: item.id, tenant_id: '', status: 'reserved' })}><UserCheck className="h-3 w-3" /></button>}
                        {item.status === 'available' && <button title="Auto-distribute" className={btnGhost} onClick={() => distributeMut.mutate(item.id)}><Zap className="h-3 w-3" /></button>}
                        {item.status === 'reserved' && <button title="Release" className={btnGhost} onClick={() => releaseMut.mutate(item.id)}><Undo2 className="h-3 w-3" /></button>}
                        {item.status === 'reserved' && <button title="Mark sold" className={btnGhost} onClick={() => soldMut.mutate(item.id)}><BadgeCheck className="h-3 w-3" /></button>}
                        <button title="Delete" className={btnDanger} onClick={() => setConfirmDel(item.id)}><Trash2 className="h-3 w-3" /></button>
                      </span>
                    )}
                  </td>
                </tr>
                {expandedId === item.id && (
                  <tr key={`${item.id}-detail`} className="bg-gray-900">
                    <td colSpan={8} className="px-4 py-3">
                      {editItem?.id === item.id ? (
                        <div className="grid grid-cols-3 gap-3">
                          <div><label className={lbl}>Price (£)</label><input className={inp} type="number" step="0.01" value={editItem.price} onChange={e => setEditItem(f => f && { ...f, price: e.target.value })} /></div>
                          <div><label className={lbl}>Exclusivity</label>
                            <select className={inp} value={editItem.exclusivity} onChange={e => setEditItem(f => f && { ...f, exclusivity: e.target.value })}>
                              <option>shared</option><option>semi-exclusive</option><option>exclusive</option>
                            </select>
                          </div>
                          <div><label className={lbl}>Status</label>
                            <select className={inp} value={editItem.status} onChange={e => setEditItem(f => f && { ...f, status: e.target.value as LMStatus })}>
                              <option>available</option><option>reserved</option><option>sold</option><option>expired</option>
                            </select>
                          </div>
                        </div>
                      ) : (
                        <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-gray-400 sm:grid-cols-4">
                          <div><span className="text-gray-500">Lead ID:</span> <span className="font-mono text-gray-300">{item.lead_id}</span></div>
                          <div><span className="text-gray-500">Marketplace ID:</span> <span className="font-mono text-gray-300">{item.id}</span></div>
                          <div><span className="text-gray-500">Assigned tenant:</span> <span className="font-mono text-gray-300">{item.assigned_tenant_id ?? '—'}</span></div>
                          <div><span className="text-gray-500">Created:</span> <span className="text-gray-300">{new Date(item.created_at).toLocaleString()}</span></div>
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-right text-xs text-gray-600">{items.length} leads shown</p>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// ROOT PAGE
// ═════════════════════════════════════════════════════════════════════════════
export default function LeadMarketplacePage() {
  const [tab, setTab] = useState<TabKey>('categories')
  const { toasts, push } = useToast()

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      <ToastStack toasts={toasts} />

      <div className="mb-6">
        <h1 className="text-2xl font-bold">Lead Marketplace</h1>
        <p className="mt-1 text-sm text-gray-400">
          Manage categories, pricing, territories, quality rules, assignment rules, and the full marketplace inventory.
        </p>
      </div>

      {/* Tab bar */}
      <div className="mb-6 flex flex-wrap gap-1 rounded-xl border border-gray-800 bg-gray-900 p-1">
        {TABS.map(t => {
          const Icon = t.icon
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition
                ${tab === t.key ? 'bg-amber-500 text-black' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}
            >
              <Icon className="h-3.5 w-3.5" />{t.label}
            </button>
          )
        })}
      </div>

      {tab === 'categories'        && <CategoriesTab push={push} />}
      {tab === 'pricing'           && <PricingTab push={push} />}
      {tab === 'territories'       && <TerritoriesTab push={push} />}
      {tab === 'quality-rules'     && <QualityRulesTab push={push} />}
      {tab === 'assignment-rules'  && <AssignmentRulesTab push={push} />}
      {tab === 'inventory'         && <InventoryTab push={push} />}
    </div>
  )
}
