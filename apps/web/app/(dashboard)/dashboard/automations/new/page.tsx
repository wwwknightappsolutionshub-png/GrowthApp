'use client'

import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { toast } from 'sonner'

import { AutomationBuilderForm, type AutomationDraft } from '@/components/automations/AutomationBuilderForm'
import { Button } from '@/components/ui/button'
import { automations } from '@/lib/api-client'

const DEFAULT_DRAFT: AutomationDraft = {
  name: 'New workflow',
  trigger_event: 'lead_created',
  is_active: true,
  steps: [
    {
      step_order: 0,
      action_type: 'send_sms',
      delay_minutes: 0,
      config: {
        body: 'Hi {{first_name}}, thanks for contacting {{business_name}}. We will be in touch shortly.',
      },
    },
  ],
}

export default function NewAutomationPage() {
  const router = useRouter()

  const create = useMutation({
    mutationFn: (draft: AutomationDraft) => automations.create(draft),
    onSuccess: (res) => {
      toast.success('Automation created')
      router.push(`/dashboard/automations/${res.data.id}`)
    },
    onError: () => toast.error('Failed to create automation'),
  })

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/automations')}>
        <ArrowLeft className="mr-1 h-4 w-4" /> Back to automations
      </Button>
      <div>
        <h1 className="text-2xl font-bold text-foreground">Create automation</h1>
        <p className="text-sm text-muted-foreground">Build a trigger-based SMS and email sequence.</p>
      </div>
      <AutomationBuilderForm
        initial={DEFAULT_DRAFT}
        saving={create.isPending}
        submitLabel="Create automation"
        onSubmit={(draft) => create.mutate(draft)}
      />
    </div>
  )
}
