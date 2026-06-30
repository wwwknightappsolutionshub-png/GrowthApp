import Link from 'next/link'
import { PRIVACY_POLICY } from '@/lib/legal/privacy-content'
import type { Metadata } from 'next'
import { canonical } from '@/lib/seo'

export const metadata: Metadata = {
  title: 'Privacy Policy | CustomerFlow AI',
  description: 'How CustomerFlow AI collects, uses, and protects your personal data (UK GDPR).',
  alternates: { canonical: canonical('/privacy') },
  robots: { index: true, follow: true },
}

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="flex items-center justify-between px-6 py-4 border-b bg-white max-w-3xl mx-auto w-full">
        <Link href="/" className="text-xl font-bold text-blue-600">
          CustomerFlow AI
        </Link>
        <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">
          Sign in
        </Link>
      </nav>

      <article className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900">{PRIVACY_POLICY.title}</h1>
        <p className="mt-2 text-sm text-gray-500">{PRIVACY_POLICY.subtitle}</p>
        <p className="mt-6 text-sm leading-relaxed text-gray-700">{PRIVACY_POLICY.intro}</p>
        <div className="mt-8 space-y-6">
          {PRIVACY_POLICY.sections.map((section) => (
            <section key={section.heading}>
              <h2 className="text-base font-semibold text-gray-900">{section.heading}</h2>
              <p className="mt-2 text-sm leading-relaxed text-gray-700">{section.body}</p>
            </section>
          ))}
        </div>
      </article>
    </div>
  )
}
