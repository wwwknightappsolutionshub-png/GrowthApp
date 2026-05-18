import Image from 'next/image'
import Link from 'next/link'
import { Shield, TrendingUp, Lock, BadgeCheck } from 'lucide-react'

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="surface-light flex min-h-screen bg-background">
      {/* ── Left panel — brand + hero image ──────────────────────────── */}
      <aside className="relative hidden flex-col overflow-hidden bg-brand-forest-950 text-brand-forest-foreground lg:flex lg:w-[44%] xl:w-[40%]">
        {/* Full-bleed Pexels photo */}
        <Image
          src="https://images.pexels.com/photos/3760263/pexels-photo-3760263.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80"
          alt="UK business owner reviewing growth analytics on a laptop"
          fill
          sizes="(min-width: 1280px) 40vw, 44vw"
          className="object-cover object-center"
          priority
        />
        {/* Dark scrim for text legibility */}
        <div aria-hidden className="absolute inset-0 bg-brand-forest-950/65" />
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_100%,hsl(var(--brand-forest)/0.6),transparent_80%)]"
        />

        <div className="relative flex h-full flex-col px-10 py-10">
          {/* Logo */}
          <Link href="/" className="inline-flex items-center gap-2.5">
            <span className="relative inline-flex h-9 w-9 items-center justify-center rounded-md bg-brand-teal-400 text-brand-teal-foreground shadow-brand">
              <TrendingUp className="h-4 w-4" strokeWidth={2.5} />
              <span
                aria-hidden
                className="absolute -right-0.5 -bottom-0.5 h-2.5 w-2.5 rounded-full bg-white ring-2 ring-brand-forest-950"
              />
            </span>
            <span className="font-display text-lg font-bold tracking-tight text-white">
              CustomerFlow<span className="text-brand-teal-300">.</span>AI
            </span>
          </Link>

          {/* Main copy */}
          <div className="mt-16 flex flex-1 flex-col justify-center">
            <span className="inline-flex w-fit items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.18em] text-brand-teal-300">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-teal-300 opacity-60" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-brand-teal-300" />
              </span>
              The AI OS for UK businesses
            </span>

            <h2 className="mt-6 font-display text-4xl font-bold leading-[1.05] tracking-tight text-white xl:text-[44px]">
              One enterprise platform
              <br />
              for <span className="text-brand-teal-300">customers &amp; money</span>.
            </h2>
            <p className="mt-5 max-w-md text-base leading-relaxed text-white/80">
              AI-powered lead generation, retention, reviews, operations and
              money intelligence — connected and automated, for every UK business.
            </p>
          </div>

          {/* Security badges */}
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
              SOC 2 ready
            </div>
          </div>
        </div>
      </aside>

      {/* ── Right panel — form ───────────────────────────────────────── */}
      <main className="flex flex-1 flex-col bg-background">
        {/* Mobile logo */}
        <div className="flex items-center gap-2.5 border-b border-border px-6 py-5 lg:hidden">
          <span className="relative inline-flex h-8 w-8 items-center justify-center rounded-md bg-brand-forest-700 text-brand-forest-foreground">
            <TrendingUp className="h-4 w-4" strokeWidth={2.5} />
          </span>
          <span className="font-display text-lg font-bold tracking-tight text-foreground">
            CustomerFlow<span className="text-brand-teal-500">.</span>AI
          </span>
        </div>

        <div className="flex flex-1 items-center justify-center px-6 py-10">
          <div className="w-full max-w-md">{children}</div>
        </div>

        <footer className="flex flex-col items-center justify-between gap-2 border-t border-border px-6 py-5 sm:flex-row">
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
            © {new Date().getFullYear()} CustomerFlow AI · All rights reserved
          </p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <Link href="#" className="transition-colors hover:text-foreground">Privacy</Link>
            <Link href="#" className="transition-colors hover:text-foreground">Terms</Link>
            <Link href="#" className="transition-colors hover:text-foreground">Support</Link>
          </div>
        </footer>
      </main>
    </div>
  )
}
