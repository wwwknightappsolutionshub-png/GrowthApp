'use client'

import Link from 'next/link'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ExternalLink,
  FileText,
  Loader2,
  Plus,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { landingPages, type LandingPageRow } from '@/lib/api-client'
import { formatDistanceToNow } from 'date-fns'

export default function LandingPagesIndex() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery<LandingPageRow[]>({
    queryKey: ['landing-pages'],
    queryFn: () => landingPages.list().then((r) => r.data),
  })

  const togglePublish = useMutation({
    mutationFn: (p: LandingPageRow) =>
      landingPages.update(p.id, { is_published: !p.is_published }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['landing-pages'] }),
  })
  const remove = useMutation({
    mutationFn: (id: string) => landingPages.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['landing-pages'] }),
  })

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <FileText className="w-6 h-6 text-blue-600" /> Landing Pages
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            AI-generated lead-capture pages, fully editable. Each tenant gets a unique slug.
          </p>
        </div>
        <Link
          href="/dashboard/landing-pages/new"
          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Sparkles className="w-4 h-4" /> Generate with AI
        </Link>
      </header>

      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-muted-foreground">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading...
        </div>
      ) : !data?.length ? (
        <div className="rounded-xl border bg-card py-16 flex flex-col items-center gap-3 text-muted-foreground">
          <FileText className="w-10 h-10 text-gray-300" />
          <p className="text-sm">No landing pages yet.</p>
          <Link
            href="/dashboard/landing-pages/new"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600"
          >
            <Plus className="w-4 h-4" /> Generate your first page
          </Link>
        </div>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((p) => (
            <li key={p.id} className="rounded-xl border bg-card p-5 shadow-sm">
              <div className="flex items-start justify-between mb-3">
                <Link
                  href={`/dashboard/landing-pages/${p.id}`}
                  className="font-semibold hover:underline line-clamp-2"
                >
                  {p.title}
                </Link>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    p.is_published ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-muted-foreground'
                  }`}
                >
                  {p.is_published ? 'Live' : 'Draft'}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
                {p.meta_description || '(no meta description)'}
              </p>
              <div className="text-xs text-muted-foreground flex items-center justify-between mb-4">
                <code className="bg-gray-50 px-2 py-0.5 rounded">/{p.slug}</code>
                <span>Updated {formatDistanceToNow(new Date(p.updated_at))} ago</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <button
                  onClick={() => togglePublish.mutate(p)}
                  className={`text-xs font-medium rounded-md px-2 py-1 ${
                    p.is_published
                      ? 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {p.is_published ? 'Unpublish' : 'Publish'}
                </button>
                <div className="flex items-center gap-2">
                  {p.is_published && (
                    <Link
                      href={`/preview/landing/${p.slug}?id=${p.id}`}
                      target="_blank"
                      className="text-muted-foreground hover:text-foreground"
                      title="Preview"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Link>
                  )}
                  <button
                    onClick={() => {
                      if (confirm(`Delete "${p.title}"?`)) remove.mutate(p.id)
                    }}
                    className="text-gray-400 hover:text-red-600"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
