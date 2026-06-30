import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, BookOpen } from 'lucide-react'
import { BlogGrid } from '@/components/marketing/BlogGrid'
import { BreadcrumbJsonLd } from '@/components/seo/BreadcrumbJsonLd'
import { fetchBlogList } from '@/lib/blog'
import { canonical } from '@/lib/seo'

export const metadata: Metadata = {
  title: 'Blog — CustomerFlow AI | Growth Strategies for UK Businesses',
  description:
    'Expert guides, tips and case studies on AI lead generation, customer retention, Google review automation, GDPR compliance and growth strategies for UK small businesses.',
  keywords:
    'CustomerFlow AI blog, UK business growth tips, AI CRM guides, lead generation UK, customer retention strategies, Google review automation, GDPR marketing UK, trades business software',
  openGraph: {
    title: 'CustomerFlow AI Blog — Growth Strategies for UK Businesses',
    description:
      'Expert content on AI-powered lead generation, customer retention and growth for UK SMBs.',
    type: 'website',
  },
  alternates: { canonical: canonical('/blog') },
  robots: { index: true, follow: true },
}

export default async function BlogPage() {
  const { items, total } = await fetchBlogList()

  return (
    <div className="min-h-screen bg-background">
      {/* ── SEO Hero ─────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden border-b border-border bg-brand-forest-950 py-20 text-brand-forest-foreground">
        <div aria-hidden className="absolute inset-0 bg-grid-forest opacity-100" />
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,hsl(var(--brand-teal)/0.18),transparent_70%)]"
        />
        <div className="container relative">
          <Link
            href="/"
            className="mb-8 inline-flex items-center gap-1.5 text-xs font-medium text-white/50 transition-colors hover:text-white"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to home
          </Link>

          <div className="flex items-center gap-3">
            <BookOpen className="h-8 w-8 text-brand-teal-300" strokeWidth={1.5} />
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-brand-teal-300">
              CustomerFlow AI Blog
            </span>
          </div>

          <h1 className="mt-4 font-display text-4xl font-bold leading-tight text-white sm:text-5xl lg:text-[56px]">
            Growth strategies for
            <br />
            <span className="text-brand-teal-300">UK businesses</span>
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-relaxed text-white/70">
            Expert guides, case studies and how-tos on AI lead generation, customer
            retention, review automation, GDPR compliance and scaling your UK business
            with CustomerFlow AI.
          </p>

          <BreadcrumbJsonLd
            items={[
              { name: 'Home', path: '/' },
              { name: 'Blog', path: '/blog' },
            ]}
          />
        </div>
      </section>

      {/* ── Blog Grid ─────────────────────────────────────────────────── */}
      <section className="py-16 lg:py-24">
        <div className="container">
          <BlogGrid initialPosts={items} initialTotal={total} />
        </div>
      </section>

      {/* ── Bottom CTA ────────────────────────────────────────────────── */}
      <section className="border-t border-border bg-muted/40 py-16">
        <div className="container max-w-2xl text-center">
          <h2 className="font-display text-2xl font-bold text-foreground sm:text-3xl">
            Ready to put these strategies to work?
          </h2>
          <p className="mt-4 text-muted-foreground">
            Start your free 14-day trial of CustomerFlow AI — no credit card required.
          </p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-md bg-brand-forest-700 px-6 py-3 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800"
            >
              Start free trial
            </Link>
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-md border border-border px-6 py-3 text-sm font-semibold text-foreground transition-all hover:bg-muted"
            >
              See all features
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
