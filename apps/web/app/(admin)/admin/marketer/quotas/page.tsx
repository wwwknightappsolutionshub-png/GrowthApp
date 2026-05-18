'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Gauge, Save, X } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface QuotaRow {
  tenant_id: string
  tenant_name: string
  max_reports_per_month: number
  used_reports: number
  remaining: number
}

export default function MarketerQuotasPage() {
  const qc = useQueryClient()
  const [editing, setEditing] = useState<{ tenant_id: string; max: number } | null>(null)
  const [toast, setToast] = useState('')

  const { data = [], isLoading } = useQuery({
    queryKey: ['admin', 'marketer', 'quotas'],
    queryFn: () => adminApi.marketerListQuotas().then((r) => r.data as QuotaRow[]),
  })

  const saveMut = useMutation({
    mutationFn: (body: { tenant_id: string; max_reports_per_month: number }) =>
      adminApi.marketerSetQuota(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'marketer', 'quotas'] })
      setEditing(null)
      setToast('Quota updated')
      setTimeout(() => setToast(''), 2500)
    },
  })

  return (
    <div className="text-white">
      {toast && (
        <div className="fixed top-4 right-4 z-50 rounded-lg bg-green-700 px-4 py-2 text-sm font-medium shadow-lg">
          {toast}
        </div>
      )}

      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Gauge className="h-6 w-6 text-amber-400" /> Quota Configuration
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Per-tenant monthly Marketer Tools report quota. Set higher caps for premium plans.
        </p>
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-800/60 text-gray-400 text-xs uppercase tracking-wider">
            <tr>
              {['Tenant', 'Used', 'Max / month', 'Remaining', 'Actions'].map((h) => (
                <th key={h} className="px-4 py-3 text-left">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {!isLoading && data.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                  No tenants yet
                </td>
              </tr>
            )}
            {data.map((q) => (
              <tr key={q.tenant_id} className="hover:bg-gray-800/40">
                <td className="px-4 py-2 font-medium">{q.tenant_name}</td>
                <td className="px-4 py-2">{q.used_reports}</td>
                <td className="px-4 py-2">
                  {editing?.tenant_id === q.tenant_id ? (
                    <input
                      type="number"
                      min={0}
                      value={editing.max}
                      onChange={(e) =>
                        setEditing({ ...editing, max: parseInt(e.target.value || '0', 10) })
                      }
                      className="w-24 rounded bg-gray-800 border border-gray-700 px-2 py-1 text-sm"
                    />
                  ) : (
                    <span className="font-semibold">{q.max_reports_per_month}</span>
                  )}
                </td>
                <td
                  className={`px-4 py-2 ${q.remaining === 0 ? 'text-red-400' : 'text-green-400'}`}
                >
                  {q.remaining}
                </td>
                <td className="px-4 py-2">
                  {editing?.tenant_id === q.tenant_id ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() =>
                          saveMut.mutate({
                            tenant_id: editing.tenant_id,
                            max_reports_per_month: editing.max,
                          })
                        }
                        className="flex items-center gap-1 rounded bg-amber-500 px-2 py-1 text-xs font-semibold text-black hover:bg-amber-400"
                      >
                        <Save className="h-3.5 w-3.5" /> Save
                      </button>
                      <button
                        onClick={() => setEditing(null)}
                        className="flex items-center gap-1 rounded bg-gray-700 px-2 py-1 text-xs hover:bg-gray-600"
                      >
                        <X className="h-3.5 w-3.5" /> Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() =>
                        setEditing({
                          tenant_id: q.tenant_id,
                          max: q.max_reports_per_month,
                        })
                      }
                      className="rounded bg-gray-700 px-3 py-1 text-xs hover:bg-gray-600"
                    >
                      Edit
                    </button>
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
