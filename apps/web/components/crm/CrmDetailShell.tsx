'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

export function CrmDetailShell({
  title,
  subtitle,
  backHref = '/dashboard/crm',
  children,
}: {
  title: string
  subtitle?: string
  backHref?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-brand-forest-800 bg-gradient-to-br from-brand-forest-950 via-brand-forest-900 to-brand-forest-950 p-5">
        <Link
          href={backHref}
          className="inline-flex items-center gap-1.5 text-sm text-brand-teal-300 hover:text-brand-teal-200 mb-3"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to CRM hub
        </Link>
        <h1 className="text-2xl font-bold text-white">{title}</h1>
        {subtitle ? <p className="text-sm text-brand-teal-100/70 mt-1">{subtitle}</p> : null}
      </div>
      {children}
    </div>
  )
}
