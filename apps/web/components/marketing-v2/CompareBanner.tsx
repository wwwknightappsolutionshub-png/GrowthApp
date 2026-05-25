'use client'

import Link from 'next/link'

export function CompareBanner() {
  return (
    <div className="fixed inset-x-0 top-0 z-[100] border-b border-amber-500/30 bg-gray-950/95 px-4 py-2 text-center text-xs text-gray-300 backdrop-blur">
      <span className="font-semibold text-amber-400">Preview V2</span>
      {' — comparison variant. '}
      <Link href="/" className="text-white underline underline-offset-2 hover:text-amber-300">
        View current homepage
      </Link>
      {' · '}
      <Link href="/preview-v2" className="text-white underline underline-offset-2 hover:text-amber-300">
        This page
      </Link>
    </div>
  )
}
