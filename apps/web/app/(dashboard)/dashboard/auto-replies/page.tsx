'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, X, Loader2, Inbox } from 'lucide-react'
import { autoReplies } from '@/lib/api-client'
import { formatDistanceToNow } from 'date-fns'

type AutoReply = {
  id: string
  conversation_id: string
  channel: 'sms' | 'whatsapp' | 'email'
  draft: string
  status: 'pending' | 'approved' | 'rejected' | 'sent'
  rule: string | null
  provider: string | null
  model: string | null
  created_at: string
}

export default function AutoRepliesPage() {
  const [filter, setFilter] = useState<'pending' | 'sent' | 'rejected'>('pending')
  const qc = useQueryClient()
  const { data, isLoading } = useQuery<AutoReply[]>({
    queryKey: ['auto-replies', filter],
    queryFn: () => autoReplies.list(filter).then((r) => r.data),
    refetchInterval: filter === 'pending' ? 15_000 : false,
  })

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">AI Reply Queue</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Approve, edit, or reject AI-drafted responses to inbound customer messages.
          </p>
        </div>
        <nav className="flex items-center gap-1 bg-card border rounded-lg p-1 text-sm">
          {(['pending', 'sent', 'rejected'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-md capitalize transition-colors ${
                filter === s ? 'bg-blue-600 text-white' : 'text-muted-foreground hover:bg-gray-50'
              }`}
            >
              {s}
            </button>
          ))}
        </nav>
      </header>

      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-muted-foreground">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading...
        </div>
      ) : !data?.length ? (
        <EmptyState filter={filter} />
      ) : (
        <ul className="space-y-3">
          {data.map((r) => (
            <ReplyCard key={r.id} reply={r} qc={qc} editable={filter === 'pending'} />
          ))}
        </ul>
      )}
    </div>
  )
}

function EmptyState({ filter }: { filter: string }) {
  return (
    <div className="rounded-xl border bg-card py-16 flex flex-col items-center gap-3 text-muted-foreground">
      <Inbox className="w-10 h-10 text-gray-300" />
      <p className="text-sm">
        {filter === 'pending'
          ? 'Nothing waiting for review. Inbound messages will appear here as AI drafts them.'
          : `No ${filter} replies in this view.`}
      </p>
    </div>
  )
}

function ReplyCard({
  reply,
  qc,
  editable,
}: {
  reply: AutoReply
  qc: ReturnType<typeof useQueryClient>
  editable: boolean
}) {
  const [text, setText] = useState(reply.draft)
  const approve = useMutation({
    mutationFn: () => autoReplies.approve(reply.id, text !== reply.draft ? text : undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['auto-replies'] }),
  })
  const reject = useMutation({
    mutationFn: () => autoReplies.reject(reply.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['auto-replies'] }),
  })

  return (
    <li className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="rounded-full bg-blue-50 text-blue-700 px-2 py-0.5 capitalize">
            {reply.channel}
          </span>
          {reply.provider && (
            <span className="rounded-full bg-gray-100 px-2 py-0.5">
              {reply.provider}/{reply.model}
            </span>
          )}
          <span>· {formatDistanceToNow(new Date(reply.created_at))} ago</span>
        </div>
        {reply.status !== 'pending' && (
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {reply.status}
          </span>
        )}
      </div>

      {editable ? (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          className="w-full rounded-lg border bg-gray-50 p-3 text-sm font-medium leading-relaxed focus:bg-white focus:ring-2 focus:ring-blue-100"
        />
      ) : (
        <p className="rounded-lg bg-gray-50 p-3 text-sm leading-relaxed whitespace-pre-wrap">
          {reply.draft}
        </p>
      )}

      {editable && (
        <div className="mt-3 flex items-center justify-end gap-2">
          <button
            onClick={() => reject.mutate()}
            disabled={reject.isPending || approve.isPending}
            className="inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-sm text-muted-foreground hover:bg-gray-50 disabled:opacity-50"
          >
            <X className="w-4 h-4" /> Reject
          </button>
          <button
            onClick={() => approve.mutate()}
            disabled={approve.isPending || reject.isPending}
            className="inline-flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {approve.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Check className="w-4 h-4" />
            )}
            {text !== reply.draft ? 'Approve & send edited' : 'Approve & send'}
          </button>
        </div>
      )}
    </li>
  )
}
