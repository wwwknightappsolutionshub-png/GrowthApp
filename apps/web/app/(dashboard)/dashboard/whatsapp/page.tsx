'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Loader2,
  Send,
  Sparkles,
  Wand2,
  MessageSquareText,
  Activity,
  Filter,
} from 'lucide-react'
import { toast } from 'sonner'

import { whatsapp } from '@/lib/api-client'

interface ConversationSummary {
  id: string
  customer_id: string | null
  customer_phone: string | null
  customer_name: string | null
  last_message_at: string | null
  is_resolved: boolean
  unread_count: number
  last_preview: string | null
  last_direction: 'inbound' | 'outbound' | null
}

interface MessageItem {
  id: string
  direction: 'inbound' | 'outbound'
  body: string
  from_address: string | null
  to_address: string | null
  status: string
  created_at: string
}

interface ConversationDetail extends ConversationSummary {
  messages: MessageItem[]
}

interface Sentiment {
  label: 'positive' | 'neutral' | 'negative' | 'urgent'
  score: number
  reason: string | null
}

interface Summary {
  summary: string
  bullets: string[]
  next_action: string | null
}

interface Suggestion {
  suggestion: string
  tone: string
  requires_review: boolean
}

type StatusFilter = 'all' | 'open' | 'resolved'

export default function WhatsAppPage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<StatusFilter>('open')
  const [activeId, setActiveId] = useState<string | null>(null)
  const [detail, setDetail] = useState<ConversationDetail | null>(null)
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)

  // AI state
  const [aiLoading, setAiLoading] = useState<string | null>(null)
  const [sentiment, setSentiment] = useState<Sentiment | null>(null)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null)

  const refresh = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true)
    try {
      const status_filter = filter === 'all' ? undefined : filter
      const res = await whatsapp.listConversations({ status_filter })
      const rows = res.data as ConversationSummary[]
      setConversations(rows)
      if (!activeId && rows.length) setActiveId(rows[0].id)
    } catch (err) {
      console.error(err)
      toast.error('Failed to load WhatsApp conversations')
    } finally {
      setLoading(false)
    }
  }, [filter, activeId])

  useEffect(() => {
    void refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter])

  useEffect(() => {
    if (!activeId) {
      setDetail(null)
      return
    }
    let cancelled = false
    whatsapp
      .getConversation(activeId)
      .then((res) => {
        if (!cancelled) setDetail(res.data as ConversationDetail)
      })
      .catch(() => toast.error('Could not load conversation'))
    // reset AI state when switching conversation
    setSentiment(null)
    setSummary(null)
    setSuggestion(null)
    return () => {
      cancelled = true
    }
  }, [activeId])

  async function send() {
    if (!detail || !draft.trim() || !detail.customer_phone) return
    setSending(true)
    try {
      await whatsapp.send({
        to: detail.customer_phone,
        body: draft.trim(),
        customer_id: detail.customer_id ?? undefined,
      })
      setDraft('')
      toast.success('Message queued')
      // refresh detail + list
      const res = await whatsapp.getConversation(detail.id)
      setDetail(res.data as ConversationDetail)
      void refresh({ silent: true })
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e.response?.data?.detail || 'Send failed')
    } finally {
      setSending(false)
    }
  }

  async function resolve(resolved: boolean) {
    if (!detail) return
    try {
      await whatsapp.resolve(detail.id, resolved)
      toast.success(resolved ? 'Conversation closed' : 'Re-opened')
      void refresh({ silent: true })
    } catch {
      toast.error('Could not update conversation')
    }
  }

  async function runAI(kind: 'sentiment' | 'summary' | 'suggest') {
    if (!detail) return
    setAiLoading(kind)
    try {
      if (kind === 'sentiment') {
        const res = await whatsapp.sentiment(detail.id)
        setSentiment(res.data as Sentiment)
      } else if (kind === 'summary') {
        const res = await whatsapp.summarise(detail.id)
        setSummary(res.data as Summary)
      } else {
        const res = await whatsapp.suggestReply(detail.id)
        const data = res.data as Suggestion
        setSuggestion(data)
        setDraft(data.suggestion)
      }
    } catch (err) {
      console.error(err)
      toast.error('AI request failed')
    } finally {
      setAiLoading(null)
    }
  }

  return (
    <div className="grid h-[calc(100vh-4rem)] grid-cols-[320px_1fr] overflow-hidden">
      {/* ── Conversation list ───────────────────────────────────────── */}
      <aside className="flex flex-col border-r border-border bg-card">
        <header className="flex h-14 items-center justify-between border-b border-border px-4">
          <div>
            <h2 className="text-sm font-semibold">WhatsApp Inbox</h2>
            <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              {conversations.length} threads
            </p>
          </div>
          <div className="inline-flex items-center gap-1 rounded-md border border-border bg-background p-0.5">
            {(['open', 'all', 'resolved'] as StatusFilter[]).map((f) => (
              <button
                type="button"
                key={f}
                onClick={() => setFilter(f)}
                className={`rounded-sm px-2 py-1 text-[10px] font-semibold uppercase tracking-wider transition-colors ${
                  filter === f
                    ? 'bg-brand-forest-700 text-brand-forest-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </header>
        <div className="flex-1 overflow-y-auto">
          {loading && conversations.length === 0 ? (
            <p className="p-4 text-xs text-muted-foreground">Loading…</p>
          ) : conversations.length === 0 ? (
            <div className="px-4 py-10 text-center">
              <p className="text-xs text-muted-foreground">
                No WhatsApp conversations yet.
              </p>
              <p className="mt-2 text-[10px] text-muted-foreground/70">
                When a customer messages you on WhatsApp Business, it lands here
                with an AI-drafted reply.
              </p>
            </div>
          ) : (
            <ul>
              {conversations.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => setActiveId(c.id)}
                    className={`flex w-full items-start gap-3 border-b border-border px-4 py-3 text-left transition-colors hover:bg-muted/40 ${
                      activeId === c.id ? 'bg-brand-forest-50/50' : ''
                    }`}
                  >
                    <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-forest-700 font-mono text-[10px] font-bold text-brand-forest-foreground">
                      {initialsFromPhone(c.customer_name, c.customer_phone)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate text-sm font-semibold text-foreground">
                          {c.customer_name || c.customer_phone || 'Unknown'}
                        </p>
                        {c.last_message_at && (
                          <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                            {formatTime(c.last_message_at)}
                          </span>
                        )}
                      </div>
                      <p className="truncate text-xs leading-snug text-muted-foreground">
                        {c.last_direction === 'outbound' ? '↗ ' : '↘ '}
                        {c.last_preview || '—'}
                      </p>
                      <div className="mt-1 flex items-center gap-2">
                        {c.is_resolved ? (
                          <span className="inline-flex items-center gap-1 font-mono text-[9px] uppercase tracking-wider text-emerald-600">
                            <CheckCircle2 className="h-2.5 w-2.5" /> closed
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 font-mono text-[9px] uppercase tracking-wider text-brand-teal-600">
                            <Activity className="h-2.5 w-2.5" /> open
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* ── Detail + AI assist ─────────────────────────────────────── */}
      <section className="flex flex-col bg-background">
        {!detail ? (
          <div className="flex flex-1 items-center justify-center text-center text-sm text-muted-foreground">
            <div>
              <MessageSquareText className="mx-auto h-8 w-8 text-muted-foreground/40" />
              <p className="mt-3">Select a conversation to begin.</p>
            </div>
          </div>
        ) : (
          <ConversationView
            detail={detail}
            draft={draft}
            sending={sending}
            sentiment={sentiment}
            summary={summary}
            suggestion={suggestion}
            aiLoading={aiLoading}
            onDraftChange={setDraft}
            onSend={send}
            onResolve={resolve}
            onAI={runAI}
          />
        )}
      </section>
    </div>
  )
}

interface ConversationViewProps {
  detail: ConversationDetail
  draft: string
  sending: boolean
  sentiment: Sentiment | null
  summary: Summary | null
  suggestion: Suggestion | null
  aiLoading: string | null
  onDraftChange: (v: string) => void
  onSend: () => void
  onResolve: (resolved: boolean) => void
  onAI: (kind: 'sentiment' | 'summary' | 'suggest') => void
}

function ConversationView({
  detail,
  draft,
  sending,
  sentiment,
  summary,
  suggestion,
  aiLoading,
  onDraftChange,
  onSend,
  onResolve,
  onAI,
}: ConversationViewProps) {
  const scrollerRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (scrollerRef.current) {
      scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight
    }
  }, [detail.id, detail.messages.length])

  const sentimentTone = useMemo(() => {
    if (!sentiment) return null
    const map: Record<Sentiment['label'], string> = {
      positive: 'bg-emerald-500/15 text-emerald-700',
      neutral: 'bg-muted text-muted-foreground',
      negative: 'bg-orange-500/15 text-orange-700',
      urgent: 'bg-rose-500/15 text-rose-700',
    }
    return map[sentiment.label]
  }, [sentiment])

  return (
    <>
      <header className="flex h-16 items-center justify-between border-b border-border bg-card px-6">
        <div>
          <p className="text-sm font-semibold text-foreground">
            {detail.customer_name || detail.customer_phone || 'Unknown contact'}
          </p>
          <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            WhatsApp · {detail.customer_phone || '—'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <AiButton
            label="Sentiment"
            icon={Activity}
            loading={aiLoading === 'sentiment'}
            onClick={() => onAI('sentiment')}
          />
          <AiButton
            label="Summarise"
            icon={Filter}
            loading={aiLoading === 'summary'}
            onClick={() => onAI('summary')}
          />
          <AiButton
            label="Suggest reply"
            icon={Wand2}
            loading={aiLoading === 'suggest'}
            onClick={() => onAI('suggest')}
            primary
          />
          <button
            type="button"
            onClick={() => onResolve(!detail.is_resolved)}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:bg-muted/40"
          >
            {detail.is_resolved ? 'Re-open' : 'Mark resolved'}
          </button>
        </div>
      </header>

      {(sentiment || summary) && (
        <div className="grid grid-cols-1 gap-3 border-b border-border bg-muted/30 px-6 py-4 lg:grid-cols-2">
          {sentiment && (
            <div className="rounded-md border border-border bg-card p-4">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                AI sentiment
              </p>
              <div className="mt-2 flex items-center gap-3">
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-bold uppercase tracking-wider ${sentimentTone}`}
                >
                  {sentiment.label}
                </span>
                <span className="font-mono text-xs text-muted-foreground">
                  Score {sentiment.score.toFixed(2)}
                </span>
              </div>
              {sentiment.reason && (
                <p className="mt-2 text-xs text-muted-foreground">
                  {sentiment.reason}
                </p>
              )}
            </div>
          )}
          {summary && (
            <div className="rounded-md border border-border bg-card p-4">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                AI summary
              </p>
              <p className="mt-1.5 text-xs leading-relaxed text-foreground">
                {summary.summary}
              </p>
              {summary.bullets.length > 0 && (
                <ul className="mt-2 list-disc space-y-0.5 pl-4 text-[11px] text-muted-foreground">
                  {summary.bullets.map((b, i) => (
                    <li key={i}>{b}</li>
                  ))}
                </ul>
              )}
              {summary.next_action && (
                <p className="mt-2 inline-flex items-center gap-1 rounded-md bg-brand-forest-50 px-2 py-0.5 text-[11px] font-semibold text-brand-forest-700">
                  Next: {summary.next_action}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      <div ref={scrollerRef} className="flex-1 overflow-y-auto px-6 py-6">
        {detail.messages.length === 0 ? (
          <p className="text-center text-sm text-muted-foreground">No messages yet.</p>
        ) : (
          <ul className="space-y-3">
            {detail.messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
          </ul>
        )}
      </div>

      <footer className="border-t border-border bg-card px-6 py-4">
        {suggestion && suggestion.requires_review && (
          <div className="mb-2 flex items-center gap-2 rounded-md border border-brand-teal-300 bg-brand-teal-50/60 px-3 py-1.5 text-[11px] text-brand-forest-800">
            <Sparkles className="h-3 w-3" />
            AI draft loaded into the box — review before sending.
          </div>
        )}
        <div className="flex items-end gap-2">
          <textarea
            value={draft}
            onChange={(e) => onDraftChange(e.target.value)}
            rows={2}
            placeholder="Type a WhatsApp message…"
            className="flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:border-brand-forest-400 focus:outline-none focus:ring-2 focus:ring-brand-forest-400/30"
          />
          <button
            type="button"
            onClick={onSend}
            disabled={sending || !draft.trim()}
            className="inline-flex h-10 items-center gap-2 rounded-md bg-brand-forest-700 px-4 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-colors hover:bg-brand-forest-800 disabled:opacity-50"
          >
            {sending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            Send
          </button>
        </div>
      </footer>
    </>
  )
}

function MessageBubble({ message }: { message: MessageItem }) {
  const isOutbound = message.direction === 'outbound'
  return (
    <li className={`flex ${isOutbound ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-2.5 shadow-soft ${
          isOutbound
            ? 'bg-brand-forest-700 text-brand-forest-foreground'
            : 'bg-card text-foreground'
        }`}
      >
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.body}</p>
        <div
          className={`mt-1 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider ${
            isOutbound ? 'text-white/65' : 'text-muted-foreground'
          }`}
        >
          {message.status === 'sent' ? (
            <CheckCircle2 className="h-3 w-3" />
          ) : message.status === 'failed' ? (
            <AlertCircle className="h-3 w-3" />
          ) : (
            <Clock className="h-3 w-3" />
          )}
          {formatTime(message.created_at)} · {message.status}
        </div>
      </div>
    </li>
  )
}

function AiButton({
  label,
  icon: Icon,
  loading,
  onClick,
  primary,
}: {
  label: string
  icon: React.ComponentType<{ className?: string }>
  loading: boolean
  onClick: () => void
  primary?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading}
      className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors disabled:opacity-50 ${
        primary
          ? 'bg-brand-teal-400 text-brand-teal-foreground hover:bg-brand-teal-300'
          : 'border border-border bg-background text-foreground hover:bg-muted/40'
      }`}
    >
      {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Icon className="h-3 w-3" />}
      {label}
    </button>
  )
}

function initialsFromPhone(name: string | null, phone: string | null): string {
  if (name) {
    const parts = name
      .trim()
      .split(/\s+/)
      .filter(Boolean)
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  }
  if (phone) return phone.slice(-2)
  return '??'
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    const now = new Date()
    const sameDay =
      d.getFullYear() === now.getFullYear() &&
      d.getMonth() === now.getMonth() &&
      d.getDate() === now.getDate()
    return sameDay
      ? d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
      : d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
  } catch {
    return ''
  }
}
