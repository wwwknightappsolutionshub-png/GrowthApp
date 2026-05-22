'use client'

import { useState } from 'react'
import Link from 'next/link'
import { BookOpen, ChevronDown, ChevronUp, Sparkles, VolumeX } from 'lucide-react'

const SILENT_KEY = 'cf_crm_educator_silent'

const TIPS = [
  {
    title: 'Pipeline board',
    body: 'Drag deals between stages to reflect real progress. Won/lost stages trigger automations when configured.',
  },
  {
    title: 'Customers',
    body: 'Store visit dates, follow-ups, and business clients. Link every deal to a customer for accurate LTV.',
  },
  {
    title: 'Segments',
    body: 'Group contacts by rules (value, last activity, service type) for targeted outreach.',
  },
  {
    title: 'Import',
    body: 'Bulk-load spreadsheets to migrate from spreadsheets without losing history.',
  },
]

export function CrmEducatorPanel() {
  const [open, setOpen] = useState(true)
  const [silent, setSilent] = useState(() => {
    if (typeof window === 'undefined') return false
    return localStorage.getItem(SILENT_KEY) === '1'
  })

  if (silent) return null

  return (
    <section className="rounded-2xl border border-brand-teal-400/25 bg-brand-forest-900/90 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between gap-3 px-5 py-4 text-left hover:bg-brand-forest-900"
      >
        <span className="flex items-center gap-2 text-sm font-bold text-white">
          <BookOpen className="w-4 h-4 text-brand-teal-300" />
          CRM guide — get more from every tool
        </span>
        {open ? <ChevronUp className="w-4 h-4 text-brand-teal-100/60" /> : <ChevronDown className="w-4 h-4" />}
      </button>
      {open ? (
        <div className="px-5 pb-5 border-t border-brand-forest-800">
          <p className="text-sm text-brand-teal-100/75 mt-3 leading-relaxed">
            CustomerFlow CRM connects leads, bookings, and accounts. Use the tiles below to work each area;
            this panel explains how to maximise productivity.
          </p>
          <ul className="mt-4 grid sm:grid-cols-2 gap-3">
            {TIPS.map((t) => (
              <li
                key={t.title}
                className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-3 text-sm"
              >
                <p className="font-semibold text-white">{t.title}</p>
                <p className="text-brand-teal-100/65 mt-1 text-xs leading-relaxed">{t.body}</p>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              href="/dashboard/assistant?focus=crm"
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand-forest-700 px-3 py-2 text-xs font-semibold text-white hover:bg-brand-forest-800"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Ask CRM coach (AI)
            </Link>
            <button
              type="button"
              onClick={() => {
                localStorage.setItem(SILENT_KEY, '1')
                setSilent(true)
              }}
              className="inline-flex items-center gap-1.5 rounded-lg border border-brand-forest-700 px-3 py-2 text-xs text-brand-teal-100/70 hover:bg-brand-forest-950"
            >
              <VolumeX className="w-3.5 h-3.5" />
              Keep silent
            </button>
          </div>
        </div>
      ) : null}
    </section>
  )
}
