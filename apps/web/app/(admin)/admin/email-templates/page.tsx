'use client'

import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { sanitizeHtml } from '@/lib/sanitize'
import {
  AlertCircle,
  Code2,
  Eye,
  FileCode2,
  Loader2,
  Mail,
  Paintbrush,
  RefreshCw,
  Save,
  Search,
} from 'lucide-react'
import { adminApi } from '@/lib/api-client'

// ── Types ─────────────────────────────────────────────────────────────────────

interface EmailTemplate {
  name: string
  label: string
  description: string
  category: string
  size_bytes: number
  updated_at: string
  html?: string
}

// ── Category config ────────────────────────────────────────────────────────────

const CATEGORY_META: Record<string, { label: string; color: string }> = {
  system:        { label: 'System',        color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' },
  lifecycle:     { label: 'Lifecycle',     color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' },
  auth:          { label: 'Auth',          color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' },
  transactional: { label: 'Transactional', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' },
  other:         { label: 'Other',         color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
}

function fmtDate(s: string) {
  return new Date(s).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function fmtBytes(n: number) {
  return n < 1024 ? `${n} B` : `${(n / 1024).toFixed(1)} KB`
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function EmailTemplatesPage() {
  const qc = useQueryClient()
  const [selected, setSelected] = useState<string | null>(null)
  const [html, setHtml] = useState('')
  const [dirty, setDirty] = useState(false)
  const [viewMode, setViewMode] = useState<'code' | 'wysiwyg' | 'preview'>('code')
  const [search, setSearch] = useState('')
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const wysiwygRef = useRef<HTMLDivElement>(null)

  // List all templates
  const { data: templates = [], isLoading: listLoading, isError: listError, error: listLoadError } = useQuery<EmailTemplate[]>({
    queryKey: ['admin', 'email-templates'],
    queryFn: () => adminApi.listEmailTemplates().then((r) => r.data),
  })

  // Load single template
  const { data: templateDetail, isLoading: detailLoading } = useQuery<EmailTemplate>({
    queryKey: ['admin', 'email-template', selected],
    queryFn: () => adminApi.getEmailTemplate(selected!).then((r) => r.data),
    enabled: !!selected,
  })

  useEffect(() => {
    if (templateDetail?.html !== undefined) {
      setHtml(templateDetail.html)
      setDirty(false)
      setPreviewHtml(null)
    }
  }, [templateDetail])

  // Save mutation
  const saveMut = useMutation({
    mutationFn: () => adminApi.updateEmailTemplate(selected!, html),
    onSuccess: () => {
      toast.success('Template saved')
      setDirty(false)
      qc.invalidateQueries({ queryKey: ['admin', 'email-templates'] })
      qc.invalidateQueries({ queryKey: ['admin', 'email-template', selected] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed to save'),
  })

  // Preview mutation
  const previewMut = useMutation({
    mutationFn: () => adminApi.previewEmailTemplate(selected!),
    onSuccess: (r) => {
      setPreviewHtml(r.data)
      setViewMode('preview')
    },
    onError: () => toast.error('Preview failed — check template syntax'),
  })

  // Group templates by category
  const grouped: Record<string, EmailTemplate[]> = {}
  const filtered = templates.filter((t) =>
    !search || t.label.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase()),
  )
  for (const t of filtered) {
    const cat = t.category ?? 'other'
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push(t)
  }
  const categoryOrder = ['system', 'lifecycle', 'auth', 'transactional', 'other']

  const selectedMeta = templates.find((t) => t.name === selected)

  // Keyboard save
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's' && selected && dirty) {
        e.preventDefault()
        saveMut.mutate()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [selected, dirty, html])

  return (
    <div className="flex h-[calc(100dvh-7rem)] min-h-[620px] flex-col overflow-hidden rounded-xl border border-gray-800 bg-gray-950 lg:h-[calc(100dvh-8rem)] lg:flex-row">
      {/* ── Sidebar: template list ── */}
      <aside className="flex max-h-72 w-full shrink-0 flex-col border-b border-gray-800 lg:max-h-none lg:w-72 lg:border-b-0 lg:border-r">
        <div className="border-b border-gray-800 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Mail className="h-5 w-5 text-amber-400" />
            <h1 className="text-base font-bold text-white">Email Templates</h1>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search templates…"
              className="w-full rounded-lg border border-gray-800 bg-gray-900 py-1.5 pl-8 pr-3 text-xs text-gray-200 placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-amber-500/40"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto py-2">
          {listLoading ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : listError ? (
            <div className="mx-4 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-xs text-red-300">
              <div className="mb-1 flex items-center gap-1.5 font-semibold">
                <AlertCircle className="h-3.5 w-3.5" /> Could not load templates
              </div>
              <p className="text-red-300/80">
                {String((listLoadError as any)?.response?.data?.detail || 'Please refresh or sign in again.')}
              </p>
            </div>
          ) : (
            categoryOrder.map((cat) => {
              const items = grouped[cat]
              if (!items?.length) return null
              const cm = CATEGORY_META[cat] ?? CATEGORY_META.other
              return (
                <div key={cat} className="mb-3">
                  <p className="px-4 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-widest text-gray-600">
                    {cm.label}
                  </p>
                  {items.map((t) => (
                    <button
                      key={t.name}
                      onClick={() => {
                        if (dirty && !confirm('You have unsaved changes. Discard them?')) return
                        setSelected(t.name)
                        setViewMode('code')
                        setPreviewHtml(null)
                      }}
                      className={`w-full px-4 py-2.5 text-left transition-colors ${
                        selected === t.name
                          ? 'bg-amber-500/10 border-l-2 border-amber-500'
                          : 'hover:bg-gray-900 border-l-2 border-transparent'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className={`text-sm font-medium ${selected === t.name ? 'text-amber-300' : 'text-gray-200'}`}>
                          {t.label}
                        </span>
                        {selected === t.name && dirty && (
                          <span className="h-2 w-2 shrink-0 rounded-full bg-amber-400" title="Unsaved changes" />
                        )}
                      </div>
                      <p className="mt-0.5 text-xs text-gray-500 leading-snug line-clamp-1">{t.description}</p>
                    </button>
                  ))}
                </div>
              )
            })
          )}
        </div>
      </aside>

      {/* ── Editor / preview ── */}
      <div className="flex flex-1 flex-col min-w-0">
        {!selected ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 text-gray-500">
            <FileCode2 className="h-12 w-12 opacity-30" />
            <p className="text-sm">Select a template to edit</p>
          </div>
        ) : (
          <>
            {/* Toolbar */}
            <div className="flex flex-col gap-3 border-b border-gray-800 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold text-white truncate">{selectedMeta?.label}</h2>
                  {selectedMeta?.category && (
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${CATEGORY_META[selectedMeta.category]?.color ?? CATEGORY_META.other.color}`}>
                      {CATEGORY_META[selectedMeta.category]?.label}
                    </span>
                  )}
                  {dirty && (
                    <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-400">
                      Unsaved
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-0.5">{selectedMeta?.description}</p>
              </div>

              <div className="flex w-full shrink-0 flex-wrap items-center gap-2 sm:w-auto sm:flex-nowrap">
                {/* View toggle */}
                <div className="flex max-w-full items-center gap-1 overflow-x-auto rounded-lg border border-gray-800 bg-gray-900 p-1">
                  <button
                    onClick={() => setViewMode('code')}
                    className={`flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium transition-colors ${viewMode === 'code' ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'}`}
                  >
                    <Code2 className="h-3.5 w-3.5" /> Code
                  </button>
                  <button
                    onClick={() => setViewMode('wysiwyg')}
                    className={`flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium transition-colors ${viewMode === 'wysiwyg' ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'}`}
                  >
                    <Paintbrush className="h-3.5 w-3.5" /> WYSIWYG
                  </button>
                  <button
                    onClick={() => {
                      if (!previewHtml) previewMut.mutate()
                      else setViewMode('preview')
                    }}
                    disabled={previewMut.isPending}
                    className={`flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium transition-colors ${viewMode === 'preview' ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'}`}
                  >
                    {previewMut.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Eye className="h-3.5 w-3.5" />}
                    Preview
                  </button>
                </div>

                {/* Refresh preview */}
                {viewMode === 'preview' && (
                  <button
                    onClick={() => previewMut.mutate()}
                    disabled={previewMut.isPending}
                    className="flex items-center gap-1.5 rounded-lg border border-gray-800 bg-gray-900 px-3 py-1.5 text-xs text-gray-400 hover:text-white"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${previewMut.isPending ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                )}

                {/* Save */}
                <button
                  onClick={() => saveMut.mutate()}
                  disabled={!dirty || saveMut.isPending}
                  className="flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-black hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {saveMut.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Save className="h-3.5 w-3.5" />
                  )}
                  Save {dirty ? '·' : ''} <kbd className="ml-0.5 font-mono text-[10px] opacity-60">⌘S</kbd>
                </button>
              </div>
            </div>

            {/* Info bar */}
            {selectedMeta?.name === 'base' && (
              <div className="flex items-start gap-2 border-b border-gray-800 bg-amber-500/5 px-5 py-2.5 text-xs text-amber-400">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>This is the master template. Changes here affect the layout and branding of <strong>all</strong> emails.</span>
              </div>
            )}

            {/* Editor or preview */}
            {detailLoading ? (
              <div className="flex flex-1 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-amber-500" />
              </div>
            ) : viewMode === 'code' ? (
              <textarea
                value={html}
                onChange={(e) => { setHtml(e.target.value); setDirty(true) }}
                spellCheck={false}
                className="min-h-[360px] flex-1 resize-none bg-gray-950 p-4 font-mono text-xs leading-relaxed text-gray-200 focus:outline-none sm:p-5"
                style={{ tabSize: 2 }}
                onKeyDown={(e) => {
                  if (e.key === 'Tab') {
                    e.preventDefault()
                    const start = e.currentTarget.selectionStart
                    const end = e.currentTarget.selectionEnd
                    const newHtml = html.substring(0, start) + '  ' + html.substring(end)
                    setHtml(newHtml)
                    setDirty(true)
                    requestAnimationFrame(() => {
                      e.currentTarget.selectionStart = e.currentTarget.selectionEnd = start + 2
                    })
                  }
                }}
              />
            ) : viewMode === 'wysiwyg' ? (
              <div className="flex flex-1 flex-col overflow-hidden bg-gray-100">
                <div className="border-b border-gray-300 bg-white px-4 py-2 text-xs text-gray-500">
                  Visual editor for rendered HTML. Dynamic template tags are preserved as text where they appear.
                </div>
                <div
                  key={selected}
                  ref={wysiwygRef}
                  contentEditable
                  suppressContentEditableWarning
                  dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }}
                  onInput={(event) => {
                    const next = event.currentTarget.innerHTML
                    setHtml(next)
                    setPreviewHtml(null)
                    setDirty(true)
                  }}
                  className="prose prose-sm max-w-none flex-1 overflow-auto bg-white p-4 text-gray-900 focus:outline-none sm:p-8"
                />
              </div>
            ) : (
              <div className="flex-1 overflow-hidden bg-gray-100">
                {previewHtml ? (
                  <iframe
                    ref={iframeRef}
                    srcDoc={previewHtml}
                    className="h-full w-full border-0"
                    title="Email preview"
                    sandbox="allow-same-origin"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center text-gray-500 text-sm">
                    No preview yet — click Refresh
                  </div>
                )}
              </div>
            )}

            {/* Status bar */}
            <div className="flex items-center justify-between border-t border-gray-800 px-5 py-1.5 text-[10px] text-gray-600">
              <span>
                {selectedMeta?.name}.html · {fmtBytes(new Blob([html]).size)}
              </span>
              <span>
                {selectedMeta?.updated_at ? `Last saved ${fmtDate(selectedMeta.updated_at)}` : ''}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
