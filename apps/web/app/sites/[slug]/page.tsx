import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { SectionRenderer } from '@/components/landing/SectionRenderer'

type SitePayload = {
  tenant_slug: string
  business_name: string
  title: string
  meta_description: string | null
  theme: Record<string, unknown>
  sections: Array<{ type: string; props: Record<string, unknown> }>
  primary_color?: string
}

async function fetchSite(slug: string): Promise<SitePayload | null> {
  const base = process.env.INTERNAL_API_URL
  if (!base) return null
  try {
    const res = await fetch(`${base}/api/v1/public/site/${encodeURIComponent(slug)}`, {
      next: { revalidate: 60 },
    })
    if (!res.ok) return null
    return (await res.json()) as SitePayload
  } catch {
    return null
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const site = await fetchSite(slug)
  return {
    title: site?.title || site?.business_name || 'Business',
    description: site?.meta_description || undefined,
  }
}

export default async function TenantBusinessSitePage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const site = await fetchSite(slug)
  if (!site) notFound()

  const primary =
    (site.theme?.primary_color as string) ||
    site.primary_color ||
    '#166534'

  return (
    <main className="min-h-screen bg-white text-gray-900 antialiased">
      <header className="border-b border-gray-100 bg-white/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <span className="font-semibold text-gray-900">{site.business_name}</span>
        </div>
      </header>
      {site.sections.map((s, i) => (
        <SectionRenderer key={i} section={s} primaryColor={primary} />
      ))}
      <footer className="py-8 px-6 text-center text-xs text-gray-400 border-t">
        Powered by{' '}
        <a href="https://customerflowai.online" className="text-gray-500 hover:underline">
          CustomerFlow AI
        </a>
      </footer>
    </main>
  )
}
