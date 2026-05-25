import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Hero Preview — CustomerFlow AI',
  robots: { index: false, follow: false },
}

export default function PreviewHeroLayout({ children }: { children: React.ReactNode }) {
  return children
}
