'use client'

import Link from 'next/link'
import type { LucideIcon } from 'lucide-react'

export type ModuleCardItem = {
  title: string
  description: string
  href: string
  icon: LucideIcon
  badge?: string
}

export function ModuleCardGrid({ items }: { items: ModuleCardItem[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((item) => {
        const Icon = item.icon
        return (
          <Link
            key={item.href}
            href={item.href}
            className="group rounded-2xl border border-brand-forest-800 bg-brand-forest-900/80 p-5 shadow-sm transition-all hover:border-brand-teal-400/40 hover:bg-brand-forest-900 hover:shadow-md"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="w-11 h-11 rounded-xl bg-brand-teal-400/15 flex items-center justify-center">
                <Icon className="w-5 h-5 text-brand-teal-300" />
              </div>
              {item.badge ? (
                <span className="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full bg-brand-forest-800 text-brand-teal-200">
                  {item.badge}
                </span>
              ) : null}
            </div>
            <h3 className="mt-4 text-base font-bold text-white group-hover:text-brand-teal-100">
              {item.title}
            </h3>
            <p className="mt-1.5 text-sm text-brand-teal-100/65 leading-relaxed">{item.description}</p>
          </Link>
        )
      })}
    </div>
  )
}
