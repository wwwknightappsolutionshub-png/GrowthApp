'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  Loader2,
  Mail,
  MessageSquare,
  Phone,
  Plus,
  Sparkles,
  Trash2,
} from 'lucide-react'
import {
  outreach,
  segments,
  type OutreachChannel,
  type OutreachStep,
  type OutreachStepCondition,
} from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { RichTextEditor } from '@/components/editor/RichTextEditor'

type SegmentSummary = {
  id: string
  name: string
  description: string | null
  size: number
}

const CHANNEL_ICON: Record<OutreachChannel, React.ComponentType<{ className?: string }>> = {
  sms: Phone,
  email: Mail,
  whatsapp: MessageSquare,
}

export default function NewCampaignPage() {
  const router = useRouter()
  const [name, setName] = useState('New campaign')
  const [description, setDescription] = useState('')
  const [segmentId, setSegmentId] = useState<string>('')
  const [steps, setSteps] = useState<OutreachStep[]>([
    { channel: 'email', subject: '', body: '', delay_hours: 0, condition: 'always', label: 'Step 1' },
  ])
  const [error, setError] = useState<string>('')

  const { data: segmentList } = useQuery<SegmentSummary[]>({
    queryKey: ['segments'],
    queryFn: () => segments.list().then((r) => r.data),
  })

  const create = useMutation({
    mutationFn: () =>
      outreach.create({
        name,
        description: description || undefined,
        audience: segmentId ? { segment_id: segmentId } : { filter: {} },
        steps,
      }),
    onSuccess: (res) => router.push(`/dashboard/outreach/${res.data.id}`),
    onError: (err: Error) => setError(err.message || 'Failed to create campaign'),
  })

  const updateStep = (idx: number, patch: Partial<OutreachStep>) => {
    setSteps((s) => s.map((step, i) => (i === idx ? { ...step, ...patch } : step)))
  }
  const addStep = () => {
    setSteps((s) => [
      ...s,
      {
        channel: s[s.length - 1]?.channel || 'email',
        subject: '',
        body: '',
        delay_hours: 24,
        condition: 'no_reply',
        label: `Step ${s.length + 1}`,
      },
    ])
  }
  const removeStep = (idx: number) => setSteps((s) => s.filter((_, i) => i !== idx))

  return (
    <div className="space-y-6 max-w-4xl">
      <Button variant="ghost" size="sm" onClick={() => router.back()}>
        <ArrowLeft className="w-4 h-4" /> Back to campaigns
      </Button>

      <Card>
        <CardContent className="p-5 space-y-4">
          <Label>Campaign</Label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Campaign name"
            className="text-lg font-semibold h-11"
          />
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Internal description (optional)"
            rows={2}
          />

          <div>
            <Label>Audience (customer segment)</Label>
            <select
              value={segmentId}
              onChange={(e) => setSegmentId(e.target.value)}
              className="mt-1 flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">— Choose a saved segment —</option>
              {segmentList?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.size} customers)
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      <section className="space-y-3">
        <header className="flex items-center justify-between">
          <Label className="text-sm">Sequence</Label>
          <Button variant="ghost" size="sm" onClick={addStep}>
            <Plus className="w-4 h-4" /> Add step
          </Button>
        </header>
        {steps.map((step, idx) => (
          <StepCard
            key={idx}
            index={idx}
            step={step}
            onChange={(patch) => updateStep(idx, patch)}
            onRemove={steps.length > 1 ? () => removeStep(idx) : undefined}
          />
        ))}
      </section>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="flex items-center justify-end gap-2">
        <Button variant="ghost" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button
          onClick={() => create.mutate()}
          disabled={create.isPending || !name.trim() || steps.some((s) => !s.body.trim())}
        >
          {create.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
          Save as draft
        </Button>
      </div>
    </div>
  )
}

function StepCard({
  index,
  step,
  onChange,
  onRemove,
}: {
  index: number
  step: OutreachStep
  onChange: (patch: Partial<OutreachStep>) => void
  onRemove?: () => void
}) {
  const Icon = CHANNEL_ICON[step.channel]
  const aiDraft = useMutation({
    mutationFn: (goal: string) =>
      outreach.draftStep({
        channel: step.channel,
        goal,
        tone: 'friendly, concise',
      }),
    onSuccess: (res) => {
      const data = res.data as { subject?: string | null; body: string }
      onChange({
        body: data.body || step.body,
        subject: data.subject ?? step.subject,
      })
    },
  })

  return (
    <Card>
      <CardContent className="p-5">
        <header className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="w-7 h-7 rounded-full justify-center p-0">
              {index + 1}
            </Badge>
            <div className="text-sm font-medium flex items-center gap-1.5">
              <Icon className="w-4 h-4 text-muted-foreground" />
              {step.label || `Step ${index + 1}`}
            </div>
          </div>
          {onRemove && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onRemove}
              className="text-muted-foreground hover:text-destructive"
              title="Remove step"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          )}
        </header>

        <div className="grid sm:grid-cols-3 gap-3 mb-3">
          <Select
            label="Channel"
            value={step.channel}
            options={['email', 'sms', 'whatsapp']}
            onChange={(v) => onChange({ channel: v as OutreachChannel })}
          />
          <NumberField
            label="Delay (hours)"
            value={step.delay_hours}
            onChange={(v) => onChange({ delay_hours: v })}
            min={0}
            disabled={index === 0}
            hint={index === 0 ? 'Send immediately on launch' : undefined}
          />
          <Select
            label="Condition"
            value={step.condition}
            options={['always', 'no_reply', 'replied', 'opened']}
            onChange={(v) => onChange({ condition: v as OutreachStepCondition })}
          />
        </div>

        {step.channel === 'email' && (
          <div className="mb-3">
            <Label>Subject</Label>
            <Input
              value={step.subject || ''}
              onChange={(e) => onChange({ subject: e.target.value })}
              className="mt-1"
              placeholder="Subject line"
            />
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-1">
            <Label>Message body</Label>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const goal =
                  prompt('Goal of this step?', step.label || 'Re-engage the customer') || ''
                if (goal) aiDraft.mutate(goal)
              }}
              disabled={aiDraft.isPending}
              className="h-6 text-xs"
            >
              {aiDraft.isPending ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              AI draft
            </Button>
          </div>
          {step.channel === 'email' ? (
            <RichTextEditor
              value={step.body}
              onChange={(html) => onChange({ body: html })}
              placeholder="Hi {{first_name}}, ..."
            />
          ) : (
            <Textarea
              value={step.body}
              onChange={(e) => onChange({ body: e.target.value })}
              rows={5}
              className="font-mono"
              placeholder="Hi {{first_name}}, ..."
            />
          )}
          <p className="text-xs text-muted-foreground mt-1">
            Tokens: <code className="text-[11px]">{'{{first_name}}'}</code>,{' '}
            <code className="text-[11px]">{'{{full_name}}'}</code>,{' '}
            <code className="text-[11px]">{'{{business_name}}'}</code>,{' '}
            <code className="text-[11px]">{'{{business_phone}}'}</code>
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: string[]
  onChange: (v: string) => void
}) {
  return (
    <div>
      <Label>{label}</Label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm capitalize shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o.replace('_', ' ')}
          </option>
        ))}
      </select>
    </div>
  )
}

function NumberField({
  label,
  value,
  onChange,
  min,
  disabled,
  hint,
}: {
  label: string
  value: number
  onChange: (v: number) => void
  min?: number
  disabled?: boolean
  hint?: string
}) {
  return (
    <div>
      <Label>{label}</Label>
      <Input
        type="number"
        min={min}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(parseInt(e.target.value || '0', 10))}
        className="mt-1"
      />
      {hint && <p className="text-[10px] text-muted-foreground mt-0.5">{hint}</p>}
    </div>
  )
}
