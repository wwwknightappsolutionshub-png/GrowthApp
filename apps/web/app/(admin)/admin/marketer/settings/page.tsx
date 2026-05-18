'use client'

import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, Settings2 } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface PricingConfig {
  funnel_blueprint_credits: number
  audience_research_credits: number
  competitor_scan_credits: number
  plan_quotas: Record<string, number>
}

export default function MarketerSettingsPage() {
  const qc = useQueryClient()
  const [form, setForm] = useState<PricingConfig | null>(null)
  const [toast, setToast] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'marketer', 'pricing'],
    queryFn: () => adminApi.marketerPricing().then((r) => r.data),
  })

  useEffect(() => {
    if (data?.pricing) setForm(data.pricing as PricingConfig)
  }, [data])

  const saveMut = useMutation({
    mutationFn: (body: PricingConfig) => adminApi.marketerSetPricing(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'marketer', 'pricing'] })
      setToast('Pricing saved')
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
          <Settings2 className="h-6 w-6 text-amber-400" /> Global Marketer Settings
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Credit cost per Marketer tool + default monthly quota per subscription plan.
        </p>
      </div>

      {isLoading || !form ? (
        <div className="text-gray-400">Loading…</div>
      ) : (
        <div className="max-w-2xl space-y-6 rounded-xl border border-gray-800 bg-gray-900 p-6">
          <section>
            <h2 className="text-sm uppercase tracking-wider text-gray-400 mb-3">
              Credit costs
            </h2>
            <div className="grid grid-cols-3 gap-3">
              {[
                ['Funnel blueprint', 'funnel_blueprint_credits'],
                ['Audience research', 'audience_research_credits'],
                ['Competitor scan', 'competitor_scan_credits'],
              ].map(([label, key]) => (
                <div key={key}>
                  <label className="block text-xs text-gray-400 mb-1">{label}</label>
                  <input
                    type="number"
                    min={0}
                    value={(form as any)[key]}
                    onChange={(e) =>
                      setForm({ ...form, [key]: parseInt(e.target.value || '0', 10) } as PricingConfig)
                    }
                    className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm"
                  />
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-sm uppercase tracking-wider text-gray-400 mb-3">
              Plan quotas (monthly reports)
            </h2>
            <div className="grid grid-cols-3 gap-3">
              {Object.entries(form.plan_quotas).map(([plan, val]) => (
                <div key={plan}>
                  <label className="block text-xs text-gray-400 mb-1 capitalize">{plan}</label>
                  <input
                    type="number"
                    min={0}
                    value={val}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        plan_quotas: {
                          ...form.plan_quotas,
                          [plan]: parseInt(e.target.value || '0', 10),
                        },
                      })
                    }
                    className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm"
                  />
                </div>
              ))}
            </div>
          </section>

          <button
            onClick={() => saveMut.mutate(form)}
            disabled={saveMut.isPending}
            className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-black hover:bg-amber-400 disabled:opacity-60"
          >
            <Save className="h-4 w-4" />
            {saveMut.isPending ? 'Saving…' : 'Save settings'}
          </button>
        </div>
      )}
    </div>
  )
}
