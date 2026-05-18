import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { SectionRenderer } from '@/components/landing/SectionRenderer'

type PageJson = {
  slug: string
  title: string
  meta_description: string | null
  cover_image_url: string | null
  theme: Record<string, unknown>
  sections: { type: string; props: Record<string, unknown> }[]
}

async function fetchPage(tenant: string, slug: string): Promise<PageJson | null> {
  const base = process.env.INTERNAL_API_URL
  if (!base) return null
  const url = `${base}/api/v1/public/landing/${encodeURIComponent(tenant)}/${encodeURIComponent(slug)}`
  try {
    const res = await fetch(url, { next: { revalidate: 60 } })
    if (!res.ok) return null
    return (await res.json()) as PageJson
  } catch {
    return null
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ tenant: string; slug: string }>
}): Promise<Metadata> {
  const { tenant, slug } = await params
  const page = await fetchPage(tenant, slug)
  if (!page) return { title: 'Page not found' }
  return {
    title: page.title,
    description: page.meta_description || undefined,
    openGraph: {
      title: page.title,
      description: page.meta_description || undefined,
      images: page.cover_image_url ? [page.cover_image_url] : undefined,
    },
  }
}

export default async function PublicLandingPage({
  params,
}: {
  params: Promise<{ tenant: string; slug: string }>
}) {
  const { tenant, slug } = await params
  const page = await fetchPage(tenant, slug)
  if (!page) notFound()
  const primary = (page.theme as { primary_color?: string })?.primary_color || '#2563EB'
  return (
    <main className="bg-white text-gray-900 antialiased">
      {page.sections.map((s, i) => (
        <SectionRenderer key={i} section={s} primaryColor={primary} />
      ))}
      <footer className="py-6 px-6 text-center text-xs text-gray-400 border-t">
        Powered by CustomerFlow AI
      </footer>
    </main>
  )
}
