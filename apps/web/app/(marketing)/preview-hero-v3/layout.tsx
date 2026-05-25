import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Hero V3 Preview — CustomerFlow AI',
  robots: { index: false, follow: false },
}

export default function PreviewHeroV3Layout({ children }: { children: React.ReactNode }) {
  return children
}
