'use client'

/**
 * SupportChatWidget
 * Floating bottom-right AI chat widget for the marketing site.
 * - Answers questions about CustomerFlow AI using a smart rule-based engine
 * - "Warm hands-off" to WhatsApp for qualified leads / complex queries
 * - The optional /api/v1/public/chat endpoint can power full LLM responses
 */

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageCircle,
  X,
  Send,
  ChevronDown,
  Phone,
  ExternalLink,
  Bot,
  User,
  Sparkles,
} from 'lucide-react'

const WA_NUMBER = '447756183484'
const WA_BASE = `https://wa.me/${WA_NUMBER}?text=`

// ─── Knowledge base (rule-based AI) ──────────────────────────────────────────

interface KbEntry {
  patterns: RegExp[]
  reply: string
  ctaLabel?: string
  ctaHref?: string
  quickReplies?: string[]
}

const KB: KbEntry[] = [
  {
    patterns: [/price|cost|how much|pricing|plan|subscription|monthly|£/i],
    reply:
      'CustomerFlow AI starts at **£99/month** for the Starter plan. Most growing tradespeople choose **Growth at £149/month** — it includes 10 AI-sourced leads, unlimited automations, and the full CRM suite.\n\n• Starter £99 — Core CRM, 3 leads/mo\n• Growth £149 — Everything, 10 leads/mo ⭐\n• Pro £199 — Unlimited seats, 25 leads/mo\n\nAll plans include a 14-day free trial with no credit card required.',
    ctaLabel: 'Start free trial →',
    ctaHref: '/register',
    quickReplies: ["What's included in Growth?", 'Is there a free trial?', 'Can I cancel anytime?'],
  },
  {
    patterns: [/free trial|try|demo|sign up|register|get started/i],
    reply:
      'Yes! You get a full **14-day free trial** — no credit card needed. You\'ll have access to every feature on the Growth plan so you can see real results before committing.\n\nMost customers capture their first new lead within 24 hours of setup.',
    ctaLabel: 'Start your free trial →',
    ctaHref: '/register',
    quickReplies: ['How long is the trial?', 'What features are included?', 'Talk to a human →'],
  },
  {
    patterns: [/cancel|contract|commitment|lock.?in|tie/i],
    reply:
      'No contracts, no lock-ins. You can **cancel anytime** from your dashboard with a single click.\n\nWe also offer a **14-day money-back guarantee** if you\'re not satisfied — just ask us.',
    quickReplies: ['How do I cancel?', 'Start free trial →', 'Talk to a human →'],
  },
  {
    patterns: [/lead|prospect|scrape|source|ai lead|find customer/i],
    reply:
      'Our **AI Lead Engine** scans public sources and directories daily to find businesses that match your ideal customer profile. Leads are scored 0–100 and delivered straight to your CRM.\n\nPlan allocations:\n• Starter: 3 AI leads/month\n• Growth: 10 AI leads/month ⭐\n• Pro: 25 AI leads/month',
    quickReplies: ["How accurate are the leads?", 'Can I request more leads?', "What's the AI score?"],
  },
  {
    patterns: [/review|google|reputation|star|rating/i],
    reply:
      'CustomerFlow AI **automates your Google review collection** — after every job, customers receive a personalised text or email asking for a review, with a one-tap link to your Google Business profile.\n\nOur customers average **4× more reviews** within 60 days compared to asking manually. More reviews = more inbound calls.',
    quickReplies: ['How does it send reviews?', 'Does it work with Trustpilot?', 'See pricing →'],
  },
  {
    patterns: [/miss|call|sms|text|reply|follow.?up|automation/i],
    reply:
      'Our **Missed-Call SMS Recovery** sends an automated text within **60 seconds** when a customer calls and you\'re busy.\n\nThe message: *"Sorry I missed your call — I\'ll be in touch within the hour."* Simple, personal, effective.\n\nCustomers who implement this alone recover an average of **£2,400/month** in lost job enquiries.',
    quickReplies: ['How does automation work?', 'What else can I automate?', 'Start free trial →'],
  },
  {
    patterns: [/whatsapp|message|chat|wa/i],
    reply:
      'Great choice! Our team is available on **WhatsApp** — click below to start a live chat. We typically respond within 2 hours and can walk you through the platform or set up your trial.',
    ctaLabel: 'Chat on WhatsApp →',
    ctaHref: WA_BASE + encodeURIComponent('Hi! I\'d like to learn more about CustomerFlow AI.'),
    quickReplies: ['Tell me more about pricing', 'Start free trial →'],
  },
  {
    patterns: [/crm|customer|contact|manage|database/i],
    reply:
      'CustomerFlow AI includes a full **CRM system** built for UK tradespeople — track every customer, job, follow-up, quote, invoice, and booking in one place.\n\nKey CRM features:\n• Visit history & next visit date\n• "Requires follow-up" reminders\n• Special notes per customer\n• Integrated quotes & invoices\n• Automatic review requests after jobs',
    quickReplies: ['Can I import my existing contacts?', 'Does it integrate with Xero?', 'See pricing →'],
  },
  {
    patterns: [/invoice|quote|payment|stripe|deposit/i],
    reply:
      'Yes — CustomerFlow AI includes a full **Quote & Invoice** builder.\n\n• Send branded quotes in seconds\n• Customers approve online\n• Invoices with **Stripe payments** built in\n• Automated payment reminders\n• Deposit collection before the job starts',
    quickReplies: ['What payment methods are supported?', 'Is there a transaction fee?', 'Start free trial →'],
  },
  {
    patterns: [/booking|schedule|calendar|appointment/i],
    reply:
      'Our **Booking Engine** lets customers book appointments directly from your website or via SMS link — synced with your calendar in real time.\n\nAutomatic reminders are sent to both you and the customer 24 hours before the appointment.',
    quickReplies: ['Does it sync with Google Calendar?', 'Can customers self-book?', 'See pricing →'],
  },
  {
    patterns: [/tradesman|plumber|electrician|builder|roofer|painter|carpenter|hvac|industry|sector|type/i],
    reply:
      'CustomerFlow AI is built specifically for **UK tradespeople and service businesses** — plumbers, electricians, builders, roofers, painters, HVAC engineers, landscapers, and more.\n\nThe platform automatically adapts its tools and lead sources based on your trade.',
    quickReplies: ['Does it work for my trade?', 'Tell me about AI leads', 'Start free trial →'],
  },
  {
    patterns: [/help|support|question|human|person|talk|speak|agent/i],
    reply:
      'Happy to connect you with a real human! Our team is available on **WhatsApp** — we\'ll usually reply within 2 hours during business hours (Mon–Fri 8am–7pm UK).',
    ctaLabel: 'Chat with us on WhatsApp →',
    ctaHref: WA_BASE + encodeURIComponent("Hi, I have a question about CustomerFlow AI."),
  },
]

const FALLBACK: KbEntry = {
  patterns: [],
  reply:
    "Great question! I don't have a specific answer for that, but one of our team members would love to help.\n\nClick below to start a WhatsApp chat — we reply within 2 hours.",
  ctaLabel: 'Chat on WhatsApp →',
  ctaHref: WA_BASE + encodeURIComponent("Hi, I have a question about CustomerFlow AI."),
  quickReplies: ['Pricing →', 'Free trial →', 'How it works →'],
}

function matchKb(text: string): KbEntry {
  for (const entry of KB) {
    if (entry.patterns.some((p) => p.test(text))) return entry
  }
  return FALLBACK
}

// ─── Message types ────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string
  role: 'user' | 'bot'
  text: string
  ctaLabel?: string
  ctaHref?: string
  quickReplies?: string[]
}

function uid() {
  return Math.random().toString(36).slice(2)
}

// ─── Markdown-lite renderer (bold + newlines only) ────────────────────────────

function MdText({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*|\n)/g)
  return (
    <span>
      {parts.map((p, i) => {
        if (p.startsWith('**') && p.endsWith('**'))
          return <strong key={i}>{p.slice(2, -2)}</strong>
        if (p === '\n') return <br key={i} />
        return <span key={i}>{p}</span>
      })}
    </span>
  )
}

// ─── Component ────────────────────────────────────────────────────────────────

const INTRO: ChatMessage = {
  id: 'intro',
  role: 'bot',
  text: "Hi! 👋 I'm the CustomerFlow AI assistant. I can answer questions about the platform, pricing, and how it helps UK tradespeople grow.\n\nWhat would you like to know?",
  quickReplies: ['Pricing & plans', 'How does it work?', 'Free trial', 'AI-sourced leads', 'Talk to a human →'],
}

export function SupportChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([INTRO])
  const [input, setInput] = useState('')
  const [typing, setTyping] = useState(false)
  const [unread, setUnread] = useState(0)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom on new message
  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
      setUnread(0)
    }
  }, [messages, open])

  function handleOpen() {
    setOpen(true)
    setUnread(0)
  }

  function sendMessage(text: string) {
    if (!text.trim()) return
    const userMsg: ChatMessage = { id: uid(), role: 'user', text: text.trim() }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setTyping(true)

    // Simulate brief typing delay
    const delay = 600 + Math.random() * 700
    setTimeout(() => {
      const matched = matchKb(text)
      const botMsg: ChatMessage = {
        id: uid(),
        role: 'bot',
        text: matched.reply,
        ctaLabel: matched.ctaLabel,
        ctaHref: matched.ctaHref,
        quickReplies: matched.quickReplies,
      }
      setMessages((prev) => [...prev, botMsg])
      setTyping(false)
      if (!open) setUnread((n) => n + 1)
    }, delay)
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    sendMessage(input)
  }

  return (
    <>
      {/* Floating button */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
        <AnimatePresence>
          {!open && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: 10 }}
              className="rounded-2xl border border-white/10 bg-[#025422] px-4 py-2 text-sm font-medium text-white shadow-xl"
            >
              Ask me anything about CustomerFlow AI
            </motion.div>
          )}
        </AnimatePresence>

        <button
          onClick={() => (open ? setOpen(false) : handleOpen())}
          className="relative flex h-14 w-14 items-center justify-center rounded-full bg-[#025422] shadow-xl ring-2 ring-white/10 transition-transform hover:scale-105 active:scale-95"
          aria-label="Open support chat"
        >
          {open ? (
            <ChevronDown className="h-6 w-6 text-white" />
          ) : (
            <MessageCircle className="h-6 w-6 text-white" />
          )}
          {!open && unread > 0 && (
            <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
              {unread}
            </span>
          )}
        </button>
      </div>

      {/* Chat panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            key="chat-panel"
            initial={{ opacity: 0, y: 24, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
            className="fixed bottom-24 right-6 z-50 flex w-[360px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#0c1f12] shadow-2xl"
            style={{ maxHeight: '75vh' }}
          >
            {/* Header */}
            <div className="flex items-center gap-3 bg-[#025422] px-4 py-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-white">CustomerFlow AI</p>
                <p className="text-[11px] text-white/60">Sales &amp; Support · Usually replies in 2h</p>
              </div>
              <a
                href={WA_BASE + encodeURIComponent("Hi! I'd like to chat about CustomerFlow AI.")}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 rounded-full bg-[#25D366]/20 px-2.5 py-1 text-[11px] font-semibold text-[#25D366] hover:bg-[#25D366]/30"
              >
                WhatsApp
                <ExternalLink className="h-3 w-3" />
              </a>
              <button onClick={() => setOpen(false)} className="ml-1 rounded-md p-1 text-white/50 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4" style={{ minHeight: 0 }}>
              {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  {/* Avatar */}
                  <div className={`mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs ${msg.role === 'bot' ? 'bg-[#025422] text-white' : 'bg-amber-500 text-black'}`}>
                    {msg.role === 'bot' ? <Bot className="h-3.5 w-3.5" /> : <User className="h-3.5 w-3.5" />}
                  </div>
                  <div className="flex max-w-[80%] flex-col gap-2">
                    <div
                      className={`rounded-2xl px-3 py-2 text-sm leading-relaxed ${
                        msg.role === 'bot'
                          ? 'rounded-tl-none bg-[#1a3322] text-gray-200'
                          : 'rounded-tr-none bg-amber-500 text-black'
                      }`}
                    >
                      <MdText text={msg.text} />
                    </div>

                    {/* CTA button */}
                    {msg.ctaLabel && msg.ctaHref && (
                      <a
                        href={msg.ctaHref}
                        target={msg.ctaHref.startsWith('http') ? '_blank' : undefined}
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 self-start rounded-full bg-[#025422] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#036b2b]"
                      >
                        {msg.ctaLabel}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}

                    {/* Quick replies */}
                    {msg.quickReplies && msg.quickReplies.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {msg.quickReplies.map((qr) => (
                          <button
                            key={qr}
                            onClick={() => sendMessage(qr)}
                            className="rounded-full border border-[#025422]/50 bg-[#025422]/10 px-2.5 py-1 text-[11px] font-medium text-[#20ccce] hover:border-[#20ccce]/40 hover:bg-[#20ccce]/10"
                          >
                            {qr}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Typing indicator */}
              {typing && (
                <div className="flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#025422]">
                    <Bot className="h-3.5 w-3.5 text-white" />
                  </div>
                  <div className="flex gap-1 rounded-2xl rounded-tl-none bg-[#1a3322] px-3 py-3">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <form
              onSubmit={onSubmit}
              className="flex items-center gap-2 border-t border-white/5 bg-[#0c1f12] px-3 py-3"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about pricing, features, trial…"
                className="flex-1 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-gray-200 placeholder:text-gray-600 focus:border-[#025422] focus:outline-none"
              />
              <button
                type="submit"
                disabled={!input.trim()}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-[#025422] text-white disabled:opacity-30 hover:bg-[#036b2b]"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>

            {/* Footer note */}
            <p className="bg-[#0c1f12] pb-3 text-center text-[10px] text-gray-600">
              Powered by CustomerFlow AI · For urgent queries WhatsApp{' '}
              <a href={`tel:+${WA_NUMBER}`} className="text-gray-500 underline">
                +44 7756 183 484
              </a>
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
