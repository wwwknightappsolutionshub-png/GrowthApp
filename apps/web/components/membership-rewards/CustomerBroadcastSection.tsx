'use client'

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { BellRing, Mail, Megaphone } from 'lucide-react'
import { toast } from 'sonner'
import { membershipRewards } from '@/lib/api-client'

export function CustomerBroadcastSection() {
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [sendPush, setSendPush] = useState(true)
  const [sendEmail, setSendEmail] = useState(false)

  const { data: preview } = useQuery({
    queryKey: ['membership-customer-broadcast-preview'],
    queryFn: () => membershipRewards.previewCustomerBroadcast().then((r) => r.data),
  })

  const send = useMutation({
    mutationFn: () =>
      membershipRewards.sendCustomerBroadcast({
        title: title.trim(),
        body: body.trim(),
        send_push: sendPush,
        send_email: sendEmail,
      }),
    onSuccess: (res) => {
      toast.success(
        `Sent to ${res.data.push_sent} push subscriber(s) and ${res.data.email_sent} email recipient(s)`,
      )
      setTitle('')
      setBody('')
    },
    onError: () => toast.error('Could not send customer message'),
  })

  return (
    <section className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <Megaphone className="mt-0.5 h-5 w-5 text-primary" />
        <div className="flex-1 space-y-4">
          <div>
            <h2 className="text-base font-semibold">Message wallet customers</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Send offers and updates to enrolled loyalty customers via push and/or email.
            </p>
            {preview ? (
              <p className="mt-2 text-xs text-muted-foreground">
                {preview.customers} enrolled · {preview.push_subscribers} push subscribers ·{' '}
                {preview.email_opted_in} email opt-in
              </p>
            ) : null}
          </div>

          <div className="space-y-3">
            <input
              className="w-full rounded-lg border bg-background px-3 py-2 text-sm"
              placeholder="Message title (e.g. Double points weekend)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <textarea
              className="min-h-[100px] w-full rounded-lg border bg-background px-3 py-2 text-sm"
              placeholder="Your offer or update message…"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
            <div className="flex flex-wrap gap-4 text-sm">
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={sendPush} onChange={(e) => setSendPush(e.target.checked)} />
                <BellRing className="h-4 w-4" />
                Push notification
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={sendEmail} onChange={(e) => setSendEmail(e.target.checked)} />
                <Mail className="h-4 w-4" />
                Email (marketing opt-in)
              </label>
            </div>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50"
              disabled={!title.trim() || !body.trim() || (!sendPush && !sendEmail) || send.isPending}
              onClick={() => send.mutate()}
            >
              {send.isPending ? 'Sending…' : 'Send to customers'}
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}
