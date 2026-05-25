'use client'

import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { admin as adminApi, type CategoryToolConfig, type ToolMeta } from '@/lib/api-client'
import {
  LayoutDashboard, Sparkles, Target, Users, ListTodo, Calendar,
  FileText, CreditCard, PoundSterling, MessageSquare, PhoneCall,
  Inbox, Megaphone, Globe, Search as SearchIcon, Zap, Star,
  TrendingUp, Settings, RotateCcw, Save, CheckCircle2, XCircle, Link2,
  type LucideIcon,
} from 'lucide-react'

// ── Icon map (href → icon component) ─────────────────────────────────────────
const ICON_MAP: Record<string, LucideIcon> = {
  '/dashboard':              LayoutDashboard,
  '/dashboard/assistant':    Sparkles,
  '/dashboard/leads':        Target,
  '/dashboard/crm':          Users,
  '/dashboard/tasks':        ListTodo,
  '/dashboard/bookings':     Calendar,
  '/dashboard/quotes':       FileText,
  '/dashboard/invoices':     CreditCard,
  '/dashboard/money':        PoundSterling,
  '/dashboard/messages':     MessageSquare,
  '/dashboard/whatsapp':     PhoneCall,
  '/dashboard/auto-replies': Inbox,
  '/dashboard/outreach':     Megaphone,
  '/dashboard/ads':          Megaphone,
  '/dashboard/seo':          SearchIcon,
  '/dashboard/automations':  Zap,
  '/dashboard/reviews':      Star,
  '/dashboard/integrations': Link2,
  '/dashboard/membership-rewards': TrendingUp,
  '/dashboard/settings':     Settings,
}

// ── Category display names ────────────────────────────────────────────────────
const CAT_LABELS: Record<string, string> = {
  tradesman:            'Tradesman',
  salon_beauty:         'Salon & Beauty',
  healthcare:           'Healthcare',
  restaurant_food:      'Restaurant / Food',
  retail:               'Retail',
  fitness_wellness:     'Fitness & Wellness',
  professional_services:'Professional Services',
  general:              'General',
}

// ── Toast state helpers ───────────────────────────────────────────────────────
type ToastKind = 'success' | 'error'
interface Toast { id: number; kind: ToastKind; msg: string }

export default function ToolConfigsPage() {
  const qc = useQueryClient()
  const [toasts, setToasts] = useState<Toast[]>([])
  const [pendingChanges, setPendingChanges] = useState<Record<string, Set<string>>>({})

  const addToast = (kind: ToastKind, msg: string) => {
    const id = Date.now()
    setToasts((t) => [...t, { id, kind, msg }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500)
  }

  // Fetch meta (canonical tool list + categories)
  const { data: meta } = useQuery({
    queryKey: ['admin', 'tool-config-meta'],
    queryFn: () => adminApi.getToolConfigMeta().then((r) => r.data),
    staleTime: 10 * 60 * 1000,
  })

  // Fetch all category configs
  const { data: configs = [], isLoading } = useQuery({
    queryKey: ['admin', 'tool-configs'],
    queryFn: () => adminApi.listToolConfigs().then((r) => r.data),
    staleTime: 60 * 1000,
  })

  // Build effective enabled set per category (pending > server)
  const effectiveEnabled = useMemo<Record<string, Set<string>>>(() => {
    const out: Record<string, Set<string>> = {}
    for (const cfg of configs) {
      out[cfg.category] = pendingChanges[cfg.category]
        ? new Set(pendingChanges[cfg.category])
        : new Set(cfg.enabled_tools)
    }
    return out
  }, [configs, pendingChanges])

  const toggleTool = (category: string, href: string) => {
    setPendingChanges((prev) => {
      const base: Set<string> = prev[category]
        ? new Set(prev[category])
        : new Set(configs.find((c) => c.category === category)?.enabled_tools ?? [])
      if (base.has(href)) base.delete(href)
      else base.add(href)
      return { ...prev, [category]: base }
    })
  }

  const hasPending = (category: string) => !!pendingChanges[category]

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: ({ category, tools }: { category: string; tools: string[] }) =>
      adminApi.updateToolConfig(category, tools),
    onSuccess: (_, { category }) => {
      setPendingChanges((p) => { const n = { ...p }; delete n[category]; return n })
      qc.invalidateQueries({ queryKey: ['admin', 'tool-configs'] })
      addToast('success', `Saved config for ${CAT_LABELS[category] ?? category}`)
    },
    onError: (_, { category }) => {
      addToast('error', `Failed to save ${CAT_LABELS[category] ?? category}`)
    },
  })

  // Reset mutation
  const resetMutation = useMutation({
    mutationFn: (category: string) => adminApi.resetToolConfig(category),
    onSuccess: (_, category) => {
      setPendingChanges((p) => { const n = { ...p }; delete n[category]; return n })
      qc.invalidateQueries({ queryKey: ['admin', 'tool-configs'] })
      addToast('success', `Reset ${CAT_LABELS[category] ?? category} to defaults`)
    },
    onError: (_, category) => {
      addToast('error', `Failed to reset ${CAT_LABELS[category] ?? category}`)
    },
  })

  const tools: ToolMeta[] = meta?.tools ?? []
  const categories: string[] = meta?.categories ?? configs.map((c) => c.category)

  return (
    <div className="text-white">
      {/* Toast stack */}
      <div className="fixed inset-x-4 top-4 z-50 flex flex-col gap-2 sm:inset-x-auto sm:right-5 sm:top-5">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm shadow-xl
              ${t.kind === 'success' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'}`}
          >
            {t.kind === 'success' ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
            {t.msg}
          </div>
        ))}
      </div>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Module Visibility</h1>
        <p className="mt-1 text-sm text-gray-400">
          Control which modules are visible in the tenant dashboard for each business category.
          Toggle individual tools per category, then save. Reset reverts a category to system defaults.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-16 text-gray-500">Loading…</div>
      )}

      {!isLoading && categories.map((cat) => {
        const cfg = configs.find((c) => c.category === cat)
        const enabled = effectiveEnabled[cat] ?? new Set<string>()
        const isPending = hasPending(cat)
        const isSaving = saveMutation.isPending && (saveMutation.variables as { category: string })?.category === cat
        const isResetting = resetMutation.isPending && resetMutation.variables === cat

        return (
          <div key={cat} className="mb-6 rounded-xl border border-gray-800 bg-gray-900">
            {/* Category header */}
            <div className="flex flex-col gap-3 border-b border-gray-800 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between sm:px-5">
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-base font-semibold text-white">
                  {CAT_LABELS[cat] ?? cat}
                </span>
                {cfg?.is_customised && (
                  <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-xs font-medium text-amber-400">
                    customised
                  </span>
                )}
                {isPending && (
                  <span className="rounded-full bg-blue-500/15 px-2 py-0.5 text-xs font-medium text-blue-400">
                    unsaved changes
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {cfg?.is_customised && (
                  <button
                    onClick={() => resetMutation.mutate(cat)}
                    disabled={isResetting}
                    className="flex items-center gap-1.5 rounded-lg border border-gray-700 px-3 py-1.5 text-xs text-gray-400 transition hover:border-gray-600 hover:text-white disabled:opacity-40"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    {isResetting ? 'Resetting…' : 'Reset to defaults'}
                  </button>
                )}
                <button
                  onClick={() => saveMutation.mutate({ category: cat, tools: Array.from(enabled) })}
                  disabled={!isPending || isSaving}
                  className="flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-black transition hover:bg-amber-400 disabled:opacity-40"
                >
                  <Save className="h-3.5 w-3.5" />
                  {isSaving ? 'Saving…' : 'Save'}
                </button>
              </div>
            </div>

            {/* Tool grid */}
            <div className="grid grid-cols-1 gap-px bg-gray-800 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5">
              {tools.map((tool) => {
                const Icon = ICON_MAP[tool.href] ?? LayoutDashboard
                const on = enabled.has(tool.href)
                return (
                  <button
                    key={tool.href}
                    onClick={() => toggleTool(cat, tool.href)}
                    className={`flex items-center gap-2.5 px-4 py-3 text-left text-sm transition
                      ${on
                        ? 'bg-gray-900 text-white hover:bg-gray-800'
                        : 'bg-gray-950 text-gray-600 hover:bg-gray-900 hover:text-gray-400'
                      }`}
                  >
                    {/* Toggle pill */}
                    <span
                      className={`relative inline-flex h-5 w-9 flex-shrink-0 rounded-full border-2 transition-colors
                        ${on ? 'border-amber-500 bg-amber-500' : 'border-gray-700 bg-gray-800'}`}
                    >
                      <span
                        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform
                          ${on ? 'translate-x-3.5' : 'translate-x-0.5'}`}
                        style={{ marginTop: '1px' }}
                      />
                    </span>
                    <Icon className={`h-4 w-4 flex-shrink-0 ${on ? 'text-amber-400' : 'text-gray-700'}`} />
                    <span className="truncate">{tool.label}</span>
                  </button>
                )
              })}
            </div>

            {/* Footer: count */}
            <div className="border-t border-gray-800 px-5 py-2 text-xs text-gray-500">
              {enabled.size} / {tools.length} modules enabled
            </div>
          </div>
        )
      })}
    </div>
  )
}
