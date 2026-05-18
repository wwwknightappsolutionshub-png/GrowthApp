'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { CheckCircle2, MessageCircle, XCircle } from 'lucide-react'
import { social } from '@/lib/api-client'
import { toast } from 'sonner'

export default function ApprovalFlowPage() {
  const [draftId, setDraftId] = useState('')
  const [responseText, setResponseText] = useState('')

  const respondMut = useMutation({
    mutationFn: ({ approved }: { approved: boolean }) =>
      social.approvalWebhook({
        draft_id: draftId,
        response_text: responseText || (approved ? 'APPROVE' : 'REVISE'),
        approved,
      }),
    onSuccess: (res) => {
      const status = res.data?.status
      toast.success(`Status updated → ${status}`)
      setResponseText('')
    },
    onError: () => toast.error('Failed to record response'),
  })

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <MessageCircle className="h-6 w-6 text-primary" /> Approval Flow
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          When you receive an approval email or WhatsApp message, paste the draft ID here and
          confirm or request changes.
        </p>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium mb-1">Draft ID</label>
          <input
            value={draftId}
            onChange={(e) => setDraftId(e.target.value)}
            placeholder="e.g. 8e6b2a3f-…"
            className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm font-mono"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Notes (optional)</label>
          <textarea
            value={responseText}
            onChange={(e) => setResponseText(e.target.value)}
            placeholder='"Looks great" / "Please change the headline to…"'
            rows={3}
            className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm"
          />
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => {
              if (!draftId) return toast.error('Add a draft ID')
              respondMut.mutate({ approved: true })
            }}
            disabled={respondMut.isPending}
            className="flex items-center gap-2 rounded-lg bg-green-600 px-5 py-3 text-sm font-semibold text-white hover:bg-green-500 disabled:opacity-60"
          >
            <CheckCircle2 className="h-4 w-4" /> Approve & auto-schedule
          </button>
          <button
            onClick={() => {
              if (!draftId) return toast.error('Add a draft ID')
              respondMut.mutate({ approved: false })
            }}
            disabled={respondMut.isPending}
            className="flex items-center gap-2 rounded-lg bg-amber-500 px-5 py-3 text-sm font-semibold text-white hover:bg-amber-400 disabled:opacity-60"
          >
            <XCircle className="h-4 w-4" /> Request revision
          </button>
        </div>
      </div>

      <div className="bg-muted/40 border border-border rounded-xl p-4 text-xs text-muted-foreground">
        <strong>How it works:</strong> When a draft is sent for approval, you receive a message
        on email and/or WhatsApp containing the draft ID. Approve here to push it straight into
        the publishing schedule, or request a revision to send it back to the AI for re-work.
      </div>
    </div>
  )
}
