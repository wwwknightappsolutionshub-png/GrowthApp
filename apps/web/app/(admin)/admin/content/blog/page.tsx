'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Eye, EyeOff, Save, X, ExternalLink } from 'lucide-react'
import { adminApiClient } from '@/lib/api-client'

interface BlogPost {
  id: string
  title: string
  slug: string
  excerpt: string | null
  content: string | null
  category: string | null
  image_url: string | null
  seo_title: string | null
  seo_description: string | null
  author_name: string | null
  read_minutes: number
  is_published: boolean
  published_at: string | null
}

const api = {
  list: (page = 1) => adminApiClient.get<{ items: BlogPost[]; total: number }>(`/content/blog?page=${page}&per_page=20`).then((r) => r.data),
  create: (body: Partial<BlogPost>) => adminApiClient.post('/content/blog', body),
  update: (id: string, body: Partial<BlogPost>) => adminApiClient.put(`/content/blog/${id}`, body),
  delete: (id: string) => adminApiClient.delete(`/content/blog/${id}`),
}

const EMPTY: Partial<BlogPost> = {
  title: '', slug: '', excerpt: '', content: '', category: 'Guide',
  image_url: '', seo_title: '', seo_description: '',
  author_name: 'CustomerFlow Team', read_minutes: 5, is_published: false,
}

function slugify(s: string) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

export default function BlogAdminPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['admin-blog'], queryFn: () => api.list() })
  const items = data?.items ?? []
  const [editing, setEditing] = useState<BlogPost | null>(null)
  const [creating, setCreating] = useState(false)
  const [draft, setDraft] = useState<Partial<BlogPost>>(EMPTY)
  const [tab, setTab] = useState<'content' | 'seo'>('content')

  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin-blog'] })

  const saveMut = useMutation({
    mutationFn: () => editing ? api.update(editing.id, draft) : api.create(draft),
    onSuccess: () => { invalidate(); setEditing(null); setCreating(false); setDraft(EMPTY) },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(id),
    onSuccess: invalidate,
  })

  const toggleMut = useMutation({
    mutationFn: (item: BlogPost) => api.update(item.id, { ...item, is_published: !item.is_published }),
    onSuccess: invalidate,
  })

  function startEdit(item: BlogPost) { setEditing(item); setDraft({ ...item }); setCreating(false) }
  function startCreate() { setCreating(true); setEditing(null); setDraft(EMPTY) }
  function cancel() { setEditing(null); setCreating(false); setDraft(EMPTY) }

  const CATEGORIES = ['Guide', 'Trades', 'Strategy', 'Reviews', 'Bookings', 'Lead Generation', 'Hospitality', 'Compliance', 'Case Study', 'News']

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Blog Posts</h1>
          <p className="mt-1 text-sm text-white/50">Manage blog content, SEO and publish status.</p>
        </div>
        <button onClick={startCreate} className="flex items-center gap-2 rounded-lg bg-brand-teal-400 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-300">
          <Plus className="h-4 w-4" /> New Post
        </button>
      </div>

      {/* Editor */}
      {(editing || creating) && (
        <div className="rounded-xl border border-white/10 bg-gray-900 p-5 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-white">{creating ? 'New Blog Post' : 'Edit Post'}</h2>
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
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Title *</label>
                <input value={draft.title ?? ''} onChange={(e) => setDraft({ ...draft, title: e.target.value, slug: draft.slug || slugify(e.target.value) })}
                  className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
                  placeholder="Blog post title" />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-white/60 mb-1.5">Slug *</label>
                  <input value={draft.slug ?? ''} onChange={(e) => setDraft({ ...draft, slug: slugify(e.target.value) })}
                    className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
                    placeholder="my-blog-post-slug" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-white/60 mb-1.5">Category</label>
                  <select value={draft.category ?? 'Guide'} onChange={(e) => setDraft({ ...draft, category: e.target.value })}
                    className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400">
                    {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Excerpt</label>
                <textarea rows={2} value={draft.excerpt ?? ''} onChange={(e) => setDraft({ ...draft, excerpt: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
                  placeholder="Short description shown in blog cards…" />
              </div>
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Content (HTML)</label>
                <textarea rows={10} value={draft.content ?? ''} onChange={(e) => setDraft({ ...draft, content: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 font-mono text-xs text-white outline-none focus:border-brand-teal-400"
                  placeholder="<h1>Post title</h1><p>Post content…</p>" />
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="block text-xs font-medium text-white/60 mb-1.5">Cover image URL</label>
                  <input value={draft.image_url ?? ''} onChange={(e) => setDraft({ ...draft, image_url: e.target.value })}
                    className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
                    placeholder="https://images.pexels.com/…" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-white/60 mb-1.5">Author name</label>
                  <input value={draft.author_name ?? ''} onChange={(e) => setDraft({ ...draft, author_name: e.target.value })}
                    className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
                    placeholder="CustomerFlow Team" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-white/60 mb-1.5">Read time (min)</label>
                  <input type="number" value={draft.read_minutes ?? 5} onChange={(e) => setDraft({ ...draft, read_minutes: Number(e.target.value) })}
                    className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400" />
                </div>
              </div>
              <label className="flex items-center gap-2 text-sm text-white/70 cursor-pointer">
                <input type="checkbox" checked={draft.is_published ?? false}
                  onChange={(e) => setDraft({ ...draft, is_published: e.target.checked })} className="rounded" />
                Published (visible on site)
              </label>
            </div>
          )}

          {tab === 'seo' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">SEO Title (≤60 chars)</label>
                <input value={draft.seo_title ?? ''} onChange={(e) => setDraft({ ...draft, seo_title: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
                  placeholder="Post Title | CustomerFlow AI" />
                <p className="mt-1 text-[11px] text-white/30">{(draft.seo_title ?? '').length}/60 characters</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">SEO Description (≤160 chars)</label>
                <textarea rows={3} value={draft.seo_description ?? ''} onChange={(e) => setDraft({ ...draft, seo_description: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-brand-teal-400"
                  placeholder="Concise description for search engines…" />
                <p className="mt-1 text-[11px] text-white/30">{(draft.seo_description ?? '').length}/160 characters</p>
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2 border-t border-white/10">
            <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending || !draft.title || !draft.slug}
              className="flex items-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-forest-600 disabled:opacity-50">
              <Save className="h-3.5 w-3.5" />
              {saveMut.isPending ? 'Saving…' : 'Save Post'}
            </button>
            <button onClick={cancel} className="flex items-center gap-2 rounded-lg border border-white/10 px-4 py-2 text-sm text-white/60 hover:text-white">
              <X className="h-3.5 w-3.5" /> Cancel
            </button>
          </div>
        </div>
      )}

      {/* Posts list */}
      {isLoading ? <p className="text-white/50 text-sm">Loading…</p> : (
        <div className="divide-y divide-white/5 rounded-xl border border-white/10 bg-gray-900">
          {items.map((item) => (
            <div key={item.id} className="flex items-center gap-4 p-4">
              {item.image_url && (
                <div className="h-14 w-20 shrink-0 overflow-hidden rounded-lg bg-gray-800">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={item.image_url} alt="" className="h-full w-full object-cover" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 rounded-full ${item.is_published ? 'bg-green-400' : 'bg-gray-500'}`} />
                  <p className="font-medium text-white text-sm truncate">{item.title}</p>
                </div>
                <p className="mt-0.5 text-xs text-white/40">{item.category} · {item.read_minutes} min · /{item.slug}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <a href={`/blog`} target="_blank" rel="noreferrer"
                  className="rounded p-1.5 text-white/40 hover:bg-white/5 hover:text-white">
                  <ExternalLink className="h-4 w-4" />
                </a>
                <button onClick={() => toggleMut.mutate(item)} className="rounded p-1.5 text-white/40 hover:bg-white/5 hover:text-white">
                  {item.is_published ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                </button>
                <button onClick={() => startEdit(item)} className="rounded p-1.5 text-white/40 hover:bg-white/5 hover:text-white">
                  <Pencil className="h-4 w-4" />
                </button>
                <button onClick={() => { if (confirm('Delete this post?')) deleteMut.mutate(item.id) }}
                  className="rounded p-1.5 text-red-400/60 hover:bg-red-400/10 hover:text-red-400">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
          {items.length === 0 && <p className="px-5 py-10 text-center text-sm text-white/30">No posts yet.</p>}
        </div>
      )}
    </div>
  )
}
