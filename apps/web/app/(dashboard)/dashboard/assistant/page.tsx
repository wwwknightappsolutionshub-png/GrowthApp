'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bot, Plus, Send, Sparkles, User } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

import { aiAssistant } from '@/lib/api-client'

type Thread = {
  id: string
  title: string
  pinned: boolean
  last_message_at: string | null
  archived_at: string | null
  created_at: string
}

type Message = {
  id: string
  thread_id: string
  role: 'user' | 'assistant' | 'tool' | 'system'
  content: string
  tool_calls: Array<{ id: string; function: { name: string; arguments: string } }>
  tool_call_id: string | null
  provider: string | null
  model: string | null
  created_at: string
}

const SUGGESTED_PROMPTS = [
  'Show me my hottest leads this week',
  "What's stuck in my pipeline?",
  'Which invoices are overdue?',
  'Draft a follow-up message for my newest lead',
  'How many tasks am I overdue on?',
]

function ThreadList({
  threads,
  activeId,
  onSelect,
  onCreate,
}: {
  threads: Thread[]
  activeId: string | null
  onSelect: (id: string) => void
  onCreate: () => void
}) {
  return (
    <aside className="flex h-60 w-full shrink-0 flex-col border-b border-brand-forest-800 bg-brand-forest-950 lg:h-full lg:w-64 lg:border-b-0 lg:border-r">
      <div className="p-3 border-b border-brand-forest-800 bg-brand-forest-900">
        <button
          onClick={onCreate}
          className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-semibold text-brand-forest-foreground bg-brand-forest-700 rounded-lg hover:bg-brand-forest-800"
        >
          <Plus className="w-4 h-4" />
          New conversation
        </button>
      </div>
      <ul className="flex-1 overflow-y-auto p-2 space-y-1">
        {threads.length === 0 && (
          <li className="px-3 py-4 text-xs text-center text-brand-teal-100/60">No conversations yet.</li>
        )}
        {threads.map((t) => (
          <li key={t.id}>
            <button
              onClick={() => onSelect(t.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                activeId === t.id
                  ? 'bg-brand-forest-800 text-white font-semibold'
                  : 'text-brand-teal-100/80 hover:bg-brand-forest-900'
              }`}
            >
              <p className="line-clamp-2">{t.title}</p>
              <p className="text-[10px] text-brand-teal-100/60 mt-0.5">
                {t.last_message_at
                  ? new Date(t.last_message_at).toLocaleString()
                  : new Date(t.created_at).toLocaleString()}
              </p>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  )
}

function MessageBubble({ message }: { message: Message }) {
  if (message.role === 'tool') return null
  if (message.role === 'assistant' && !message.content && message.tool_calls?.length > 0) {
    return (
      <div className="flex items-start gap-3 my-3">
        <div className="w-7 h-7 rounded-full bg-brand-teal-400/20 flex items-center justify-center flex-shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-brand-teal-100" />
        </div>
        <div className="flex-1 text-xs text-brand-teal-100/60 italic mt-1.5">
          Looking up {message.tool_calls.map((tc) => tc.function.name).join(', ')}…
        </div>
      </div>
    )
  }

  const isUser = message.role === 'user'
  const Icon = isUser ? User : Bot
  return (
    <div className={`flex items-start gap-3 my-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? 'bg-brand-forest-700' : 'bg-brand-teal-400/20'
        }`}
      >
        <Icon className={`w-3.5 h-3.5 ${isUser ? 'text-brand-forest-foreground' : 'text-brand-teal-100'}`} />
      </div>
      <div className={`max-w-[80%] ${isUser ? 'text-right' : ''}`}>
        <div
          className={`inline-block px-3.5 py-2.5 rounded-2xl text-sm whitespace-pre-wrap leading-relaxed ${
            isUser
              ? 'bg-brand-forest-700 text-brand-forest-foreground rounded-tr-md'
              : 'bg-brand-forest-900 border border-brand-forest-700 text-brand-teal-50 rounded-tl-md'
          }`}
        >
          {message.content}
        </div>
        {!isUser && message.provider && (
          <p className="text-[10px] text-brand-teal-100/60 mt-1 ml-1">
            {message.provider} · {message.model}
          </p>
        )}
      </div>
    </div>
  )
}

function ChatView({ threadId }: { threadId: string | null }) {
  const qc = useQueryClient()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: messages, isLoading } = useQuery<Message[]>({
    queryKey: ['assistant-messages', threadId],
    queryFn: () =>
      threadId
        ? aiAssistant.listMessages(threadId).then((r) => r.data)
        : Promise.resolve([]),
    enabled: !!threadId,
  })

  const sendMutation = useMutation({
    mutationFn: ({ content }: { content: string }) =>
      aiAssistant.sendMessage(threadId!, content).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assistant-messages', threadId] })
      qc.invalidateQueries({ queryKey: ['assistant-threads'] })
    },
    onError: () => toast.error('Failed to send message'),
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sendMutation.isPending])

  const handleSend = () => {
    if (!threadId || !input.trim() || sendMutation.isPending) return
    sendMutation.mutate({ content: input.trim() })
    setInput('')
  }

  if (!threadId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-brand-forest-950">
        <div className="text-center max-w-md px-6">
          <Sparkles className="w-10 h-10 text-brand-teal-300 mx-auto" />
          <h2 className="mt-3 text-lg font-bold text-white">CustomerFlow AI Assistant</h2>
          <p className="mt-2 text-sm text-brand-teal-100/70">
            Ask anything about your pipeline, leads, invoices or tasks. The assistant can read your
            data and suggest next actions.
          </p>
        </div>
      </div>
    )
  }

  const list = messages ?? []

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-brand-forest-950">
      <div className="flex-1 overflow-y-auto px-4 py-4 sm:px-6">
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin w-6 h-6 border-2 border-brand-forest-700 border-t-transparent rounded-full" />
          </div>
        )}
        {!isLoading && list.length === 0 && (
          <div className="max-w-2xl mx-auto py-6">
            <p className="text-sm text-brand-teal-100/70 mb-3">Try one of these to get started:</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SUGGESTED_PROMPTS.map((p) => (
                <button
                  key={p}
                  onClick={() => {
                    setInput(p)
                  }}
                  className="text-left text-sm px-3 py-2 rounded-lg border border-brand-forest-700 bg-brand-forest-900 text-brand-teal-50 hover:border-brand-teal-300 hover:bg-brand-forest-800 transition-colors"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="max-w-3xl mx-auto">
          {list.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {sendMutation.isPending && (
            <div className="flex items-start gap-3 my-3">
              <div className="w-7 h-7 rounded-full bg-brand-teal-400/20 flex items-center justify-center">
                <Bot className="w-3.5 h-3.5 text-brand-teal-100" />
              </div>
              <div className="inline-block px-3.5 py-2.5 rounded-2xl bg-brand-forest-900 border border-brand-forest-700">
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-brand-teal-300 rounded-full animate-bounce" />
                  <span className="w-1.5 h-1.5 bg-brand-teal-300 rounded-full animate-bounce [animation-delay:120ms]" />
                  <span className="w-1.5 h-1.5 bg-brand-teal-300 rounded-full animate-bounce [animation-delay:240ms]" />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t border-brand-forest-800 bg-brand-forest-900 p-3">
        <div className="max-w-3xl mx-auto flex gap-2 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            rows={1}
            placeholder="Ask the assistant…"
            className="flex-1 resize-none px-4 py-3 border border-brand-forest-700 bg-brand-forest-950 text-white placeholder:text-brand-teal-100/50 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal-300/30 max-h-32"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sendMutation.isPending}
            className="p-3 rounded-xl bg-brand-forest-700 text-brand-forest-foreground hover:bg-brand-forest-800 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
            aria-label="Send"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default function AssistantPage() {
  const qc = useQueryClient()
  const [activeId, setActiveId] = useState<string | null>(null)

  const { data: threads } = useQuery<Thread[]>({
    queryKey: ['assistant-threads'],
    queryFn: () => aiAssistant.listThreads().then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: () => aiAssistant.createThread().then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['assistant-threads'] })
      setActiveId(data.id)
    },
    onError: () => toast.error('Failed to create thread'),
  })

  useEffect(() => {
    if (!activeId && threads && threads.length > 0) {
      setActiveId(threads[0].id)
    }
  }, [activeId, threads])

  return (
    <div className="-m-4 flex h-[calc(100dvh-4rem)] min-h-[620px] flex-col bg-brand-forest-950 sm:-m-6 lg:flex-row">
      <ThreadList
        threads={threads ?? []}
        activeId={activeId}
        onSelect={setActiveId}
        onCreate={() => createMutation.mutate()}
      />
      <ChatView threadId={activeId} />
    </div>
  )
}
