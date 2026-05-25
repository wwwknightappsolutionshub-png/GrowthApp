'use client'

import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { automations } from '@/lib/api-client'
import { toast } from 'sonner'
import { Plus, Sparkles, ToggleLeft, ToggleRight, Trash2, Zap, Pencil } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { Button } from '@/components/ui/button'

const EVENT_LABELS: Record<string, string> = {
  lead_created: 'New lead created',
  lead_stage_changed: 'Lead moved on CRM pipeline',
  deal_stage_changed: 'Deal moved on CRM pipeline',
  booking_confirmed: 'Booking confirmed',
  job_completed: 'Job completed',
  quote_sent: 'Quote sent',
  invoice_sent: 'Invoice sent',
}

const ACTION_LABELS: Record<string, string> = {
  send_sms: 'Send SMS',
  send_email: 'Send Email',
  wait: 'Wait',
  add_tag: 'Add Tag',
  move_stage: 'Move Stage',
}

type Preset = {
  key: string
  name: string
  description: string
  trigger_event: string
  installed: boolean
}

export default function AutomationsPage() {
  const qc = useQueryClient()

  const { data: automationList, isLoading } = useQuery({
    queryKey: ['automations'],
    queryFn: () => automations.list().then((r) => r.data),
  })

  const { data: presetList } = useQuery({
    queryKey: ['automation-presets'],
    queryFn: () => automations.listPresets().then((r) => r.data as Preset[]),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      automations.update(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automations'] }),
    onError: () => toast.error('Failed to update automation'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => automations.delete(id),
    onSuccess: () => {
      toast.success('Automation deleted')
      qc.invalidateQueries({ queryKey: ['automations'] })
      qc.invalidateQueries({ queryKey: ['automation-presets'] })
    },
    onError: () => toast.error('Failed to delete automation'),
  })

  const installAllMutation = useMutation({
    mutationFn: () => automations.installAllPresets(),
    onSuccess: (res) => {
      toast.success(res.data.message || 'Recommended workflows installed')
      qc.invalidateQueries({ queryKey: ['automations'] })
      qc.invalidateQueries({ queryKey: ['automation-presets'] })
    },
    onError: () => toast.error('Failed to install presets'),
  })

  const installPresetMutation = useMutation({
    mutationFn: (key: string) => automations.installPreset(key),
    onSuccess: () => {
      toast.success('Workflow installed')
      qc.invalidateQueries({ queryKey: ['automations'] })
      qc.invalidateQueries({ queryKey: ['automation-presets'] })
    },
    onError: () => toast.error('Failed to install workflow'),
  })

  const missingPresets = presetList?.filter((p) => !p.installed) ?? []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Automations</h1>
          <p className="text-sm text-muted-foreground">Automatic follow-ups and workflows that run 24/7</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {missingPresets.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => installAllMutation.mutate()}
              disabled={installAllMutation.isPending}
            >
              <Sparkles className="mr-1 h-4 w-4" />
              Install 3 recommended workflows
            </Button>
          )}
          <Button asChild size="sm" className="bg-brand-forest-700 hover:bg-brand-forest-800">
            <Link href="/dashboard/automations/new">
              <Plus className="mr-1 h-4 w-4" /> New automation
            </Link>
          </Button>
        </div>
      </div>

      {missingPresets.length > 0 && (
        <div className="grid gap-3 md:grid-cols-3">
          {presetList?.map((preset) => (
            <div
              key={preset.key}
              className="rounded-xl border border-border bg-card p-4 shadow-sm"
            >
              <p className="font-semibold text-foreground">{preset.name}</p>
              <p className="mt-1 text-sm text-muted-foreground">{preset.description}</p>
              <p className="mt-2 text-xs text-muted-foreground">
                Trigger: {EVENT_LABELS[preset.trigger_event] || preset.trigger_event}
              </p>
              {preset.installed ? (
                <span className="mt-3 inline-block text-xs font-medium text-emerald-600">Installed</span>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={() => installPresetMutation.mutate(preset.key)}
                  disabled={installPresetMutation.isPending}
                >
                  Install
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-4 text-sm text-brand-teal-50 shadow-sm">
        <strong>Tip:</strong> Automations fire when events occur (new lead, quote sent, job completed). Each step sends SMS or email — or waits before the next step.
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-forest-700 border-t-transparent" />
        </div>
      ) : (
        <div className="grid gap-4">
          {automationList?.length === 0 && (
            <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-12 text-center">
              <Zap className="mx-auto mb-3 h-10 w-10 text-brand-teal-300/70" />
              <p className="font-medium text-brand-teal-50">No automations yet</p>
              <p className="mt-1 text-sm text-brand-teal-100/70">
                Install the recommended workflows above or build your own sequence.
              </p>
            </div>
          )}
          {automationList?.map((automation: any) => (
            <div
              key={automation.id}
              className={`rounded-xl border bg-brand-forest-950 p-5 shadow-sm ${automation.is_active ? 'border-brand-forest-700' : 'border-brand-forest-900 opacity-70'}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <p className="font-semibold text-white">{automation.name}</p>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${automation.is_active ? 'bg-brand-teal-400/20 text-brand-teal-100 ring-1 ring-brand-teal-300/30' : 'bg-brand-forest-800 text-brand-teal-100/70'}`}
                    >
                      {automation.is_active ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  <p className="text-sm text-brand-teal-100/70">
                    Trigger:{' '}
                    <span className="font-medium text-brand-teal-50">
                      {EVENT_LABELS[automation.trigger_event] || automation.trigger_event}
                    </span>
                  </p>
                  {automation.steps?.length > 0 && (
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      {automation.steps.map((step: any, i: number) => (
                        <div key={step.id} className="flex items-center gap-1">
                          <span className="rounded bg-brand-forest-800 px-2 py-1 text-xs text-brand-teal-100/80">
                            {ACTION_LABELS[step.action_type] || step.action_type}
                            {step.delay_minutes > 0 && ` (+${step.delay_minutes}m)`}
                          </span>
                          {i < automation.steps.length - 1 && (
                            <span className="text-xs text-brand-teal-100/40">→</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  <p className="mt-3 text-xs text-brand-teal-100/60">
                    Created {formatDate(automation.created_at)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Link
                    href={`/dashboard/automations/${automation.id}`}
                    className="text-brand-teal-100/60 hover:text-white"
                    title="Edit automation"
                  >
                    <Pencil className="h-4 w-4" />
                  </Link>
                  <button
                    onClick={() => toggleMutation.mutate({ id: automation.id, is_active: !automation.is_active })}
                    disabled={toggleMutation.isPending}
                    className="text-brand-teal-100/60 hover:text-white disabled:opacity-40"
                    title={automation.is_active ? 'Pause automation' : 'Activate automation'}
                  >
                    {automation.is_active ? (
                      <ToggleRight className="h-7 w-7 text-green-500" />
                    ) : (
                      <ToggleLeft className="h-7 w-7" />
                    )}
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Delete this automation?')) deleteMutation.mutate(automation.id)
                    }}
                    disabled={deleteMutation.isPending}
                    className="text-brand-teal-100/50 hover:text-red-300 disabled:opacity-40"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
