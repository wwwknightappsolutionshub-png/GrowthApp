'use client'

import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Check, RefreshCw, RotateCcw, ToggleLeft } from 'lucide-react'
import { adminApi, type ToolMeta } from '@/lib/api-client'

interface FreelancerVisibility {
  enabled_tools: string[]
  is_customised: boolean
  updated_at: string | null
}

interface VisibilityMeta {
  tools: ToolMeta[]
  default_enabled_tools: string[]
}

const GROUPS: Array<{ label: string; hrefs: string[] }> = [
  { label: 'Overview', hrefs: ['/dashboard', '/dashboard/clients', '/dashboard/assistant'] },
  {
    label: 'Pipeline',
    hrefs: [
      '/dashboard/leads',
      '/dashboard/crm',
      '/dashboard/tasks',
      '/dashboard/bookings',
      '/dashboard/quotes',
      '/dashboard/invoices',
      '/dashboard/money',
    ],
  },
  {
    label: 'Engagement',
    hrefs: [
      '/dashboard/messages',
      '/dashboard/whatsapp',
      '/dashboard/auto-replies',
      '/dashboard/outreach',
    ],
  },
  {
    label: 'Growth',
    hrefs: [
      '/dashboard/landing-pages',
      '/dashboard/ads',
      '/dashboard/seo',
      '/dashboard/automations',
      '/dashboard/reviews',
      '/dashboard/referrals',
    ],
  },
  {
    label: 'AI Social',
    hrefs: [
      '/dashboard/ai-social/brand-identity',
      '/dashboard/ai-social/samples',
      '/dashboard/ai-social/preferences',
      '/dashboard/ai-social/drafts',
      '/dashboard/ai-social/approval',
      '/dashboard/ai-social/calendar',
    ],
  },
  {
    label: 'Marketer Tools',
    hrefs: [
      '/dashboard/marketer/funnel',
      '/dashboard/marketer/audience',
      '/dashboard/marketer/competitor',
      '/dashboard/marketer/quota',
    ],
  },
  { label: 'System', hrefs: ['/dashboard/settings'] },
]

function fmtDate(iso: string | null): string {
  if (!iso) return 'Default profile'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export default function FreelancerModuleVisibilityPage() {
  const qc = useQueryClient()
  const [enabled, setEnabled] = useState<Set<string>>(new Set())

  const meta = useQuery({
    queryKey: ['admin', 'freelancer-management', 'module-visibility', 'meta'],
    queryFn: () => adminApi.freelancerModuleVisibilityMeta().then((r) => r.data as VisibilityMeta),
  })
  const visibility = useQuery({
    queryKey: ['admin', 'freelancer-management', 'module-visibility'],
    queryFn: () =>
      adminApi.getFreelancerModuleVisibility().then((r) => r.data as FreelancerVisibility),
  })

  useEffect(() => {
    if (visibility.data?.enabled_tools) {
      setEnabled(new Set(visibility.data.enabled_tools))
    }
  }, [visibility.data?.enabled_tools])

  const toolsByHref = useMemo(() => {
    return new Map((meta.data?.tools ?? []).map((tool) => [tool.href, tool]))
  }, [meta.data?.tools])

  const groupedTools = useMemo(() => {
    const used = new Set(GROUPS.flatMap((group) => group.hrefs))
    const knownGroups = GROUPS.map((group) => ({
      ...group,
      tools: group.hrefs.map((href) => toolsByHref.get(href)).filter(Boolean) as ToolMeta[],
    })).filter((group) => group.tools.length > 0)
    const remaining = (meta.data?.tools ?? []).filter((tool) => !used.has(tool.href))
    return remaining.length > 0
      ? [...knownGroups, { label: 'Other', hrefs: remaining.map((tool) => tool.href), tools: remaining }]
      : knownGroups
  }, [meta.data?.tools, toolsByHref])

  const enabledList = useMemo(() => {
    const validHrefs = new Set((meta.data?.tools ?? []).map((tool) => tool.href))
    return Array.from(enabled).filter((href) => validHrefs.has(href))
  }, [enabled, meta.data?.tools])

  const save = useMutation({
    mutationFn: () => adminApi.updateFreelancerModuleVisibility(enabledList),
    onSuccess: () => {
      toast.success('Freelancer module visibility saved')
      qc.invalidateQueries({ queryKey: ['admin', 'freelancer-management', 'module-visibility'] })
    },
    onError: (err: any) => {
      toast.error(String(err?.response?.data?.detail || 'Could not save freelancer module visibility'))
    },
  })

  const reset = useMutation({
    mutationFn: () => adminApi.resetFreelancerModuleVisibility(),
    onSuccess: (res) => {
      const data = res.data as FreelancerVisibility
      setEnabled(new Set(data.enabled_tools))
      toast.success('Freelancer module visibility reset to default')
      qc.invalidateQueries({ queryKey: ['admin', 'freelancer-management', 'module-visibility'] })
    },
    onError: (err: any) => {
      toast.error(String(err?.response?.data?.detail || 'Could not reset freelancer module visibility'))
    },
  })

  const setAll = (hrefs: string[], value: boolean) => {
    setEnabled((current) => {
      const next = new Set(current)
      hrefs.forEach((href) => {
        if (value) next.add(href)
        else next.delete(href)
      })
      return next
    })
  }

  const isLoading = meta.isLoading || visibility.isLoading
  const allHrefs = (meta.data?.tools ?? []).map((tool) => tool.href)

  return (
    <div className="text-white">
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <ToggleLeft className="h-6 w-6 text-amber-400" /> Freelancer Module Visibility
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-gray-400">
            Choose which dashboard modules freelancers can see in their sidebar. This profile is
            separate from tenant business-category module visibility.
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            <span className="rounded-full bg-gray-800 px-2.5 py-1 text-gray-300">
              {enabledList.length} of {meta.data?.tools?.length ?? 0} modules enabled
            </span>
            <span className="rounded-full bg-gray-800 px-2.5 py-1 text-gray-300">
              {visibility.data?.is_customised ? 'Custom freelancer profile' : 'Using default profile'}
            </span>
            <span className="rounded-full bg-gray-800 px-2.5 py-1 text-gray-300">
              Updated: {fmtDate(visibility.data?.updated_at ?? null)}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => visibility.refetch()}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
          <button
            onClick={() => setAll(allHrefs, true)}
            disabled={isLoading || allHrefs.length === 0}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800 disabled:opacity-50"
          >
            Enable all
          </button>
          <button
            onClick={() => setAll(allHrefs, false)}
            disabled={isLoading || allHrefs.length === 0}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800 disabled:opacity-50"
          >
            Disable all
          </button>
          <button
            onClick={() => reset.mutate()}
            disabled={reset.isPending || isLoading}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800 disabled:opacity-50"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Reset default
          </button>
          <button
            onClick={() => save.mutate()}
            disabled={save.isPending || isLoading}
            className="inline-flex items-center gap-1.5 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-semibold text-gray-950 hover:bg-amber-400 disabled:opacity-60"
          >
            <Check className="h-3.5 w-3.5" /> Save changes
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-10 text-center text-sm text-gray-500">
          Loading freelancer modules...
        </div>
      ) : meta.isError || visibility.isError ? (
        <div className="rounded-lg border border-red-900/60 bg-red-950/30 p-6 text-sm text-red-300">
          Could not load freelancer module visibility.
        </div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {groupedTools.map((group) => {
            const groupEnabled = group.tools.filter((tool) => enabled.has(tool.href)).length
            return (
              <section key={group.label} className="rounded-lg border border-gray-800 bg-gray-900">
                <div className="flex items-center justify-between gap-3 border-b border-gray-800 px-4 py-3">
                  <div>
                    <h2 className="font-semibold">{group.label}</h2>
                    <p className="text-xs text-gray-500">
                      {groupEnabled} of {group.tools.length} enabled
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setAll(group.tools.map((tool) => tool.href), true)}
                      className="rounded border border-gray-700 px-2 py-1 text-[11px] text-gray-300 hover:bg-gray-800"
                    >
                      Enable group
                    </button>
                    <button
                      onClick={() => setAll(group.tools.map((tool) => tool.href), false)}
                      className="rounded border border-gray-700 px-2 py-1 text-[11px] text-gray-300 hover:bg-gray-800"
                    >
                      Disable group
                    </button>
                  </div>
                </div>
                <div className="divide-y divide-gray-800">
                  {group.tools.map((tool) => {
                    const checked = enabled.has(tool.href)
                    return (
                      <label
                        key={tool.href}
                        className="flex cursor-pointer items-start justify-between gap-4 px-4 py-3 hover:bg-gray-950/40"
                      >
                        <span>
                          <span className="block text-sm font-medium">{tool.label}</span>
                          <span className="block text-xs text-gray-500">{tool.href}</span>
                        </span>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(event) => {
                            const nextChecked = event.target.checked
                            setEnabled((current) => {
                              const next = new Set(current)
                              if (nextChecked) next.add(tool.href)
                              else next.delete(tool.href)
                              return next
                            })
                          }}
                          className="mt-1 h-4 w-4 rounded border-gray-700 bg-gray-950 text-amber-500 focus:ring-amber-500"
                        />
                      </label>
                    )
                  })}
                </div>
              </section>
            )
          })}
        </div>
      )}
    </div>
  )
}
