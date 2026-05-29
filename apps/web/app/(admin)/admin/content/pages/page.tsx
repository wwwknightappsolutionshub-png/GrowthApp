'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Globe, Pencil, Plus, Save, Trash2, X } from 'lucide-react'
import { adminApiClient } from '@/lib/api-client'

interface StaticPage {
  id: string
  slug: string
  title: string
  content: string | null
  meta_title: string | null
  meta_description: string | null
  is_active: boolean
  updated_at: string | null
}

const api = {
  list: () => adminApiClient.get<StaticPage[]>('/content/pages').then((r) => r.data),
  create: (body: Partial<StaticPage>) => adminApiClient.post('/content/pages', body),
  update: (id: string, body: Partial<StaticPage>) => adminApiClient.put(`/content/pages/${id}`, body),
  delete: (id: string) => adminApiClient.delete(`/content/pages/${id}`),
}

const PAGE_LABELS: Record<string, string> = {
  about: 'About CustomerFlow AI',
  contact: 'Contact Page',
  partners: 'Partner Programme',
  careers: 'Careers (Coming Soon)',
  privacy: 'Privacy Policy',
  terms: 'Terms of Service',
  'gdpr-dpa': 'GDPR & DPA',
  cookies: 'Cookie Policy',
}

export default function StaticPagesAdminPage() {
  const qc = useQueryClient()
  const { data: pages = [], isLoading } = useQuery({ queryKey: ['admin-pages'], queryFn: api.list })
  const [editing, setEditing] = useState<StaticPage | null>(null)
  const [creating, setCreating] = useState(false)
  const [draft, setDraft] = useState<Partial<StaticPage>>({})
  const [tab, setTab] = useState<'content' | 'seo'>('content')

  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin-pages'] })

  const saveMut = useMutation({
    mutationFn: () => editing ? api.update(editing.id, draft) : api.create(draft),
    onSuccess: () => { invalidate(); setEditing(null); setCreating(false); setDraft({}) },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(id),
    onSuccess: invalidate,
  })

  function startEdit(page: StaticPage) {
    setEditing(page)
    setDraft({ title: page.title, content: page.content ?? '', meta_title: page.meta_title ?? '', meta_description: page.meta_description ?? '', is_active: page.is_active })
    setCreating(false)
  }

  function startCreate() {
    setEditing(null)
    setCreating(true)
    setTab('content')
    setDraft({ slug: '', title: '', content: '', meta_title: '', meta_description: '', is_active: true })
  }

  function cancel() { setEditing(null); setCreating(false); setDraft({}) }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Static Pages</h1>
          <p className="mt-1 text-sm text-white/50">Create, edit and delete static public content pages such as About, Contact, Terms and Privacy.</p>
        </div>
        <button onClick={startCreate} className="flex items-center gap-2 rounded-lg bg-brand-teal-400 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-300">
          <Plus className="h-4 w-4" /> New Page
        </button>
      </div>

      {(editing || creating) && (
        <div className="rounded-xl border border-white/10 bg-gray-900 p-5 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-white">
              {creating ? 'New static page' : <>Editing: <span className="text-brand-teal-300">{PAGE_LABELS[editing!.slug] ?? editing!.slug}</span></>}
            </h2>
            <div className="flex gap-2 rounded-lg border border-white/10 p-0.5">
              {(['content', 'seo'] as const).map((t) => (
                <button key={t} onClick={() => setTab(t)}
                  className={`rounded px-3 py-1 text-xs font-medium capitalize transition-colors ${tab === t ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white'}`}>
                  {t}
                </button>
              ))}
            </div>
          </div>

          {tab === 'content' && (
            <div className="space-y-4">
              {creating && (
                <div>
                  <label className="block text-xs font-medium text-white/60 mb-1.5">Slug *</label>
                  <input
                    value={draft.slug ?? ''}
                    onChange={(e) => setDraft({ ...draft, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-') })}
                    className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
                    placeholder="e.g. about-us"
                  />
                </div>
              )}
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Page title</label>
                <input value={draft.title ?? ''} onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400" />
              </div>
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">
                  Content (HTML — this overrides the hardcoded modal content)
                </label>
                <textarea rows={16} value={draft.content ?? ''} onChange={(e) => setDraft({ ...draft, content: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 font-mono text-xs text-white outline-none focus:border-brand-teal-400"
                  placeholder="<h2>Section heading</h2><p>Content…</p>" />
              </div>
              <label className="flex items-center gap-2 text-sm text-white/70 cursor-pointer">
                <input type="checkbox" checked={draft.is_active ?? true}
                  onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })} className="rounded" />
                Active (modal visible from footer)
              </label>
            </div>
          )}

          {tab === 'seo' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Meta title (≤60 chars)</label>
                <input value={draft.meta_title ?? ''} onChange={(e) => setDraft({ ...draft, meta_title: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
                  placeholder="About CustomerFlow AI | AI Platform for UK Businesses" />
              </div>
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Meta description (≤160 chars)</label>
                <textarea rows={3} value={draft.meta_description ?? ''} onChange={(e) => setDraft({ ...draft, meta_description: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
                  placeholder="Discover how CustomerFlow AI…" />
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2 border-t border-white/10">
            <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending || !draft.title || (creating && !draft.slug)}
              className="flex items-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-forest-600 disabled:opacity-50">
              <Save className="h-3.5 w-3.5" />
              {saveMut.isPending ? 'Saving…' : 'Save Page'}
            </button>
            <button onClick={cancel} className="flex items-center gap-2 rounded-lg border border-white/10 px-4 py-2 text-sm text-white/60 hover:text-white">
              <X className="h-3.5 w-3.5" /> Cancel
            </button>
          </div>
        </div>
      )}

      {isLoading ? <p className="text-white/50 text-sm">Loading…</p> : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {pages.map((page) => (
            <div key={page.id} className="rounded-xl border border-white/10 bg-gray-900 p-5">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Globe className="h-4 w-4 text-brand-teal-400 shrink-0" />
                  <h3 className="font-semibold text-white text-sm">{PAGE_LABELS[page.slug] ?? page.slug}</h3>
                </div>
                <span className={`h-2 w-2 rounded-full shrink-0 mt-1 ${page.is_active ? 'bg-green-400' : 'bg-gray-500'}`} />
              </div>
              <p className="mt-2 text-xs text-white/40 font-mono">/{page.slug}</p>
              {page.content ? (
                <p className="mt-2 text-xs text-white/50 line-clamp-2">{page.content.replace(/<[^>]+>/g, ' ').slice(0, 100)}…</p>
              ) : (
                <p className="mt-2 text-xs text-white/30 italic">Using hardcoded default content</p>
              )}
              {page.updated_at && (
                <p className="mt-2 text-[10px] text-white/20">Updated {new Date(page.updated_at).toLocaleDateString('en-GB')}</p>
              )}
              <button onClick={() => startEdit(page)}
                className="mt-4 flex items-center gap-1.5 text-xs font-medium text-brand-teal-400 hover:text-brand-teal-300">
                <Pencil className="h-3.5 w-3.5" /> Edit page
              </button>
              <button
                onClick={() => { if (confirm('Delete this static page?')) deleteMut.mutate(page.id) }}
                className="mt-3 flex items-center gap-1.5 text-xs font-medium text-red-400/80 hover:text-red-300"
              >
                <Trash2 className="h-3.5 w-3.5" /> Delete page
              </button>
            </div>
          ))}
          {pages.length === 0 && (
            <p className="rounded-xl border border-white/10 bg-gray-900 px-5 py-10 text-center text-sm text-white/30">
              No static pages yet. Click "New Page" to create one.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
