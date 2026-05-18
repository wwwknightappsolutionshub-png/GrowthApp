'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { automations } from '@/lib/api-client'
import { toast } from 'sonner'
import { Zap, ToggleLeft, ToggleRight, Trash2 } from 'lucide-react'
import { formatDate } from '@/lib/utils'

const EVENT_LABELS: Record<string, string> = {
  lead_created: 'New lead created',
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

export default function AutomationsPage() {
  const qc = useQueryClient()

  const { data: automationList, isLoading } = useQuery({
    queryKey: ['automations'],
    queryFn: () => automations.list().then(r => r.data),
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
    },
    onError: () => toast.error('Failed to delete automation'),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Automations</h1>
          <p className="text-muted-foreground text-sm">Automatic follow-ups and workflows that run 24/7</p>
        </div>
        <span className="text-sm text-muted-foreground">{automationList?.length ?? 0} automations</span>
      </div>

      {/* Info banner */}
      <div className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-4 text-sm text-brand-teal-50 shadow-sm">
        <strong>Tip:</strong> Automations fire automatically when events occur (e.g., new lead, job completed). Each step can send an SMS, email, or wait before the next action.
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="grid gap-4">
          {automationList?.length === 0 && (
            <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-12 text-center">
              <Zap className="w-10 h-10 mx-auto mb-3 text-brand-teal-300/70" />
              <p className="font-medium text-brand-teal-50">No automations yet</p>
              <p className="text-sm text-brand-teal-100/70 mt-1">Automations are pre-configured during onboarding. Contact support to set up custom sequences.</p>
            </div>
          )}
          {automationList?.map((automation: any) => (
            <div key={automation.id} className={`rounded-xl border bg-brand-forest-950 p-5 shadow-sm ${automation.is_active ? 'border-brand-forest-700' : 'border-brand-forest-900 opacity-70'}`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-semibold text-white">{automation.name}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${automation.is_active ? 'bg-brand-teal-400/20 text-brand-teal-100 ring-1 ring-brand-teal-300/30' : 'bg-brand-forest-800 text-brand-teal-100/70'}`}>
                      {automation.is_active ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  <p className="text-sm text-brand-teal-100/70">
                    Trigger: <span className="font-medium text-brand-teal-50">{EVENT_LABELS[automation.trigger_event] || automation.trigger_event}</span>
                  </p>
                  {automation.steps?.length > 0 && (
                    <div className="flex items-center gap-2 mt-3 flex-wrap">
                      {automation.steps.map((step: any, i: number) => (
                        <div key={step.id} className="flex items-center gap-1">
                          <span className="text-xs bg-brand-forest-800 text-brand-teal-100/80 px-2 py-1 rounded">
                            {ACTION_LABELS[step.action_type] || step.action_type}
                            {step.delay_minutes > 0 && ` (+${step.delay_minutes}m)`}
                          </span>
                          {i < automation.steps.length - 1 && <span className="text-brand-teal-100/40 text-xs">→</span>}
                        </div>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-brand-teal-100/60 mt-3">Created {formatDate(automation.created_at)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => toggleMutation.mutate({ id: automation.id, is_active: !automation.is_active })}
                    disabled={toggleMutation.isPending}
                    className="text-brand-teal-100/60 hover:text-white disabled:opacity-40"
                    title={automation.is_active ? 'Pause automation' : 'Activate automation'}
                  >
                    {automation.is_active
                      ? <ToggleRight className="w-7 h-7 text-green-500" />
                      : <ToggleLeft className="w-7 h-7" />}
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Delete this automation?')) deleteMutation.mutate(automation.id)
                    }}
                    disabled={deleteMutation.isPending}
                    className="text-brand-teal-100/50 hover:text-red-300 disabled:opacity-40"
                  >
                    <Trash2 className="w-4 h-4" />
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
