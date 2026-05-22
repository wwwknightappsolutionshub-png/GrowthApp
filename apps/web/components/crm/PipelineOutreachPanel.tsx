'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Mail, MessageCircle, Send } from 'lucide-react'
import { toast } from 'sonner'
import { messaging } from '@/lib/api-client'

const REMARKETING_TEMPLATE =
  'Hi — we wanted to reach out with a special offer for returning customers. Reply if you would like to book your next visit.'

const UPSELL_TEMPLATE =
  'Hi — based on your history with us, we have a complementary service that could add real value. Would you like details and a quick quote?'

type BoardCard = {
  card_type: 'lead' | 'deal'
  id: string
  title: string
  email?: string | null
  phone?: string | null
}

export function PipelineOutreachPanel({ card }: { card: BoardCard }) {
  const [channel, setChannel] = useState<'email' | 'whatsapp'>('email')
  const [template, setTemplate] = useState<'remarketing' | 'upsell'>('remarketing')
  const [body, setBody] = useState(REMARKETING_TEMPLATE)

  const toAddress = channel === 'email' ? (card.email?.trim() || '') : (card.phone?.trim() || '')

  const sendMut = useMutation({
    mutationFn: () =>
      messaging.send({
        channel: channel === 'whatsapp' ? 'whatsapp' : 'email',
        to_address: toAddress,
        subject: template === 'upsell' ? 'A service we think you will love' : 'We would love to see you again',
        body,
        ...(card.card_type === 'deal' ? { deal_id: card.id } : {}),
      }),
    onSuccess: () => toast.success('Message queued'),
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      const detail = err.response?.data?.detail
      toast.error(typeof detail === 'string' ? detail : 'Failed to send')
    },
  })

  const applyTemplate = (kind: 'remarketing' | 'upsell') => {
    setTemplate(kind)
    setBody(kind === 'upsell' ? UPSELL_TEMPLATE : REMARKETING_TEMPLATE)
  }

  return (
    <div className="rounded-xl border border-brand-forest-700 bg-brand-forest-900/80 p-4 space-y-3">
      <h3 className="text-sm font-bold text-white flex items-center gap-2">
        <Send className="w-4 h-4 text-brand-teal-300" />
        Pipeline outreach
      </h3>
      <p className="text-xs text-brand-teal-100/65">
        Send remarketing or upsell messages from this deal — without leaving the board.
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => applyTemplate('remarketing')}
          className={`text-xs px-2.5 py-1.5 rounded-lg border ${
            template === 'remarketing'
              ? 'border-brand-teal-300 bg-brand-forest-800 text-white'
              : 'border-brand-forest-700 text-brand-teal-100/70'
          }`}
        >
          Remarketing
        </button>
        <button
          type="button"
          onClick={() => applyTemplate('upsell')}
          className={`text-xs px-2.5 py-1.5 rounded-lg border ${
            template === 'upsell'
              ? 'border-brand-teal-300 bg-brand-forest-800 text-white'
              : 'border-brand-forest-700 text-brand-teal-100/70'
          }`}
        >
          Upsell
        </button>
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setChannel('email')}
          className={`flex-1 inline-flex items-center justify-center gap-1.5 text-xs py-2 rounded-lg border ${
            channel === 'email' ? 'border-brand-teal-300 text-white' : 'border-brand-forest-700 text-brand-teal-100/70'
          }`}
        >
          <Mail className="w-3.5 h-3.5" />
          Email
        </button>
        <button
          type="button"
          onClick={() => setChannel('whatsapp')}
          className={`flex-1 inline-flex items-center justify-center gap-1.5 text-xs py-2 rounded-lg border ${
            channel === 'whatsapp'
              ? 'border-brand-teal-300 text-white'
              : 'border-brand-forest-700 text-brand-teal-100/70'
          }`}
        >
          <MessageCircle className="w-3.5 h-3.5" />
          WhatsApp
        </button>
      </div>
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        rows={4}
        className="w-full rounded-lg border border-brand-forest-700 bg-brand-forest-950 px-3 py-2 text-sm text-white"
      />
      <button
        type="button"
        disabled={!toAddress || !body.trim() || sendMut.isPending}
        onClick={() => sendMut.mutate()}
        className="w-full py-2 rounded-lg bg-brand-forest-700 text-sm font-semibold text-white disabled:opacity-50"
      >
        {sendMut.isPending ? 'Sending…' : `Send ${channel === 'whatsapp' ? 'WhatsApp' : 'email'}`}
      </button>
      {!toAddress && (
        <p className="text-xs text-amber-400/90">
          Add a {channel === 'email' ? 'email' : 'phone number'} on this {card.card_type} to send.
        </p>
      )}
    </div>
  )
}
