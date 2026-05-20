'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Database, FileSearch, FolderTree, Globe2, Settings2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { aiScraper } from '@/lib/api-client'

import { CategoriesPanel } from '@/components/admin/ai-scraper/categories-panel'
import { ResultsPanel } from '@/components/admin/ai-scraper/results-panel'
import { SettingsPanel } from '@/components/admin/ai-scraper/settings-panel'
import { SourcesPanel } from '@/components/admin/ai-scraper/sources-panel'
import { TasksPanel } from '@/components/admin/ai-scraper/tasks-panel'

type TabId = 'sources' | 'categories' | 'tasks' | 'results' | 'settings'

const TABS: { id: TabId; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'sources', label: 'Sources', icon: Globe2 },
  { id: 'categories', label: 'Categories', icon: FolderTree },
  { id: 'tasks', label: 'Tasks', icon: Database },
  { id: 'results', label: 'Results', icon: FileSearch },
  { id: 'settings', label: 'Settings', icon: Settings2 },
]

export default function AdminAiScraperPage() {
  const [tab, setTab] = useState<TabId>('sources')

  const seed = useMutation({
    mutationFn: () => aiScraper.seedCatalog(false),
    onSuccess: (res) => {
      toast.success(`Catalog seeded: ${JSON.stringify(res.data.stats)}`)
    },
    onError: () => toast.error('Seed failed — check API logs'),
  })

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Scraper</h1>
          <p className="mt-1 text-gray-400">
            Lead factory: scrape into marketplace pool, match by trade + postcode, deliver to new
            tenants (2/day for 7 days).
          </p>
        </div>
        <button
          type="button"
          onClick={() => seed.mutate()}
          disabled={seed.isPending}
          className="inline-flex items-center gap-2 rounded-lg bg-amber-500/20 px-4 py-2 text-sm font-semibold text-amber-200 ring-1 ring-amber-500/40 hover:bg-amber-500/30 disabled:opacity-50"
        >
          <Sparkles className="h-4 w-4" />
          {seed.isPending ? 'Seeding…' : 'Seed default catalog'}
        </button>
      </header>

      <nav className="flex flex-wrap gap-1 rounded-xl border border-gray-800 bg-gray-900 p-1">
        {TABS.map((t) => {
          const active = tab === t.id
          const Icon = t.icon
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
                active
                  ? 'bg-amber-500/15 text-amber-300'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'
              }`}
            >
              <Icon className="h-4 w-4" />
              {t.label}
            </button>
          )
        })}
      </nav>

      <div>
        {tab === 'sources' && <SourcesPanel />}
        {tab === 'categories' && <CategoriesPanel />}
        {tab === 'tasks' && <TasksPanel />}
        {tab === 'results' && <ResultsPanel />}
        {tab === 'settings' && <SettingsPanel />}
      </div>
    </div>
  )
}
