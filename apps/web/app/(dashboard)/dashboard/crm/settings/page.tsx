'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import Link from 'next/link'
import { Plus, Zap } from 'lucide-react'
import { crm } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function CrmSettingsPage() {
  const qc = useQueryClient()
  const [pipelineName, setPipelineName] = useState('')
  const [fieldLabel, setFieldLabel] = useState('')
  const [fieldKey, setFieldKey] = useState('')

  const { data: pipelines } = useQuery({
    queryKey: ['crm', 'pipelines'],
    queryFn: () => crm.listPipelines().then((r) => r.data),
  })

  const { data: fields } = useQuery({
    queryKey: ['crm', 'custom-fields'],
    queryFn: () => crm.listCustomFields('customer').then((r) => r.data),
  })

  const createPipeline = useMutation({
    mutationFn: () => crm.createPipeline({ name: pipelineName, is_default: false }),
    onSuccess: () => {
      toast.success('Pipeline created')
      setPipelineName('')
      qc.invalidateQueries({ queryKey: ['crm', 'pipelines'] })
    },
  })

  const createField = useMutation({
    mutationFn: () =>
      crm.createCustomField({
        entity_type: 'customer',
        field_key: fieldKey,
        label: fieldLabel,
        field_type: 'text',
      }),
    onSuccess: () => {
      toast.success('Custom field added')
      setFieldLabel('')
      setFieldKey('')
      qc.invalidateQueries({ queryKey: ['crm', 'custom-fields'] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-foreground">CRM Settings</h1>
        <p className="text-sm text-muted-foreground">Pipelines, stages, and custom fields</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Pipelines</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ul className="space-y-2">
            {(pipelines ?? []).map(
              (p: { id: string; name: string; is_default: boolean; stages: { name: string }[] }) => (
                <li key={p.id} className="rounded-lg border border-border px-4 py-3">
                  <p className="font-medium">
                    {p.name}
                    {p.is_default && (
                      <span className="ml-2 text-xs text-brand-teal-600">default</span>
                    )}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Stages: {(p.stages ?? []).map((s) => s.name).join(' → ')}
                  </p>
                </li>
              ),
            )}
          </ul>
          <div className="flex gap-2">
            <input
              value={pipelineName}
              onChange={(e) => setPipelineName(e.target.value)}
              placeholder="New pipeline name"
              className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm"
            />
            <button
              type="button"
              disabled={!pipelineName.trim() || createPipeline.isPending}
              onClick={() => createPipeline.mutate()}
              className="inline-flex items-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white"
            >
              <Plus className="h-4 w-4" /> Add
            </button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Zap className="h-4 w-4" /> Integrations
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          <p>
            <strong className="text-foreground">Automations</strong> — Moving cards on the pipeline
            board triggers <code className="text-xs">lead_stage_changed</code> and{' '}
            <code className="text-xs">deal_stage_changed</code>. New leads still fire{' '}
            <code className="text-xs">lead_created</code>.
          </p>
          <p>
            <strong className="text-foreground">Messaging</strong> — Emails and SMS logged in
            Conversations appear on customer, lead, and deal timelines when the address matches.
          </p>
          <p>
            <strong className="text-foreground">Bookings</strong> — Appointments linked to a
            customer show read-only on profiles and board card panels (via customer email for leads).
          </p>
          <p>
            <strong className="text-foreground">AI</strong> — Use <em>AI enrich</em> on a lead card
            from the pipeline board to summarize and log enrichment on the timeline.
          </p>
          <Link
            href="/dashboard/automations"
            className="inline-block font-medium text-brand-teal-600 hover:underline"
          >
            Open automations →
          </Link>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Customer custom fields</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ul className="space-y-1 text-sm">
            {(fields ?? []).map((f: { id: string; label: string; field_key: string }) => (
              <li key={f.id}>
                {f.label} <span className="text-muted-foreground">({f.field_key})</span>
              </li>
            ))}
          </ul>
          <div className="grid gap-2 sm:grid-cols-3">
            <input
              value={fieldLabel}
              onChange={(e) => setFieldLabel(e.target.value)}
              placeholder="Label"
              className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
            />
            <input
              value={fieldKey}
              onChange={(e) => setFieldKey(e.target.value)}
              placeholder="field_key"
              className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
            />
            <button
              type="button"
              disabled={!fieldLabel.trim() || !fieldKey.trim() || createField.isPending}
              onClick={() => createField.mutate()}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium"
            >
              Add field
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
