'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { messaging } from '@/lib/api-client'
import { useState } from 'react'
import { formatDateTime } from '@/lib/utils'
import { toast } from 'sonner'
import { MessageSquare, Send } from 'lucide-react'
import { useForm } from 'react-hook-form'

export default function MessagesPage() {
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null)
  const qc = useQueryClient()
  const { register, handleSubmit, reset } = useForm<{ body: string }>()

  const { data: convsData, isLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => messaging.conversations().then(r => r.data),
  })

  const { data: convDetail } = useQuery({
    queryKey: ['conversation', selectedConvId],
    queryFn: () => messaging.getConversation(selectedConvId!).then(r => r.data),
    enabled: !!selectedConvId,
  })

  const sendMutation = useMutation({
    mutationFn: (body: string) => {
      if (!convDetail) throw new Error('No conversation selected')
      return messaging.send({
        channel: convDetail.channel,
        to_address: convDetail.customer_phone || convDetail.customer_email || '',
        body,
        deal_id: convDetail.deal_id,
        customer_id: convDetail.customer_id,
      })
    },
    onSuccess: () => {
      toast.success('Message sent')
      reset()
      qc.invalidateQueries({ queryKey: ['conversation', selectedConvId] })
      qc.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: () => toast.error('Failed to send message'),
  })

  const onSend = ({ body }: { body: string }) => {
    if (!body.trim()) return
    sendMutation.mutate(body.trim())
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Messages</h1>
        <p className="text-muted-foreground text-sm">Unified inbox — SMS and email conversations</p>
      </div>

      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 overflow-hidden flex h-[calc(100vh-220px)] shadow-sm">
        {/* Conversation list */}
        <div className="w-80 border-r border-brand-forest-800 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-brand-forest-800 bg-brand-forest-900">
            <p className="text-sm font-medium text-white">Conversations</p>
          </div>
          <div className="flex-1 overflow-y-auto">
            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin w-6 h-6 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
              </div>
            )}
            {convsData?.items?.length === 0 && (
              <div className="p-6 text-center text-brand-teal-100/60 text-sm">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-30" />
                No conversations yet
              </div>
            )}
            {convsData?.items?.map((conv: any) => (
              <button
                key={conv.id}
                onClick={() => setSelectedConvId(conv.id)}
                className={`w-full text-left p-4 border-b border-brand-forest-800 transition-colors ${
                  selectedConvId === conv.id
                    ? 'bg-brand-forest-800 border-l-2 border-l-brand-teal-300'
                    : 'hover:bg-brand-forest-900'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-medium text-white truncate">
                    {conv.customer_phone || conv.customer_email || 'Unknown'}
                  </p>
                  <span className={`text-xs px-1.5 py-0.5 rounded uppercase font-medium ${conv.channel === 'sms' ? 'bg-brand-teal-400/20 text-brand-teal-100' : 'bg-brand-forest-700 text-brand-forest-foreground'}`}>
                    {conv.channel}
                  </span>
                </div>
                {conv.last_message_at && (
                  <p className="text-xs text-brand-teal-100/60">{formatDateTime(conv.last_message_at)}</p>
                )}
                {conv.is_resolved && <span className="text-xs text-brand-teal-100/60">Resolved</span>}
              </button>
            ))}
          </div>
        </div>

        {/* Message thread */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {!selectedConvId ? (
            <div className="flex-1 flex items-center justify-center text-brand-teal-100/60">
              <div className="text-center">
                <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p>Select a conversation to view messages</p>
              </div>
            </div>
          ) : (
            <>
              <div className="p-4 border-b border-brand-forest-800 bg-brand-forest-900">
                <p className="font-medium text-sm text-white">
                  {convDetail?.customer_phone || convDetail?.customer_email || 'Conversation'}
                </p>
                <p className="text-xs text-brand-teal-100/60 capitalize">{convDetail?.channel} conversation</p>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {convDetail?.messages?.length === 0 && (
                  <p className="text-center text-brand-teal-100/60 text-sm py-8">No messages yet</p>
                )}
                {convDetail?.messages?.map((msg: any) => (
                  <div key={msg.id} className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs lg:max-w-md px-4 py-2.5 rounded-2xl text-sm ${msg.direction === 'outbound' ? 'bg-brand-forest-700 text-brand-forest-foreground rounded-br-none' : 'bg-brand-forest-800 text-brand-teal-50 rounded-bl-none'}`}>
                      <p>{msg.body}</p>
                      <p className={`text-xs mt-1 ${msg.direction === 'outbound' ? 'text-brand-teal-100/75' : 'text-brand-teal-100/60'}`}>
                        {formatDateTime(msg.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-4 border-t border-brand-forest-800 bg-brand-forest-900">
                <form onSubmit={handleSubmit(onSend)} className="flex gap-3">
                  <input
                    {...register('body')}
                    placeholder="Type a message..."
                    className="flex-1 rounded-lg border border-brand-forest-700 bg-brand-forest-950 px-3 py-2 text-sm text-white placeholder:text-brand-teal-100/50 focus:outline-none focus:ring-2 focus:ring-brand-teal-300/30"
                  />
                  <button
                    type="submit"
                    disabled={sendMutation.isPending}
                    className="bg-brand-forest-700 text-brand-forest-foreground px-4 py-2 rounded-lg hover:bg-brand-forest-800 disabled:opacity-50 flex items-center gap-1.5 text-sm font-medium"
                  >
                    <Send className="w-4 h-4" />
                    Send
                  </button>
                </form>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
