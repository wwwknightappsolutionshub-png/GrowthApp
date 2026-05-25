import Link from 'next/link'

import { AUTH_HEADLINE, BrandMark } from '@/components/brand/BrandMark'
import { Shield, Lock, BadgeCheck } from 'lucide-react'

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="surface-light flex min-h-screen bg-background">
      <aside className="relative hidden flex-col overflow-hidden bg-brand-forest-950 text-brand-forest-foreground lg:flex lg:w-[44%] xl:w-[40%]">
        <div
          aria-hidden
          className="absolute inset-0 bg-[url('https://images.pexels.com/photos/3760263/pexels-photo-3760263.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80')] bg-cover bg-center"
        />
        <div aria-hidden className="absolute inset-0 bg-brand-forest-950/65" />
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_100%,hsl(var(--brand-forest)/0.6),transparent_80%)]"
        />

        <div className="relative flex h-full flex-col px-10 py-10">
          <Link href="/" aria-label="CustomerFlowai home">
            <BrandMark variant="light" iconSize={36} textClassName="text-lg" />
          </Link>

          <div className="mt-16 flex flex-1 flex-col justify-center">
            <span className="inline-flex w-fit items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.18em] text-brand-teal-300">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-teal-300 opacity-60" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-brand-teal-300" />
              </span>
              One platform for your customer journey
            </span>

            <h2 className="mt-6 font-display text-3xl font-bold leading-[1.08] tracking-tight text-white xl:text-[40px]">
              {AUTH_HEADLINE}
            </h2>
            <p className="mt-5 max-w-md text-base leading-relaxed text-white/80">
              Capture leads, book jobs, run your CRM, invoice customers, and win
              them back — connected in one place with AI automations behind every step.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-white/10 pt-6 text-xs text-white/55">
            <div className="inline-flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-brand-teal-300" />
              GDPR compliant
            </div>
            <div className="inline-flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5 text-brand-teal-300" />
              256-bit SSL
            </div>
            <div className="inline-flex items-center gap-1.5">
              <BadgeCheck className="h-3.5 w-3.5 text-brand-teal-300" />
              UK data residency
            </div>
          </div>
        </div>
      </aside>

      <main className="flex flex-1 flex-col bg-background">
        <div className="flex items-center gap-2.5 border-b border-border px-6 py-5 lg:hidden">
          <Link href="/" aria-label="CustomerFlowai home">
            <BrandMark iconSize={32} />
          </Link>
        </div>

        <div className="flex flex-1 items-center justify-center px-6 py-10">
          <div className="w-full max-w-md">{children}</div>
        </div>

        <footer className="flex flex-col items-center justify-between gap-2 border-t border-border px-6 py-5 sm:flex-row">
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
            © {new Date().getFullYear()} CustomerFlowai · All rights reserved
          </p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <Link href="/privacy" className="transition-colors hover:text-foreground">
              Privacy
            </Link>
            <Link href="#" className="transition-colors hover:text-foreground">
              Terms
            </Link>
            <Link href="#" className="transition-colors hover:text-foreground">
              Support
            </Link>
          </div>
        </footer>
      </main>
    </div>
  )
}
