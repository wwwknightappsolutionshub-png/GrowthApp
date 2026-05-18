'use client'

import { useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { landingPages, type LandingPageRow } from '@/lib/api-client'
import { SectionRenderer } from '@/components/landing/SectionRenderer'

/**
 * Authenticated preview route. Used from the dashboard editor.
 * Fetches by ID so unpublished drafts can still be previewed.
 */
export default function LandingPreview({
  params,
}: {
  params: { slug: string }
}) {
  // slug is for display only — the real fetch uses ?id.
  const _slug = params.slug
  const sp = useSearchParams()
  const id = sp.get('id')

  const { data, isLoading, error } = useQuery<LandingPageRow>({
    queryKey: ['landing-preview', id],
    queryFn: () => landingPages.get(id!).then((r) => r.data),
    enabled: !!id,
  })

  if (!id) {
    return (
      <div className="min-h-screen grid place-items-center text-sm text-gray-500">
        Missing page id. Open the preview from the dashboard editor.
      </div>
    )
  }
  if (isLoading) {
    return (
      <div className="min-h-screen grid place-items-center text-sm text-gray-500">
        Loading preview...
      </div>
    )
  }
  if (error || !data) {
    return (
      <div className="min-h-screen grid place-items-center text-sm text-red-600">
        Failed to load page.
      </div>
    )
  }

  const primary = (data.theme as { primary_color?: string })?.primary_color || '#2563EB'

  return (
    <main className="bg-white text-gray-900">
      {!data.is_published && (
        <div className="bg-amber-500 text-amber-950 text-center text-xs font-medium py-1.5">
          Preview · this page is unpublished
        </div>
      )}
      {data.sections.map((s, i) => (
        <SectionRenderer key={i} section={s} primaryColor={primary} />
      ))}
    </main>
  )
}
