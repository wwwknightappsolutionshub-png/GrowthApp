'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ShoppingBag, Zap, UserCheck, XCircle, Trash2, Search } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface MarketplaceItem { id: string; lead_id: string; ai_score: number; price: number; exclusivity: string; status: string; assigned_tenant_id: string | null; created_at: string }

const STATUS_COLORS: Record<string, string> = { available: 'bg-green-900/30 text-green-400', reserved: 'bg-yellow-900/30 text-yellow-400', sold: 'bg-blue-900/30 text-blue-400', expired: 'bg-gray-700 text-gray-400' }

export default function MarketplacePage() {
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')
  const [assignId, setAssignId] = useState<string | null>(null)
  const [tenantInput, setTenantInput] = useState('')
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [toast, setToast] = useState('')

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['admin', 'marketplace', statusFilter],
    queryFn: () => adminApi.listMarketplace({ status: statusFilter || undefined, limit: 200 }).then(r => r.data as MarketplaceItem[]),
  })

  const assignMut = useMutation({
    mutationFn: () => adminApi.assignMarketplaceItem(assignId!, tenantInput),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'marketplace'] }); setAssignId(null); showToast('Lead assigned') },
  })
  const releaseMut = useMutation({
    mutationFn: (id: string) => adminApi.releaseMarketplaceItem(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'marketplace'] }); showToast('Lead released') },
  })
  const distributeMut = useMutation({
    mutationFn: (id: string) => adminApi.distributeMarketplaceItem(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'marketplace'] }); showToast('Distribution complete') },
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => adminApi.deleteMarketplaceItem(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'marketplace'] }); setDeleteId(null) },
  })

  const SCORE_COLOR = (s: number) => s >= 80 ? 'text-green-400 bg-green-900/30' : s >= 50 ? 'text-amber-400 bg-amber-900/30' : 'text-red-400 bg-red-900/30'

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      {toast && <div className="fixed top-4 right-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white shadow-lg">{toast}</div>}

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><ShoppingBag className="h-6 w-6 text-amber-400" /> Lead Marketplace</h1>
          <p className="text-sm text-gray-400 mt-1">Manage lead inventory, pricing and distribution to tenants</p>
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500">
          <option value="">All Status</option>
          {['available', 'reserved', 'sold', 'expired'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Stats */}
      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {(['available', 'reserved', 'sold', 'expired'] as const).map(status => {
          const count = (items as MarketplaceItem[]).filter(i => i.status === status).length
          return (
            <div key={status} className="rounded-xl border border-gray-800 bg-gray-900 p-4">
              <p className="text-xs text-gray-400 capitalize">{status}</p>
              <p className="text-2xl font-bold text-white mt-1">{count}</p>
            </div>
          )
        })}
      </div>

      {isLoading ? <div className="text-gray-400">Loading...</div> : (
        <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wider">
              <tr>{['Lead ID', 'AI Score', 'Price', 'Exclusivity', 'Status', 'Assigned To', 'Actions'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {(items as MarketplaceItem[]).length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No leads in marketplace</td></tr>}
              {(items as MarketplaceItem[]).map(item => (
                <tr key={item.id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-300">{item.lead_id.slice(0, 8)}…</td>
                  <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${SCORE_COLOR(item.ai_score)}`}>{item.ai_score}</span></td>
                  <td className="px-4 py-3 text-amber-300 font-semibold">£{Number(item.price).toFixed(2)}</td>
                  <td className="px-4 py-3"><span className="rounded-full bg-gray-700 px-2 py-0.5 text-xs">{item.exclusivity}</span></td>
                  <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_COLORS[item.status] ?? 'bg-gray-700 text-gray-400'}`}>{item.status}</span></td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-400">{item.assigned_tenant_id ? item.assigned_tenant_id.slice(0, 8) + '…' : '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {item.status === 'available' && <>
                        <button onClick={() => { setAssignId(item.id); setTenantInput('') }} title="Assign" className="rounded p-1.5 text-gray-400 hover:bg-blue-900 hover:text-blue-400"><UserCheck className="h-4 w-4" /></button>
                        <button onClick={() => distributeMut.mutate(item.id)} title="Auto-distribute" disabled={distributeMut.isPending} className="rounded p-1.5 text-gray-400 hover:bg-amber-900 hover:text-amber-400 disabled:opacity-40"><Zap className="h-4 w-4" /></button>
                      </>}
                      {item.status === 'reserved' && <button onClick={() => releaseMut.mutate(item.id)} title="Release" disabled={releaseMut.isPending} className="rounded p-1.5 text-gray-400 hover:bg-yellow-900 hover:text-yellow-400"><XCircle className="h-4 w-4" /></button>}
                      <button onClick={() => setDeleteId(item.id)} className="rounded p-1.5 text-gray-400 hover:bg-red-900 hover:text-red-400"><Trash2 className="h-4 w-4" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {assignId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-4 text-lg font-semibold flex items-center gap-2"><UserCheck className="h-5 w-5 text-amber-400" /> Assign Lead</h2>
            <label className="mb-1 block text-xs text-gray-400">Tenant ID</label>
            <input value={tenantInput} onChange={e => setTenantInput(e.target.value)} placeholder="UUID of tenant" className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500" />
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setAssignId(null)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => assignMut.mutate()} disabled={!tenantInput.trim() || assignMut.isPending} className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-50">{assignMut.isPending ? 'Assigning…' : 'Assign'}</button>
            </div>
          </div>
        </div>
      )}

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-2 text-lg font-semibold">Remove from Marketplace</h2>
            <p className="mb-5 text-sm text-gray-400">This action cannot be undone.</p>
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
