'use client'

import { Command } from 'cmdk'
import {
  Briefcase,
  FileText,
  ListTodo,
  Receipt,
  Search,
  User as UserIcon,
  UserPlus,
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

import { search as searchApi } from '../../lib/api-client'
import { useCommandPalette } from '../../lib/stores/command-palette'

interface Hit {
  type: 'customer' | 'lead' | 'deal' | 'quote' | 'invoice' | 'task'
  id: string
  label: string
  sublabel: string | null
  url: string
}

const TYPE_META: Record<Hit['type'], { icon: typeof UserIcon; label: string; tint: string }> = {
  customer: { icon: UserIcon, label: 'Customer', tint: 'text-blue-600' },
  lead: { icon: UserPlus, label: 'Lead', tint: 'text-emerald-600' },
  deal: { icon: Briefcase, label: 'Deal', tint: 'text-indigo-600' },
  quote: { icon: FileText, label: 'Quote', tint: 'text-amber-600' },
  invoice: { icon: Receipt, label: 'Invoice', tint: 'text-rose-600' },
  task: { icon: ListTodo, label: 'Task', tint: 'text-violet-600' },
}

export function CommandPalette() {
  const router = useRouter()
  const { isOpen, open, close } = useCommandPalette()
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState<Hit[]>([])
  const [loading, setLoading] = useState(false)

  // Global keyboard shortcut.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.key === 'k' || e.key === 'K') && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        if (isOpen) close()
        else open()
      } else if (e.key === '/' && (e.target as HTMLElement)?.tagName !== 'INPUT' && (e.target as HTMLElement)?.tagName !== 'TEXTAREA') {
        e.preventDefault()
        open()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isOpen, open, close])

  // Debounced search.
  useEffect(() => {
    if (!isOpen) return
    const q = query.trim()
    if (q.length < 2) {
      setHits([])
      return
    }
    setLoading(true)
    const t = window.setTimeout(async () => {
      try {
        const { data } = await searchApi.query(q, { limit_per_type: 5 })
        setHits(data.hits)
      } catch (err) {
        console.error('Search failed', err)
        setHits([])
      } finally {
        setLoading(false)
      }
    }, 200)
    return () => window.clearTimeout(t)
  }, [query, isOpen])

  // Reset on close.
  useEffect(() => {
    if (!isOpen) {
      setQuery('')
      setHits([])
    }
  }, [isOpen])

  if (!isOpen) return null

  const goTo = (url: string) => {
    close()
    router.push(url)
  }

  // Group hits by type for nicer rendering.
  const grouped = hits.reduce<Record<string, Hit[]>>((acc, h) => {
    acc[h.type] = acc[h.type] || []
    acc[h.type].push(h)
    return acc
  }, {})

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[8vh] px-4 pointer-events-none">
      <button
        type="button"
        onClick={close}
        aria-label="Close search"
        className="absolute inset-0 bg-gray-950/60 backdrop-blur-sm pointer-events-auto"
      />
      <Command
        label="Global command palette"
        className="relative pointer-events-auto w-full max-w-xl bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden"
      >
        <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100">
          <Search className="w-4 h-4 text-gray-400" />
          <Command.Input
            value={query}
            onValueChange={setQuery}
            autoFocus
            placeholder="Search customers, leads, deals, quotes, invoices, tasks…"
            className="flex-1 bg-transparent outline-none text-sm text-gray-900 placeholder:text-gray-400"
          />
          <kbd className="hidden sm:inline text-[10px] font-mono text-gray-400 px-1.5 py-0.5 rounded border border-gray-200">
            esc
          </kbd>
        </div>

        <Command.List className="max-h-96 overflow-y-auto">
          {loading && (
            <div className="px-4 py-6 text-center text-xs text-gray-400">Searching…</div>
          )}
          {!loading && query.length >= 2 && hits.length === 0 && (
            <Command.Empty className="px-4 py-6 text-center text-xs text-gray-400">
              No results for &ldquo;{query}&rdquo;
            </Command.Empty>
          )}

          {Object.entries(grouped).map(([type, rows]) => {
            const meta = TYPE_META[type as Hit['type']]
            const Icon = meta.icon
            return (
              <Command.Group key={type} heading={meta.label}>
                {rows.map((h) => (
                  <Command.Item
                    key={`${h.type}-${h.id}`}
                    value={`${h.label} ${h.sublabel ?? ''} ${h.id}`}
                    onSelect={() => goTo(h.url)}
                    className="flex items-center gap-3 px-4 py-2 cursor-pointer text-sm aria-selected:bg-blue-50"
                  >
                    <Icon className={`w-4 h-4 flex-shrink-0 ${meta.tint}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-900 truncate">{h.label}</p>
                      {h.sublabel && (
                        <p className="text-xs text-gray-500 truncate">{h.sublabel}</p>
                      )}
                    </div>
                  </Command.Item>
                ))}
              </Command.Group>
            )
          })}

          {query.length < 2 && !loading && (
            <Command.Group heading="Jump to">
              {[
                { icon: ListTodo, label: 'Tasks', url: '/tasks' },
                { icon: UserPlus, label: 'Leads', url: '/leads' },
                { icon: Briefcase, label: 'CRM Pipeline', url: '/crm' },
                { icon: UserIcon, label: 'Customers', url: '/crm/customers' },
                { icon: FileText, label: 'Quotes', url: '/quotes' },
                { icon: Receipt, label: 'Invoices', url: '/invoices' },
              ].map((entry) => {
                const Icon = entry.icon
                return (
                  <Command.Item
                    key={entry.url}
                    value={`Jump ${entry.label}`}
                    onSelect={() => goTo(entry.url)}
                    className="flex items-center gap-3 px-4 py-2 cursor-pointer text-sm aria-selected:bg-blue-50"
                  >
                    <Icon className="w-4 h-4 text-gray-500" />
                    <span className="text-gray-900">{entry.label}</span>
                  </Command.Item>
                )
              })}
            </Command.Group>
          )}
        </Command.List>

        <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 text-[11px] text-gray-400">
          <span>
            <kbd className="font-mono px-1 py-0.5 border border-gray-200 rounded mr-1">↑↓</kbd>
            navigate
            <kbd className="font-mono px-1 py-0.5 border border-gray-200 rounded mx-1">↵</kbd>
            open
          </span>
          <span>
            <kbd className="font-mono px-1 py-0.5 border border-gray-200 rounded mr-1">⌘K</kbd>
            anywhere
          </span>
        </div>
      </Command>
    </div>
  )
}
