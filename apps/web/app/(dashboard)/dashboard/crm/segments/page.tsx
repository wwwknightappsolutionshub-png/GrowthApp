'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { segments } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function CrmSegmentsPage() {
  const qc = useQueryClient()
  const [name, setName] = useState('')

  const { data: list, isLoading } = useQuery({
    queryKey: ['segments'],
    queryFn: () => segments.list().then((r) => r.data),
  })

  const createMut = useMutation({
    mutationFn: () => segments.create({ name, rules: { all: [], any: [], none: [] } }),
    onSuccess: () => {
      toast.success('Segment created')
      setName('')
      qc.invalidateQueries({ queryKey: ['segments'] })
    },
  })

  const recomputeMut = useMutation({
    mutationFn: () => segments.recompute(),
    onSuccess: () => {
      toast.success('Segments recomputed')
      qc.invalidateQueries({ queryKey: ['segments'] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-foreground">Segments</h1>
        <p className="text-sm text-muted-foreground">Saved customer segments with rule DSL</p>
      </div>

      <div className="flex gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Segment name"
          className="max-w-xs flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm"
        />
        <button
          type="button"
          disabled={!name.trim() || createMut.isPending}
          onClick={() => createMut.mutate()}
          className="rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white"
        >
          Create
        </button>
        <button
          type="button"
          onClick={() => recomputeMut.mutate()}
          disabled={recomputeMut.isPending}
          className="rounded-lg border border-border px-4 py-2 text-sm"
        >
          Recompute all
        </button>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading…</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {(list ?? []).map(
            (s: { id: string; name: string; size: number; description?: string; is_system: boolean }) => (
              <Card key={s.id}>
                <CardHeader>
                  <CardTitle className="text-base">{s.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">{s.size}</p>
                  <p className="text-xs text-muted-foreground">members</p>
                  {s.is_system && (
                    <span className="mt-2 inline-block text-xs text-brand-teal-600">System segment</span>
                  )}
                </CardContent>
              </Card>
            ),
          )}
        </div>
      )}
    </div>
  )
}
