'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, Sparkles } from 'lucide-react'
import { social } from '@/lib/api-client'
import { toast } from 'sonner'

interface Draft {
  id: string
  text: string
  status: 'PENDING' | 'APPROVED' | 'REVISE'
  notes?: string
}

export default function DraftReviewPage() {
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [count, setCount] = useState(3)
  const [topics, setTopics] = useState('')

  const generateMut = useMutation({
    mutationFn: () => {
      const hints = topics
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean)
      return social.generateDrafts({ count, topic_hints: hints.length ? hints : undefined })
    },
    onSuccess: (res) => {
      const ids: string[] = res.data?.draft_ids ?? []
      setDrafts((prev) => [
        ...ids.map((id, i) => ({
          id,
          text: `AI draft ${i + 1} — open from approval queue once sent`,
          status: 'PENDING' as const,
        })),
        ...prev,
      ])
      toast.success(`Generated ${ids.length} draft(s)`)
    },
    onError: () => toast.error('Failed to generate drafts'),
  })

  const sendMut = useMutation({
    mutationFn: ({ draft_id, channel }: { draft_id: string; channel: 'EMAIL' | 'WHATSAPP' }) =>
      social.sendForApproval({ draft_id, delivery_channel: channel }),
    onSuccess: () => toast.success('Sent for approval'),
    onError: () => toast.error('Failed to send for approval'),
  })

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" /> Draft Review
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Generate AI-written drafts based on your brand identity. Review them, then push to the
          approval queue.
        </p>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-[160px_1fr] gap-3">
          <div>
            <label className="block text-sm font-medium mb-1">How many drafts?</label>
            <input
              type="number"
              min={1}
              max={10}
              value={count}
              onChange={(e) => setCount(parseInt(e.target.value || '1', 10))}
              className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Topic hints (one per line)</label>
            <textarea
              rows={3}
              value={topics}
              onChange={(e) => setTopics(e.target.value)}
              placeholder={'Spring promotion\nNew product launch\nCustomer testimonial'}
              className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm"
            />
          </div>
        </div>
        <button
          onClick={() => generateMut.mutate()}
          disabled={generateMut.isPending}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
        >
          <Sparkles className="h-4 w-4" />
          {generateMut.isPending ? 'Generating…' : 'Generate drafts'}
        </button>
      </div>

      <div>
        <h2 className="text-sm font-semibold text-foreground mb-3">Recent drafts</h2>
        {drafts.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-8 text-center text-muted-foreground text-sm">
            No drafts yet. Generate your first batch above.
          </div>
        ) : (
          <div className="space-y-3">
            {drafts.map((d) => (
              <div key={d.id} className="bg-card border border-border rounded-xl p-5">
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      d.status === 'APPROVED'
                        ? 'bg-green-100 text-green-700'
                        : d.status === 'REVISE'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {d.status}
                  </span>
                  <span className="text-xs font-mono text-muted-foreground">
                    {d.id.slice(0, 8)}
                  </span>
                </div>
                <p className="text-sm text-foreground mb-3">{d.text}</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => sendMut.mutate({ draft_id: d.id, channel: 'EMAIL' })}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 text-xs font-semibold"
                  >
                    <Send className="h-3.5 w-3.5" /> Email approval
                  </button>
                  <button
                    onClick={() => sendMut.mutate({ draft_id: d.id, channel: 'WHATSAPP' })}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-100 text-green-700 hover:bg-green-200 text-xs font-semibold"
                  >
                    <Send className="h-3.5 w-3.5" /> WhatsApp approval
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
