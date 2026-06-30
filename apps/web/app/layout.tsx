import type { Metadata, Viewport } from 'next'
import { Anek_Latin, Montserrat } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'
import { ResponsiveToaster } from '@/components/ui/ResponsiveToaster'
import { SITE_URL } from '@/lib/seo'

/**
 * Typography
 * ────────────────────────────────────────────────────────────────────────────
 *  Body / UI : Montserrat  (variable, Google Fonts, loaded via next/font)
 *  Display   : Anek Latin  (variable, Google Fonts, loaded via next/font)
 *
 *  Typography — Montserrat + Anek Latin only. No other typefaces permitted.
 *  Both font-family CSS variables are wired to `globals.css` design tokens
 *  (`--font-montserrat`, `--font-anek`).
 */
const montserrat = Montserrat({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  display: 'swap',
  adjustFontFallback: false,
  variable: '--font-montserrat',
})

const anek = Anek_Latin({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
  adjustFontFallback: false,
  variable: '--font-anek',
})

const appUrl = SITE_URL

export const metadata: Metadata = {
  metadataBase: new URL(appUrl),
  title: { default: 'CustomerFlowai', template: '%s | CustomerFlowai' },
  description:
    'The AI operating system for UK businesses — customers, retention, reviews and money intelligence in one enterprise-grade platform.',
  manifest: '/manifest.webmanifest',
  applicationName: 'CustomerFlowai',
  robots: { index: true, follow: true },
  openGraph: {
    type: 'website',
    locale: 'en_GB',
    siteName: 'CustomerFlowai',
  },
  twitter: {
    card: 'summary_large_image',
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'CustomerFlowai',
  },
  icons: {
    icon: [
      { url: '/icons/icon.svg', type: 'image/svg+xml' },
      { url: '/icon', sizes: '32x32', type: 'image/png' },
    ],
    shortcut: '/icons/icon.svg',
    apple: [{ url: '/apple-icon', sizes: '180x180', type: 'image/png' }],
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  viewportFit: 'cover',
  themeColor: '#025422',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${montserrat.variable} ${anek.variable}`}
    >
      <head>
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-title" content="CustomerFlow" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      </head>
      <body className="font-sans antialiased">
        <Providers>
          {children}
          <ResponsiveToaster richColors theme="system" />
        </Providers>
      </body>
    </html>
  )
}
