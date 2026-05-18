'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, Copy, Key, Plus, ShieldAlert, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { apiKeys, rbac } from '@/lib/api-client'

type ApiKey = {
  id: string
  name: string
  prefix: string
  scopes: string[]
  last_used_at: string | null
  expires_at: string | null
  revoked_at: string | null
  created_at: string
}

type ApiKeyCreated = ApiKey & { key: string }

function CreateKeyModal({
  open,
  onClose,
  catalogue,
  onCreated,
}: {
  open: boolean
  onClose: () => void
  catalogue: string[]
  onCreated: (created: ApiKeyCreated) => void
}) {
  const [name, setName] = useState('')
  const [scopes, setScopes] = useState<Set<string>>(new Set())
  const [isLive, setIsLive] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const toggleScope = (scope: string) => {
    setScopes((prev) => {
      const next = new Set(prev)
      if (next.has(scope)) next.delete(scope)
      else next.add(scope)
      return next
    })
  }

  const submit = async () => {
    if (!name.trim()) return
    setSubmitting(true)
    try {
      const { data } = await apiKeys.create({
        name: name.trim(),
        scopes: Array.from(scopes),
        is_live: isLive,
      })
      onCreated(data)
      setName('')
      setScopes(new Set())
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create key')
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null

  // Group permissions by their first segment for nicer rendering.
  const grouped = catalogue.reduce<Record<string, string[]>>((acc, perm) => {
    const [group] = perm.split('.')
    acc[group] = acc[group] || []
    acc[group].push(perm)
    return acc
  }, {})

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button onClick={onClose} className="absolute inset-0 bg-gray-950/60" aria-label="Close" />
      <div className="relative w-full max-w-2xl max-h-[90vh] bg-card rounded-xl shadow-2xl flex flex-col">
        <header className="flex items-center justify-between px-5 py-4 border-b border-border/50">
          <h2 className="text-base font-bold text-foreground">Create API key</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-foreground/80">
            <X className="w-4 h-4" />
          </button>
        </header>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div>
            <label className="text-xs font-semibold text-muted-foreground">Name</label>
            <input
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Zapier integration, internal CRM sync…"
            />
          </div>

          <div>
            <label className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
              <input
                type="checkbox"
                checked={isLive}
                onChange={(e) => setIsLive(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              Live key (uncheck for a test key)
            </label>
          </div>

          <div>
            <p className="text-xs font-semibold text-muted-foreground mb-2">Scopes</p>
            <div className="border border-border rounded-lg divide-y divide-gray-100 max-h-72 overflow-y-auto">
              {Object.entries(grouped).map(([group, perms]) => (
                <div key={group} className="p-3">
                  <p className="text-[11px] uppercase font-bold tracking-wide text-gray-400 mb-1">
                    {group}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {perms.map((p) => (
                      <label
                        key={p}
                        className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs cursor-pointer border transition-colors ${
                          scopes.has(p)
                            ? 'bg-blue-50 border-blue-200 text-blue-700'
                            : 'bg-gray-50 border-border text-muted-foreground hover:bg-gray-100'
                        }`}
                      >
                        <input
                          type="checkbox"
                          className="hidden"
                          checked={scopes.has(p)}
                          onChange={() => toggleScope(p)}
                        />
                        <code className="font-mono">{p}</code>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-amber-800">
              The full key is shown <strong>once</strong> after creation. Store it somewhere safe — we
              can&apos;t show it again.
            </p>
          </div>
        </div>
        <footer className="flex items-center justify-end gap-2 px-5 py-3 bg-gray-50 border-t border-border/50 rounded-b-xl">
          <button onClick={onClose} className="px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground">
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={submitting || !name.trim()}
            className="px-4 py-1.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? 'Creating…' : 'Create key'}
          </button>
        </footer>
      </div>
    </div>
  )
}

function CreatedKeyBanner({ created, onDismiss }: { created: ApiKeyCreated; onDismiss: () => void }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(created.key)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-emerald-900">Key created — copy it now</p>
          <p className="text-xs text-emerald-700 mt-1">
            This is the only time you&apos;ll see the full key. Treat it like a password.
          </p>
          <div className="mt-3 flex items-center gap-2">
            <code className="flex-1 font-mono text-xs bg-card border border-emerald-200 rounded px-2 py-1.5 break-all">
              {created.key}
            </code>
            <button
              onClick={copy}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-card border border-emerald-200 rounded hover:bg-emerald-100"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
        </div>
        <button onClick={onDismiss} className="p-1 text-emerald-700 hover:text-emerald-900">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

export default function ApiKeysPage() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [created, setCreated] = useState<ApiKeyCreated | null>(null)

  const { data: keys, isLoading } = useQuery<ApiKey[]>({
    queryKey: ['api-keys'],
    queryFn: () => apiKeys.list().then((r) => r.data),
  })

  const { data: catalogueData } = useQuery<{ permissions: string[] }>({
    queryKey: ['rbac-catalogue'],
    queryFn: () => rbac.catalogue().then((r) => r.data),
    staleTime: Infinity,
  })

  const revokeMutation = useMutation({
    mutationFn: (id: string) => apiKeys.revoke(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] })
      toast.success('API key revoked')
    },
    onError: () => toast.error('Failed to revoke key'),
  })

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">API Keys</h1>
          <p className="text-muted-foreground text-sm">
            Programmatic access to your CustomerFlow AI workspace.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          New API key
        </button>
      </div>

      {created && <CreatedKeyBanner created={created} onDismiss={() => setCreated(null)} />}

      <div className="bg-white rounded-xl border border-border divide-y divide-gray-100">
        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full" />
          </div>
        )}
        {!isLoading && (!keys || keys.length === 0) && (
          <div className="py-16 text-center">
            <Key className="w-8 h-8 mx-auto text-gray-300" />
            <p className="mt-3 text-sm text-muted-foreground">No API keys yet.</p>
          </div>
        )}
        {keys?.map((k) => {
          const isRevoked = !!k.revoked_at
          return (
            <div key={k.id} className="flex items-center gap-4 px-4 py-3">
              <div className="flex-shrink-0">
                <Key className={`w-5 h-5 ${isRevoked ? 'text-gray-300' : 'text-blue-600'}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${isRevoked ? 'text-gray-400 line-through' : 'text-foreground'}`}>
                  {k.name}
                </p>
                <p className="text-xs text-muted-foreground font-mono mt-0.5">
                  cf_…{k.prefix} · {k.scopes.length} scopes
                </p>
              </div>
              <div className="text-xs text-gray-400">
                {isRevoked
                  ? `Revoked ${new Date(k.revoked_at!).toLocaleDateString()}`
                  : k.last_used_at
                  ? `Used ${new Date(k.last_used_at).toLocaleDateString()}`
                  : 'Never used'}
              </div>
              {!isRevoked && (
                <button
                  onClick={() => {
                    if (window.confirm(`Revoke "${k.name}"? This cannot be undone.`)) {
                      revokeMutation.mutate(k.id)
                    }
                  }}
                  className="text-xs font-semibold text-red-600 hover:text-red-800"
                >
                  Revoke
                </button>
              )}
            </div>
          )
        })}
      </div>

      <CreateKeyModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        catalogue={catalogueData?.permissions ?? []}
        onCreated={(c) => {
          setCreated(c)
          setShowCreate(false)
          qc.invalidateQueries({ queryKey: ['api-keys'] })
        }}
      />
    </div>
  )
}
