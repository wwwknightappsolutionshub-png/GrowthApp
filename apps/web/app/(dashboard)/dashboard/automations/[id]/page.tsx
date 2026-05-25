'use client'

import { useMemo } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { toast } from 'sonner'

import {
  AutomationBuilderForm,
  type AutomationDraft,
} from '@/components/automations/AutomationBuilderForm'
import { Button } from '@/components/ui/button'
import { automations } from '@/lib/api-client'

type AutomationRecord = {
  id: string
  name: string
  trigger_event: string
  is_active: boolean
  steps: Array<{
    step_order: number
    action_type: string
    delay_minutes: number
    config: Record<string, string>
  }>
}

export default function EditAutomationPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['automation', id],
    queryFn: () => automations.get(id).then((r) => r.data as AutomationRecord),
    enabled: Boolean(id),
  })

  const initial = useMemo<AutomationDraft | null>(() => {
    if (!data) return null
    return {
      name: data.name,
      trigger_event: data.trigger_event,
      is_active: data.is_active,
      steps: [...data.steps]
        .sort((a, b) => a.step_order - b.step_order)
        .map((step) => ({
          step_order: step.step_order,
          action_type: step.action_type,
          delay_minutes: step.delay_minutes,
          config: {
            subject: step.config?.subject,
            body: step.config?.body,
            template_id: step.config?.template_id,
          },
        })),
    }
  }, [data])

  const save = useMutation({
    mutationFn: (draft: AutomationDraft) =>
      automations.update(id, {
        name: draft.name,
        trigger_event: draft.trigger_event,
        is_active: draft.is_active,
        steps: draft.steps,
      }),
    onSuccess: () => {
      toast.success('Automation saved')
      qc.invalidateQueries({ queryKey: ['automations'] })
      qc.invalidateQueries({ queryKey: ['automation', id] })
    },
    onError: () => toast.error('Failed to save automation'),
  })

  if (isLoading || !initial) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-brand-forest-700" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/automations')}>
        <ArrowLeft className="mr-1 h-4 w-4" /> Back to automations
      </Button>
      <div>
        <h1 className="text-2xl font-bold text-foreground">Edit automation</h1>
        <p className="text-sm text-muted-foreground">Update triggers, steps, and message content.</p>
      </div>
      <AutomationBuilderForm
        initial={initial}
        saving={save.isPending}
        submitLabel="Save changes"
        onSubmit={(draft) => save.mutate(draft)}
      />
    </div>
  )
}
