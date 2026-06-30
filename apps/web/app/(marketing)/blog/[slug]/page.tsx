import type { Metadata } from 'next'
import Image from 'next/image'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ArrowLeft, ArrowRight, Clock } from 'lucide-react'
import { BlogPostJsonLd } from '@/components/seo/BlogPostJsonLd'
import { BreadcrumbJsonLd } from '@/components/seo/BreadcrumbJsonLd'
import { fetchAllBlogPosts, fetchBlogPost, formatBlogDate } from '@/lib/blog'
import { canonical, DEFAULT_OG_IMAGE } from '@/lib/seo'

export const revalidate = 300

interface Props {
  params: { slug: string }
}

export async function generateStaticParams() {
  const posts = await fetchAllBlogPosts()
  return posts.map((post) => ({ slug: post.slug }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = await fetchBlogPost(params.slug)
  if (!post) return {}

  const title = post.seo_title ?? post.title
  const description = post.seo_description ?? post.excerpt ?? undefined
  const url = canonical(`/blog/${post.slug}`)

  return {
    title,
    description,
    keywords: post.category ? `${post.category}, UK business growth, CustomerFlowai` : undefined,
    openGraph: {
      title,
      description: description ?? undefined,
      type: 'article',
      publishedTime: post.published_at ?? undefined,
      modifiedTime: post.updated_at ?? post.published_at ?? undefined,
      authors: post.author_name ? [post.author_name] : undefined,
      images: post.image_url
        ? [{ url: post.image_url, width: 1200, height: 630, alt: post.title }]
        : [DEFAULT_OG_IMAGE],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description: description ?? undefined,
      images: post.image_url ? [post.image_url] : [DEFAULT_OG_IMAGE.url],
    },
    alternates: { canonical: url },
    robots: { index: true, follow: true },
  }
}

const CATEGORY_COLORS: Record<string, string> = {
  Trades: 'bg-amber-100 text-amber-700',
  Strategy: 'bg-blue-100 text-blue-700',
  Reviews: 'bg-green-100 text-green-700',
  Bookings: 'bg-purple-100 text-purple-700',
  'Lead Generation': 'bg-orange-100 text-orange-700',
  Hospitality: 'bg-pink-100 text-pink-700',
  Compliance: 'bg-red-100 text-red-700',
  Guide: 'bg-gray-100 text-gray-700',
}

function categoryClass(cat: string | null) {
  return CATEGORY_COLORS[cat ?? 'Guide'] ?? 'bg-gray-100 text-gray-700'
}

export default async function BlogPostPage({ params }: Props) {
  const post = await fetchBlogPost(params.slug)
  if (!post) notFound()

  return (
    <article className="min-h-screen bg-background">
      <BlogPostJsonLd post={post} />
      <BreadcrumbJsonLd
        items={[
          { name: 'Home', path: '/' },
          { name: 'Blog', path: '/blog' },
          { name: post.title, path: `/blog/${post.slug}` },
        ]}
      />

      {post.image_url && (
        <div className="relative aspect-[21/9] w-full overflow-hidden bg-muted">
          <Image
            src={post.image_url}
            alt={post.title}
            fill
            priority
            sizes="100vw"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background via-background/20 to-transparent" />
        </div>
      )}

      <div className="container max-w-3xl py-10 sm:py-14">
        <Link
          href="/blog"
          className="mb-8 inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to blog
        </Link>

        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          <span
            className={`rounded-full px-2.5 py-0.5 font-semibold uppercase tracking-wide ${categoryClass(post.category)}`}
          >
            {post.category ?? 'Guide'}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {post.read_minutes ?? 5} min read
          </span>
          {post.published_at && <time dateTime={post.published_at}>{formatBlogDate(post.published_at)}</time>}
          {post.author_name && <span>by {post.author_name}</span>}
        </div>

        <h1 className="mt-5 font-display text-3xl font-bold leading-tight text-foreground sm:text-4xl lg:text-5xl">
          {post.title}
        </h1>

        {post.excerpt && (
          <p className="mt-4 text-lg leading-relaxed text-muted-foreground">{post.excerpt}</p>
        )}

        {post.content ? (
          <div
            className="prose prose-sm mt-10 max-w-none prose-headings:font-display prose-headings:text-foreground prose-p:text-foreground/80 prose-li:text-foreground/80 prose-strong:text-foreground prose-a:text-brand-teal-500"
            dangerouslySetInnerHTML={{ __html: post.content }}
          />
        ) : (
          <p className="mt-10 text-muted-foreground italic">Full post content coming soon.</p>
        )}

        <div className="mt-12 flex flex-col gap-4 border-t border-border pt-8 sm:flex-row sm:items-center sm:justify-between">
          <Link
            href="/blog"
            className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            More articles
          </Link>
          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-2 rounded-md bg-brand-forest-700 px-6 py-3 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800"
          >
            Start free trial
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </article>
  )
}
