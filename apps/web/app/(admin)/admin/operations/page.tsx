'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Activity, Shield, Monitor, AlertTriangle, XCircle, Plus } from 'lucide-react'
import { adminApi, type SystemLog, type BlockedIP } from '@/lib/api-client'

type Tab = 'logs' | 'monitoring' | 'security'

const LEVEL_COLORS: Record<string, string> = {
  error: 'bg-red-900/30 text-red-400',
  warning: 'bg-yellow-900/30 text-yellow-400',
  info: 'bg-blue-900/30 text-blue-400',
  debug: 'bg-gray-700 text-gray-400',
}

export default function OperationsPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('logs')
  const [levelFilter, setLevelFilter] = useState('')
  const [blockIpForm, setBlockIpForm] = useState({ ip_address: '', reason: '' })
  const [showBlockModal, setShowBlockModal] = useState(false)
  const [toast, setToast] = useState('')

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const { data: logs = [] } = useQuery({
    queryKey: ['admin', 'ops', 'logs', levelFilter],
    queryFn: () => adminApi.listSystemLogs({ level: levelFilter || undefined, limit: 200 }).then(r => r.data),
  })
  const { data: monitoring } = useQuery({ queryKey: ['admin', 'ops', 'monitoring'], queryFn: () => adminApi.getMonitoring().then(r => r.data as Record<string, unknown>) })
  const { data: security } = useQuery({ queryKey: ['admin', 'ops', 'security'], queryFn: () => adminApi.getSecurity().then(r => r.data as { blocked_ips: BlockedIP[] }) })

  const blockMut = useMutation({
    mutationFn: () => adminApi.blockIP(blockIpForm),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ops', 'security'] }); setShowBlockModal(false); showToast('IP blocked') },
  })
  const unblockMut = useMutation({
    mutationFn: (ip: string) => adminApi.unblockIP(ip),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'ops', 'security'] }); showToast('IP unblocked') },
  })

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-white">
      {toast && <div className="fixed top-4 right-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white shadow-lg">{toast}</div>}

      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2"><Activity className="h-6 w-6 text-amber-400" /> Operations & Compliance</h1>
        <p className="text-sm text-gray-400 mt-1">System logs, health monitoring and security controls</p>
      </div>

      <div className="mb-6 flex gap-1 rounded-xl border border-gray-800 bg-gray-900 p-1 w-fit">
        {([['logs', 'System Logs', Activity], ['monitoring', 'Monitoring', Monitor], ['security', 'Security', Shield]] as [Tab, string, React.ElementType][]).map(([key, label, Icon]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${tab === key ? 'bg-amber-500 text-black' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
            <Icon className="h-4 w-4" /> {label}
          </button>
        ))}
      </div>

      {tab === 'logs' && (
        <>
          <div className="mb-4 flex items-center gap-3">
            <select value={levelFilter} onChange={e => setLevelFilter(e.target.value)} className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-amber-500">
              <option value="">All Levels</option>
              {['info', 'warning', 'error', 'debug'].map(l => <option key={l} value={l}>{l}</option>)}
            </select>
            <span className="text-sm text-gray-400">{(logs as SystemLog[]).length} records</span>
          </div>
          <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wider">
                <tr>{['Level', 'Service', 'Message', 'Time'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {(logs as SystemLog[]).length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-500">No logs found</td></tr>}
                {(logs as SystemLog[]).map(l => (
                  <tr key={l.id} className="hover:bg-gray-800/50">
                    <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${LEVEL_COLORS[l.level] ?? 'bg-gray-700 text-gray-400'}`}>{l.level}</span></td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{l.service ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-300 max-w-md truncate">{l.message}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{new Date(l.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'monitoring' && monitoring && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Object.entries(monitoring).map(([key, val]) => (
            <div key={key} className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">{key.replace(/_/g, ' ')}</p>
              <p className="text-sm text-white font-medium break-all">{String(val)}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'security' && (
        <>
          <div className="mb-4 flex justify-end">
            <button onClick={() => { setBlockIpForm({ ip_address: '', reason: '' }); setShowBlockModal(true) }} className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500">
              <Plus className="h-4 w-4" /> Block IP
            </button>
          </div>
          <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-800 text-gray-400 text-xs uppercase tracking-wider">
                <tr>{['IP Address', 'Reason', 'Blocked At', 'Actions'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {(security?.blocked_ips ?? []).length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-500">No blocked IPs</td></tr>}
                {(security?.blocked_ips ?? []).map(ip => (
                  <tr key={ip.ip_address} className="hover:bg-gray-800/50">
                    <td className="px-4 py-3 font-mono text-amber-300">{ip.ip_address}</td>
                    <td className="px-4 py-3 text-gray-400">{ip.reason || '—'}</td>
                    <td className="px-4 py-3 text-gray-400">{new Date(ip.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      <button onClick={() => unblockMut.mutate(ip.ip_address)} disabled={unblockMut.isPending} className="rounded p-1.5 text-gray-400 hover:bg-green-900 hover:text-green-400">
                        <XCircle className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {showBlockModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="w-full max-w-sm rounded-xl border border-gray-700 bg-gray-900 p-6">
            <h2 className="mb-4 text-lg font-semibold flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-red-400" /> Block IP Address</h2>
            <div className="space-y-3">
              <div><label className="mb-1 block text-xs text-gray-400">IP Address</label><input value={blockIpForm.ip_address} onChange={e => setBlockIpForm(f => ({ ...f, ip_address: e.target.value }))} placeholder="e.g. 1.2.3.4" className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-red-500" /></div>
              <div><label className="mb-1 block text-xs text-gray-400">Reason</label><input value={blockIpForm.reason} onChange={e => setBlockIpForm(f => ({ ...f, reason: e.target.value }))} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white outline-none focus:border-red-500" /></div>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setShowBlockModal(false)} className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">Cancel</button>
              <button onClick={() => blockMut.mutate()} disabled={blockMut.isPending} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50">{blockMut.isPending ? 'Blocking…' : 'Block'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
