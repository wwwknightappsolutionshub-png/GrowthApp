export interface BlogPost {
  id: string
  title: string
  slug: string
  excerpt: string | null
  content: string | null
  category: string | null
  image_url: string | null
  author_name: string | null
  read_minutes: number | null
  published_at: string | null
  updated_at?: string | null
  seo_title?: string | null
  seo_description?: string | null
}

export const FALLBACK_BLOG_POSTS: BlogPost[] = [
  {
    id: '1',
    title: 'How UK Tradesmen Are Winning More Jobs with AI-Powered Follow-Ups',
    slug: 'ai-follow-ups-uk-tradesmen',
    excerpt:
      'Discover how plumbers, electricians and builders across the UK are using CustomerFlow AI to automate follow-ups and convert 40% more enquiries into booked jobs.',
    content:
      '<p>UK trades businesses lose jobs every day because follow-ups are slow, inconsistent or forgotten entirely. CustomerFlow AI automates a five-touch sequence so every enquiry gets a professional response within minutes — not hours.</p><p>Plumbers and electricians using automated SMS and email follow-ups report significantly higher quote acceptance because prospects hear back while they are still comparing options.</p>',
    category: 'Trades',
    image_url:
      'https://images.pexels.com/photos/1216589/pexels-photo-1216589.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80',
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
    content:
      '<p>Retention is cheaper than acquisition — yet most UK SMBs focus almost all their energy on winning new leads. If repeat revenue is flat, reviews are inconsistent, or customers drift to competitors, you need a retention system.</p><p>CustomerFlow AI unifies reviews, win-back journeys and loyalty in one loop so existing customers become your best growth channel.</p>',
    category: 'Strategy',
    image_url:
      'https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80',
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
    content:
      '<p>Google reviews directly influence local search rankings and conversion rates. The challenge is asking consistently and routing unhappy feedback privately.</p><p>CustomerFlow AI sends review requests when jobs complete, routes 4–5 star customers to Google, and captures constructive feedback privately for 3 stars and below.</p>',
    category: 'Reviews',
    image_url:
      'https://images.pexels.com/photos/6476255/pexels-photo-6476255.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80',
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
    content:
      '<p>Automated SMS and email reminders sent 24 hours and 2 hours before appointments dramatically cut no-shows. Deposit collection at booking adds another layer of commitment.</p><p>Salons, clinics and trades businesses using reminder sequences recover hours of lost diary time every week.</p>',
    category: 'Bookings',
    image_url:
      'https://images.pexels.com/photos/1181406/pexels-photo-1181406.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80',
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
    content:
      '<p>Hybrid AI lead scoring combines engagement signals, source quality and response behaviour to prioritise your pipeline automatically.</p><p>Teams stop wasting time on cold enquiries and focus on prospects ready to book.</p>',
    category: 'Lead Generation',
    image_url:
      'https://images.pexels.com/photos/7376/startup-photos.jpg?auto=compress&cs=tinysrgb&w=1200&q=80',
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
    content:
      '<p>Win-back campaigns re-engage lapsed diners with personalised offers and reminders. GDPR-compliant automation ensures you only message customers who opted in.</p><p>Restaurants using timed win-back journeys see measurable return visits without discounting everyone.</p>',
    category: 'Hospitality',
    image_url:
      'https://images.pexels.com/photos/262978/pexels-photo-262978.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80',
    author_name: 'CustomerFlow Team',
    read_minutes: 5,
    published_at: '2026-04-05T09:00:00Z',
  },
  {
    id: '7',
    title: 'The ROI of Missed-Call SMS Recovery for UK Trades Businesses',
    slug: 'missed-call-sms-recovery-roi-uk-trades',
    excerpt:
      "Every missed call is a missed job. CustomerFlow AI's 60-second SMS recovery feature recaptures prospects before they dial your competitor.",
    content:
      '<p>When you miss a call, prospects rarely leave voicemail — they call the next tradesperson on Google. Instant SMS recovery keeps you in the conversation.</p><p>Trades businesses report recapturing enquiries that would otherwise be lost entirely.</p>',
    category: 'Trades',
    image_url:
      'https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80',
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
    content:
      '<p>Lawful basis, consent capture, retention policies and right-to-erasure workflows are non-negotiable for UK customer marketing in 2026.</p><p>CustomerFlow AI hosts data in the UK, logs processing activity, and automates erasure requests so you stay compliant while growing.</p>',
    category: 'Compliance',
    image_url:
      'https://images.pexels.com/photos/5668859/pexels-photo-5668859.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80',
    author_name: 'CustomerFlow Team',
    read_minutes: 8,
    published_at: '2026-03-20T09:00:00Z',
  },
]

function apiBase(): string | null {
  return process.env.INTERNAL_API_URL ?? null
}

export async function fetchBlogPost(slug: string): Promise<BlogPost | null> {
  const base = apiBase()
  if (base) {
    try {
      const res = await fetch(`${base}/api/v1/public/blog/${encodeURIComponent(slug)}`, {
        next: { revalidate: 300 },
      })
      if (res.ok) return (await res.json()) as BlogPost
    } catch {
      // fall through to local fallback
    }
  }
  return FALLBACK_BLOG_POSTS.find((post) => post.slug === slug) ?? null
}

export async function fetchBlogList(
  page = 1,
  perPage = 8,
): Promise<{ items: BlogPost[]; total: number }> {
  const base = apiBase()
  if (base) {
    try {
      const res = await fetch(
        `${base}/api/v1/public/blog?page=${page}&per_page=${perPage}`,
        { next: { revalidate: 120 } },
      )
      if (res.ok) {
        const data = await res.json()
        const items =
          Array.isArray(data.items) && data.items.length > 0
            ? (data.items as BlogPost[])
            : FALLBACK_BLOG_POSTS
        return { items, total: data.total || items.length }
      }
    } catch {
      // fall through
    }
  }
  return { items: FALLBACK_BLOG_POSTS, total: FALLBACK_BLOG_POSTS.length }
}

export async function fetchAllBlogPosts(): Promise<BlogPost[]> {
  const base = apiBase()
  if (!base) return FALLBACK_BLOG_POSTS

  const perPage = 100
  let page = 1
  let total = 0
  const all: BlogPost[] = []

  try {
    do {
      const res = await fetch(
        `${base}/api/v1/public/blog?page=${page}&per_page=${perPage}`,
        { next: { revalidate: 3600 } },
      )
      if (!res.ok) break
      const data = await res.json()
      const items = Array.isArray(data.items) ? (data.items as BlogPost[]) : []
      total = data.total || items.length
      all.push(...items)
      page += 1
    } while (all.length < total && page <= 20)
  } catch {
    return FALLBACK_BLOG_POSTS
  }

  return all.length > 0 ? all : FALLBACK_BLOG_POSTS
}

export function formatBlogDate(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}
