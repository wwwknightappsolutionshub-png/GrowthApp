import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, BookOpen } from 'lucide-react'
import { BlogGrid, type BlogPostItem } from '@/components/marketing/BlogGrid'

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
  alternates: { canonical: 'https://customerflow.ai/blog' },
  robots: { index: true, follow: true },
}

const FALLBACK_POSTS: BlogPostItem[] = [
  {
    id: '1',
    title: 'How UK Tradesmen Are Winning More Jobs with AI-Powered Follow-Ups',
    slug: 'ai-follow-ups-uk-tradesmen',
    excerpt:
      'Discover how plumbers, electricians and builders across the UK are using CustomerFlow AI to automate follow-ups and convert 40% more enquiries into booked jobs.',
    content: null,
    category: 'Trades',
    image_url:
      'https://images.pexels.com/photos/1216589/pexels-photo-1216589.jpeg?auto=compress&cs=tinysrgb&w=800&q=80',
    author_name: 'CustomerFlow Team',
    read_minutes: 6,
    published_at: '2026-05-01T09:00:00Z',
  },
  {
    id: '2',
    title: '5 Signs Your UK Small Business Needs a Customer Retention Strategy',
    slug: 'customer-retention-strategy-uk-small-business',
    excerpt:
      'If you are spending more on acquiring new customers than keeping existing ones, you are leaving serious money on the table.',
    content: null,
    category: 'Strategy',
    image_url:
      'https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg?auto=compress&cs=tinysrgb&w=800&q=80',
    author_name: 'CustomerFlow Team',
    read_minutes: 5,
    published_at: '2026-04-28T09:00:00Z',
  },
  {
    id: '3',
    title: 'The Complete Guide to Google Review Automation for UK Businesses',
    slug: 'google-review-automation-uk-businesses',
    excerpt:
      'More Google reviews mean higher rankings, more trust and more bookings. This guide shows exactly how UK businesses automate review collection without lifting a finger.',
    content: null,
    category: 'Reviews',
    image_url:
      'https://images.pexels.com/photos/6476255/pexels-photo-6476255.jpeg?auto=compress&cs=tinysrgb&w=800&q=80',
    author_name: 'CustomerFlow Team',
    read_minutes: 7,
    published_at: '2026-04-22T09:00:00Z',
  },
  {
    id: '4',
    title: 'How to Reduce No-Shows by 80% with Automated Booking Reminders',
    slug: 'reduce-no-shows-automated-booking-reminders',
    excerpt:
      'No-shows cost UK service businesses thousands of pounds every year. CustomerFlow AI brings no-show rates below 5% without any manual effort.',
    content: null,
    category: 'Bookings',
    image_url:
      'https://images.pexels.com/photos/1181406/pexels-photo-1181406.jpeg?auto=compress&cs=tinysrgb&w=800&q=80',
    author_name: 'CustomerFlow Team',
    read_minutes: 4,
    published_at: '2026-04-15T09:00:00Z',
  },
  {
    id: '5',
    title: 'AI Lead Scoring: Stop Chasing Cold Leads and Close More Business',
    slug: 'ai-lead-scoring-uk-business-close-more',
    excerpt:
      'Not all leads are equal. CustomerFlow AI scores every inbound lead in real time so your team spends time on prospects most likely to convert.',
    content: null,
    category: 'Lead Generation',
    image_url:
      'https://images.pexels.com/photos/7376/startup-photos.jpg?auto=compress&cs=tinysrgb&w=800&q=80',
    author_name: 'CustomerFlow Team',
    read_minutes: 6,
    published_at: '2026-04-10T09:00:00Z',
  },
  {
    id: '6',
    title: 'Why UK Restaurants Are Switching to Automated Customer Win-Back Campaigns',
    slug: 'automated-win-back-campaigns-uk-restaurants',
    excerpt:
      'A customer who visited 6 months ago and never returned is not lost — they just need the right message at the right time.',
    content: null,
    category: 'Hospitality',
    image_url:
      'https://images.pexels.com/photos/262978/pexels-photo-262978.jpeg?auto=compress&cs=tinysrgb&w=800&q=80',
    author_name: 'CustomerFlow Team',
    read_minutes: 5,
    published_at: '2026-04-05T09:00:00Z',
  },
  {
    id: '7',
    title: 'The ROI of Missed-Call SMS Recovery for UK Trades Businesses',
    slug: 'missed-call-sms-recovery-roi-uk-trades',
    excerpt:
      'Every missed call is a missed job. CustomerFlow AI\'s 60-second SMS recovery feature recaptures prospects before they dial your competitor.',
    content: null,
    category: 'Trades',
    image_url:
      'https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?auto=compress&cs=tinysrgb&w=800&q=80',
    author_name: 'CustomerFlow Team',
    read_minutes: 4,
    published_at: '2026-03-28T09:00:00Z',
  },
  {
    id: '8',
    title: 'GDPR-Compliant Customer Marketing: What Every UK Business Must Know in 2026',
    slug: 'gdpr-compliant-customer-marketing-uk-2026',
    excerpt:
      'GDPR fines reached £1.1bn in 2025. CustomerFlow AI is built from the ground up for UK and EU compliance.',
    content: null,
    category: 'Compliance',
    image_url:
      'https://images.pexels.com/photos/5668859/pexels-photo-5668859.jpeg?auto=compress&cs=tinysrgb&w=800&q=80',
    author_name: 'CustomerFlow Team',
    read_minutes: 8,
    published_at: '2026-03-20T09:00:00Z',
  },
]

async function loadPosts(): Promise<{ items: BlogPostItem[]; total: number }> {
  const base = process.env.INTERNAL_API_URL
  if (!base) return { items: FALLBACK_POSTS, total: FALLBACK_POSTS.length }
  try {
    const res = await fetch(`${base}/api/v1/public/blog?page=1&per_page=8`, {
      next: { revalidate: 120 },
    })
    if (!res.ok) return { items: FALLBACK_POSTS, total: FALLBACK_POSTS.length }
    const data = await res.json()
    const items = Array.isArray(data.items) && data.items.length > 0 ? data.items : FALLBACK_POSTS
    return { items, total: data.total || items.length }
  } catch {
    return { items: FALLBACK_POSTS, total: FALLBACK_POSTS.length }
  }
}

export default async function BlogPage() {
  const { items, total } = await loadPosts()

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

          {/* Schema.org BreadcrumbList for SEO */}
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{
              __html: JSON.stringify({
                '@context': 'https://schema.org',
                '@type': 'BreadcrumbList',
                itemListElement: [
                  { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://customerflow.ai' },
                  { '@type': 'ListItem', position: 2, name: 'Blog', item: 'https://customerflow.ai/blog' },
                ],
              }),
            }}
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
