'use client'

import { useEffect, useState } from 'react'
import { Loader2, Mail, MessageSquare, Plus, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

export type AutomationStepDraft = {
  step_order: number
  action_type: string
  delay_minutes: number
  config: {
    subject?: string
    body?: string
    template_id?: string
  }
}

export type AutomationDraft = {
  name: string
  trigger_event: string
  is_active: boolean
  steps: AutomationStepDraft[]
}

const TRIGGER_OPTIONS = [
  { value: 'lead_created', label: 'New lead created' },
  { value: 'quote_sent', label: 'Quote sent' },
  { value: 'job_completed', label: 'Job completed' },
  { value: 'booking_confirmed', label: 'Booking confirmed' },
  { value: 'invoice_sent', label: 'Invoice sent' },
]

const ACTION_OPTIONS = [
  { value: 'send_sms', label: 'Send SMS', icon: MessageSquare },
  { value: 'send_email', label: 'Send email', icon: Mail },
  { value: 'wait', label: 'Wait (delay on next step)', icon: Loader2 },
]

type Props = {
  initial: AutomationDraft
  saving?: boolean
  submitLabel: string
  onSubmit: (draft: AutomationDraft) => void
}

export function AutomationBuilderForm({ initial, saving, submitLabel, onSubmit }: Props) {
  const [draft, setDraft] = useState<AutomationDraft>(initial)

  useEffect(() => {
    setDraft(initial)
  }, [initial])

  const updateStep = (idx: number, patch: Partial<AutomationStepDraft>) => {
    setDraft((d) => ({
      ...d,
      steps: d.steps.map((step, i) => (i === idx ? { ...step, ...patch, config: { ...step.config, ...(patch.config || {}) } } : step)),
    }))
  }

  const addStep = () => {
    setDraft((d) => ({
      ...d,
      steps: [
        ...d.steps,
        {
          step_order: d.steps.length,
          action_type: 'send_email',
          delay_minutes: 0,
          config: { subject: '', body: '' },
        },
      ],
    }))
  }

  const removeStep = (idx: number) => {
    setDraft((d) => ({
      ...d,
      steps: d.steps.filter((_, i) => i !== idx).map((step, i) => ({ ...step, step_order: i })),
    }))
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Card>
        <CardContent className="space-y-4 p-5">
          <div>
            <Label htmlFor="automation-name">Workflow name</Label>
            <Input
              id="automation-name"
              value={draft.name}
              onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
              className="mt-1 text-lg font-semibold"
            />
          </div>
          <div>
            <Label htmlFor="automation-trigger">Trigger</Label>
            <select
              id="automation-trigger"
              value={draft.trigger_event}
              onChange={(e) => setDraft((d) => ({ ...d, trigger_event: e.target.value }))}
              className="mt-1 flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {TRIGGER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={draft.is_active}
              onChange={(e) => setDraft((d) => ({ ...d, is_active: e.target.checked }))}
            />
            Active when saved
          </label>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Steps</h2>
          <Button type="button" variant="outline" size="sm" onClick={addStep}>
            <Plus className="mr-1 h-4 w-4" /> Add step
          </Button>
        </div>

        {draft.steps.map((step, idx) => {
          const Icon = ACTION_OPTIONS.find((a) => a.value === step.action_type)?.icon || Mail
          return (
            <Card key={idx}>
              <CardContent className="space-y-3 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Icon className="h-4 w-4 text-brand-forest-700" />
                    Step {idx + 1}
                  </div>
                  {draft.steps.length > 1 && (
                    <Button type="button" variant="ghost" size="sm" onClick={() => removeStep(idx)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <Label>Action</Label>
                    <select
                      value={step.action_type}
                      onChange={(e) => updateStep(idx, { action_type: e.target.value })}
                      className="mt-1 flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
                    >
                      {ACTION_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label>Delay before next step (minutes)</Label>
                    <Input
                      type="number"
                      min={0}
                      value={step.delay_minutes}
                      onChange={(e) => updateStep(idx, { delay_minutes: Number(e.target.value) || 0 })}
                      className="mt-1"
                    />
                  </div>
                </div>

                {step.action_type === 'send_email' && (
                  <div>
                    <Label>Email subject</Label>
                    <Input
                      value={step.config.subject || ''}
                      onChange={(e) => updateStep(idx, { config: { subject: e.target.value } })}
                      className="mt-1"
                      placeholder="Thanks for getting in touch — {{business_name}}"
                    />
                  </div>
                )}

                {(step.action_type === 'send_email' || step.action_type === 'send_sms') && (
                  <div>
                    <Label>{step.action_type === 'send_sms' ? 'SMS body' : 'Email body'}</Label>
                    <Textarea
                      value={step.config.body || ''}
                      onChange={(e) => updateStep(idx, { config: { body: e.target.value } })}
                      className="mt-1 min-h-[120px] font-mono text-sm"
                      placeholder="Hi {{first_name}}, ..."
                    />
                    <p className="mt-1 text-xs text-muted-foreground">
                      Tokens: {'{{first_name}}'}, {'{{business_name}}'}, {'{{quote_url}}'}, {'{{review_url}}'}, {'{{booking_url}}'}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Button
        onClick={() => onSubmit(draft)}
        disabled={saving || !draft.name.trim() || draft.steps.length === 0}
        className="bg-brand-forest-700 hover:bg-brand-forest-800"
      >
        {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        {submitLabel}
      </Button>
    </div>
  )
}

export { TRIGGER_OPTIONS, ACTION_OPTIONS }
