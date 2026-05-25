import type { Metadata, Viewport } from 'next'
import { Anek_Latin } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'
import { Toaster } from 'sonner'

/**
 * Typography
 * ────────────────────────────────────────────────────────────────────────────
 *  Body / UI : Anek Latin   (variable, Google Fonts, loaded via next/font)
 *  Display   : Cabinet Grotesk (Fontshare CDN, loaded via <link> below)
 *
 *  Both font-family CSS variables are wired to `globals.css` design tokens
 *  (`--font-anek`, `--font-cabinet`).
 */
const anek = Anek_Latin({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-anek',
})

const appUrl =
  process.env.NEXT_PUBLIC_APP_URL ||
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 'http://localhost:3000')

export const metadata: Metadata = {
  metadataBase: new URL(appUrl),
  title: { default: 'CustomerFlow AI', template: '%s | CustomerFlow AI' },
  description:
    'The AI operating system for UK businesses — customers, retention, reviews and money intelligence in one enterprise-grade platform.',
  manifest: '/manifest.webmanifest',
  applicationName: 'CustomerFlow AI',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'CustomerFlow',
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
  themeColor: '#025422',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${anek.variable} --font-cabinet-loader`}
      style={{ ['--font-cabinet' as string]: '"Cabinet Grotesk"' }}
    >
      <head>
        {/* Cabinet Grotesk from Fontshare — heading font */}
        <link rel="preconnect" href="https://api.fontshare.com" crossOrigin="" />
        <link
          rel="stylesheet"
          href="https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@400,500,700,800,900&display=swap"
        />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-title" content="CustomerFlow" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      </head>
      <body className={anek.className}>
        <Providers>
          {children}
          <Toaster position="top-right" richColors theme="system" />
        </Providers>
      </body>
    </html>
  )
}
