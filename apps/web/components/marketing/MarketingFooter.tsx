'use client'

/**
 * MarketingFooter — 5-column footer with modal popups for all footer links.
 * Modals: About, Contact, Partners, Careers (coming soon), Privacy, Terms, GDPR & DPA, Cookies.
 */

import { useState, useEffect, type ReactNode } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  TrendingUp,
  Shield,
  Lock,
  BadgeCheck,
  MapPin,
  Mail,
  Phone,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Users,
  Globe,
  Zap,
  BarChart3,
  Clock,
  Star,
} from 'lucide-react'

type ModalId =
  | 'about'
  | 'contact'
  | 'partners'
  | 'careers'
  | 'privacy'
  | 'terms'
  | 'gdpr-dpa'
  | 'cookies'
  | null

// ── Modal Shell ───────────────────────────────────────────────────────────────

function ModalShell({
  open,
  onClose,
  title,
  subtitle,
  wide,
  children,
}: {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: string
  wide?: boolean
  children: ReactNode
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose() }
    if (open) document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.22 }}
          className="fixed inset-0 z-[9997] flex items-start justify-center overflow-y-auto bg-black/60 px-4 py-10 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
          role="dialog"
          aria-modal="true"
          aria-label={title}
        >
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
            className={`relative w-full ${wide ? 'max-w-4xl' : 'max-w-2xl'} overflow-hidden rounded-2xl bg-card shadow-2xl`}
          >
            {/* Header */}
            <div className="flex items-start justify-between border-b border-border bg-brand-forest-950 px-6 py-5 text-white">
              <div>
                <h2 className="font-display text-xl font-bold">{title}</h2>
                {subtitle && <p className="mt-1 text-sm text-white/60">{subtitle}</p>}
              </div>
              <button
                onClick={onClose}
                className="ml-4 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/10 transition-colors hover:bg-white/20"
                aria-label="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            {/* Body */}
            <div className="max-h-[75vh] overflow-y-auto px-6 py-6">{children}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// ── About Modal ───────────────────────────────────────────────────────────────

function AboutModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <ModalShell open={open} onClose={onClose} title="About CustomerFlow AI" subtitle="The AI Operating System for UK Businesses" wide>
      <div className="space-y-6 text-sm leading-relaxed text-foreground/80">
        <section>
          <h3 className="font-display text-lg font-bold text-foreground">
            What is CustomerFlow AI?
          </h3>
          <p className="mt-2">
            CustomerFlow AI is the all-in-one AI-powered growth platform built exclusively for UK businesses.
            We replace 10+ disconnected point solutions — your CRM, booking system, review tool, invoicing
            software, social scheduler and cashflow dashboard — with a single intelligent platform that runs
            quietly in the background while you focus on doing great work.
          </p>
        </section>

        <section>
          <h3 className="font-display text-base font-bold text-foreground">
            Why CustomerFlow AI Exists
          </h3>
          <p className="mt-2">
            UK small business owners are drowning in admin. The average tradesperson loses 6+ hours a week
            to follow-up calls, invoice chasing, review requests and social media. The average salon owner
            juggles 4 different apps just to run their business. We built CustomerFlow AI to give every UK
            business owner access to the same enterprise-grade automation that only large corporations could
            previously afford.
          </p>
        </section>

        <div className="grid gap-4 sm:grid-cols-2">
          {[
            { icon: Zap, title: 'AI-First Architecture', desc: 'Every feature is built with AI at the core — not bolted on.' },
            { icon: Shield, title: 'UK GDPR Native', desc: 'Built for UK data residency and compliance from day one.' },
            { icon: Users, title: 'Multi-Industry', desc: 'Works for trades, hospitality, beauty, healthcare, B2B and more.' },
            { icon: BarChart3, title: 'Unified Intelligence', desc: 'One dashboard for leads, revenue, reviews and cashflow.' },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex gap-3 rounded-lg border border-border bg-muted/30 p-4">
              <Icon className="mt-0.5 h-5 w-5 shrink-0 text-brand-teal-500" />
              <div>
                <p className="font-semibold text-foreground">{title}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{desc}</p>
              </div>
            </div>
          ))}
        </div>

        <section className="rounded-xl border border-brand-forest-200 bg-brand-forest-50 p-5">
          <h3 className="font-display text-base font-bold text-brand-forest-800">
            What Are You Losing Without CustomerFlow AI?
          </h3>
          <ul className="mt-3 space-y-2">
            {[
              'Every missed call that goes unanswered costs you an average £280 job',
              'Businesses without review automation collect 4× fewer Google reviews',
              'Manual quote follow-up means 73% of sent quotes are never chased',
              'Without win-back automation, 35% of customers quietly churn each year',
              'No cashflow dashboard means end-of-month surprises and poor decisions',
            ].map((item) => (
              <li key={item} className="flex items-start gap-2 text-sm text-brand-forest-700">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-forest-600" />
                {item}
              </li>
            ))}
          </ul>
        </section>

        <div className="flex gap-3 pt-2">
          <Link
            href="/register"
            onClick={onClose}
            className="inline-flex items-center gap-2 rounded-md bg-brand-forest-700 px-5 py-2.5 text-sm font-semibold text-white shadow-brand transition-all hover:bg-brand-forest-800"
          >
            Start free trial <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </ModalShell>
  )
}

// ── Contact Modal ─────────────────────────────────────────────────────────────

function ContactModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', phone: '', message: '' })

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    // Simulate send — wire to real endpoint as needed
    await new Promise((r) => setTimeout(r, 1200))
    setSent(true)
    setLoading(false)
  }

  return (
    <ModalShell open={open} onClose={onClose} title="Get in Touch" subtitle="We'd love to hear from you">
      {sent ? (
        <div className="flex flex-col items-center py-10 text-center">
          <CheckCircle2 className="h-12 w-12 text-green-500" />
          <h3 className="mt-4 font-display text-xl font-bold text-foreground">Message sent!</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            We typically reply within 2 business hours. We look forward to speaking with you.
          </p>
          <button onClick={onClose} className="mt-6 text-sm font-medium text-brand-teal-500 hover:underline">
            Close
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Direct contact details */}
          <div className="flex flex-wrap gap-4 text-sm">
            <a
              href="mailto:connect@customerflow.tech"
              className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-4 py-3 font-medium text-foreground transition-colors hover:bg-muted"
            >
              <Mail className="h-4 w-4 text-brand-teal-500" />
              connect@customerflow.tech
            </a>
            <a
              href="tel:+447756183484"
              className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-4 py-3 font-medium text-foreground transition-colors hover:bg-muted"
            >
              <Phone className="h-4 w-4 text-brand-teal-500" />
              +44 7756 183 484
            </a>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Full name *</label>
                <input
                  type="text" required value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground outline-none ring-0 focus:border-brand-teal-400 focus:ring-1 focus:ring-brand-teal-400"
                  placeholder="Jane Smith"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Email *</label>
                <input
                  type="email" required value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground outline-none focus:border-brand-teal-400 focus:ring-1 focus:ring-brand-teal-400"
                  placeholder="jane@example.com"
                />
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Phone</label>
              <input
                type="tel" value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground outline-none focus:border-brand-teal-400 focus:ring-1 focus:ring-brand-teal-400"
                placeholder="+44 7700 000000"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Message *</label>
              <textarea
                required rows={4} value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })}
                className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground outline-none focus:border-brand-teal-400 focus:ring-1 focus:ring-brand-teal-400"
                placeholder="Tell us how we can help…"
              />
            </div>
            <button
              type="submit" disabled={loading}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand-forest-700 py-3 text-sm font-semibold text-white transition-all hover:bg-brand-forest-800 disabled:opacity-60"
            >
              {loading ? 'Sending…' : <>Send message <ArrowRight className="h-3.5 w-3.5" /></>}
            </button>
          </form>
        </div>
      )}
    </ModalShell>
  )
}

// ── Partners Modal ────────────────────────────────────────────────────────────

function PartnersModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', company: '', type: '', clients: '' })

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    await new Promise((r) => setTimeout(r, 1200))
    setSent(true)
    setLoading(false)
  }

  return (
    <ModalShell open={open} onClose={onClose} title="Partner with CustomerFlow AI" subtitle="Grow your income. Grow your clients. Grow together." wide>
      {sent ? (
        <div className="flex flex-col items-center py-10 text-center">
          <CheckCircle2 className="h-12 w-12 text-green-500" />
          <h3 className="mt-4 font-display text-xl font-bold text-foreground">Application received!</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Our partnerships team will be in touch within 48 hours.
          </p>
        </div>
      ) : (
        <div className="space-y-8 text-sm leading-relaxed">
          {/* Audience targeting */}
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              {
                icon: Globe,
                title: 'Digital Marketing Freelancers',
                desc: 'Add a recurring revenue stream by reselling CustomerFlow AI to your existing clients. Earn up to 30% commission every month — for life.',
                cta: 'Ideal for SEO, PPC & social media freelancers',
              },
              {
                icon: Sparkles,
                title: 'Graphic Designers',
                desc: 'Offer your clients a branded, white-labelled growth platform under your studio name. Premium positioning, zero tech headaches.',
                cta: 'Perfect for studio owners and brand designers',
              },
              {
                icon: BarChart3,
                title: 'Marketing Agencies',
                desc: 'Bundle CustomerFlow AI into your client retainers or offer it as a standalone product. Volume pricing and co-branded materials provided.',
                cta: 'Designed for agencies of all sizes',
              },
            ].map(({ icon: Icon, title, desc, cta }) => (
              <div key={title} className="flex flex-col rounded-xl border border-border bg-muted/30 p-5">
                <Icon className="h-6 w-6 text-brand-teal-500" />
                <h3 className="mt-3 font-display text-base font-bold text-foreground">{title}</h3>
                <p className="mt-2 text-xs text-muted-foreground flex-1">{desc}</p>
                <span className="mt-3 text-[10px] font-semibold uppercase tracking-wide text-brand-teal-500">{cta}</span>
              </div>
            ))}
          </div>

          {/* Benefits */}
          <section>
            <h3 className="font-display text-base font-bold text-foreground">Partner Benefits</h3>
            <div className="mt-3 grid gap-2.5 sm:grid-cols-2">
              {[
                'Up to 30% monthly recurring commission',
                'White-label option on Pro plan',
                'Co-branded marketing materials',
                'Dedicated partner success manager',
                'Early access to new features',
                'Priority partner support queue',
                'Quarterly partner webinars and training',
                'Listed in the CustomerFlow partner directory',
              ].map((b) => (
                <div key={b} className="flex items-start gap-2 text-sm">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-forest-700" />
                  {b}
                </div>
              ))}
            </div>
          </section>

          {/* Application form */}
          <section className="border-t border-border pt-6">
            <h3 className="font-display text-base font-bold text-foreground">Apply to Join</h3>
            <form onSubmit={submit} className="mt-4 space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Full name *</label>
                  <input type="text" required value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none focus:border-brand-teal-400 focus:ring-1 focus:ring-brand-teal-400"
                    placeholder="Your name" />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Email *</label>
                  <input type="email" required value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none focus:border-brand-teal-400 focus:ring-1 focus:ring-brand-teal-400"
                    placeholder="you@company.com" />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Company / Studio</label>
                  <input type="text" value={form.company}
                    onChange={(e) => setForm({ ...form, company: e.target.value })}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none focus:border-brand-teal-400 focus:ring-1 focus:ring-brand-teal-400"
                    placeholder="Acme Agency Ltd" />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">I am a… *</label>
                  <select required value={form.type}
                    onChange={(e) => setForm({ ...form, type: e.target.value })}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none focus:border-brand-teal-400 focus:ring-1 focus:ring-brand-teal-400">
                    <option value="">Select type</option>
                    <option>Digital Marketing Freelancer</option>
                    <option>Graphic Designer</option>
                    <option>Marketing Agency</option>
                    <option>Web Developer</option>
                    <option>Business Consultant</option>
                    <option>Other</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">How many client businesses do you work with?</label>
                <select value={form.clients}
                  onChange={(e) => setForm({ ...form, clients: e.target.value })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none focus:border-brand-teal-400 focus:ring-1 focus:ring-brand-teal-400">
                  <option value="">Select range</option>
                  <option>1–5</option>
                  <option>6–20</option>
                  <option>21–50</option>
                  <option>50+</option>
                </select>
              </div>
              <button type="submit" disabled={loading}
                className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand-teal-400 py-3 text-sm font-bold text-brand-teal-foreground transition-all hover:bg-brand-teal-300 disabled:opacity-60">
                {loading ? 'Submitting…' : <>Apply to Partner Programme <ArrowRight className="h-3.5 w-3.5" /></>}
              </button>
            </form>
          </section>
        </div>
      )}
    </ModalShell>
  )
}

// ── Careers Modal ─────────────────────────────────────────────────────────────

function CareersModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <ModalShell open={open} onClose={onClose} title="Careers at CustomerFlow AI" subtitle="Coming Soon — We're building something great">
      <div className="flex flex-col items-center py-10 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-forest-950">
          <Sparkles className="h-8 w-8 text-brand-teal-300" />
        </div>
        <h3 className="mt-5 font-display text-2xl font-bold text-foreground">We're Hiring Soon</h3>
        <p className="mt-3 max-w-md text-sm leading-relaxed text-muted-foreground">
          CustomerFlow AI is growing fast. We will be opening roles in engineering, product, customer
          success and growth marketing very soon. Leave your email to be first in the queue.
        </p>
        <form
          className="mt-6 flex w-full max-w-sm flex-col gap-3 sm:flex-row"
          onSubmit={(e) => { e.preventDefault(); onClose() }}
        >
          <input
            type="email" required
            placeholder="your@email.com"
            className="flex-1 rounded-lg border border-border bg-background px-4 py-2.5 text-sm outline-none focus:border-brand-teal-400 focus:ring-1 focus:ring-brand-teal-400"
          />
          <button
            type="submit"
            className="rounded-lg bg-brand-forest-700 px-5 py-2.5 text-sm font-semibold text-white transition-all hover:bg-brand-forest-800"
          >
            Notify me
          </button>
        </form>
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          {[
            { label: 'Remote-first', icon: Globe },
            { label: 'Equity options', icon: Star },
            { label: 'UK-based team', icon: MapPin },
          ].map(({ label, icon: Icon }) => (
            <div key={label} className="flex flex-col items-center gap-2 rounded-xl border border-border p-4">
              <Icon className="h-5 w-5 text-brand-teal-500" />
              <span className="text-xs font-medium text-foreground">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </ModalShell>
  )
}

// ── Legal Modals ──────────────────────────────────────────────────────────────

const LEGAL_CONTENT: Record<string, { title: string; subtitle: string; body: ReactNode }> = {
  privacy: {
    title: 'Privacy Policy',
    subtitle: 'Last updated: May 2026 | CustomerFlow AI Ltd',
    body: (
      <div className="space-y-5 text-sm leading-relaxed text-foreground/80">
        <p className="font-semibold text-foreground">
          CustomerFlow AI is committed to protecting the privacy of every individual who interacts with our platform.
          This Privacy Policy explains how we collect, use, store and protect your personal data in compliance with
          UK GDPR and the Data Protection Act 2018.
        </p>
        {[
          { h: '1. Who We Are', p: 'CustomerFlow AI Ltd ("we", "us", "our") is the data controller for personal data processed through the CustomerFlow AI platform. Contact us at connect@customerflow.tech with any data-related queries.' },
          { h: '2. What Data We Collect', p: 'We collect: (a) Account data — name, email, phone, business name and billing details when you register; (b) Usage data — features accessed, API calls, session metadata; (c) Customer data — data you input about your own customers, for which you are the data controller and we are the data processor; (d) Communication data — emails, SMS and WhatsApp messages sent via our platform.' },
          { h: '3. Lawful Basis for Processing', p: 'We process your personal data under the following lawful bases: Contract (to deliver our services), Legitimate Interests (fraud prevention, security, product improvement), Consent (marketing emails where applicable), and Legal Obligation (financial records, HMRC compliance).' },
          { h: '4. How We Use Your Data', p: 'Your data is used to: deliver and improve the CustomerFlow AI service; send transactional and account-related notifications; provide customer support; process billing and prevent fraud; comply with legal obligations.' },
          { h: '5. Data Retention', p: 'Account data is retained for the duration of your subscription plus 7 years for legal and financial compliance. Customer data you upload is retained according to your configured retention settings and deleted on request.' },
          { h: '6. Your Rights', p: 'Under UK GDPR you have the right to: access your data; correct inaccurate data; request erasure; restrict or object to processing; data portability; and lodge a complaint with the ICO (ico.org.uk). Exercise these rights at connect@customerflow.tech.' },
          { h: '7. UK Data Residency', p: 'All data is stored exclusively on UK-based servers. We do not transfer personal data outside the UK without appropriate safeguards.' },
          { h: '8. Cookies', p: 'We use essential, functional and analytics cookies. See our Cookie Policy for full details.' },
          { h: '9. Contact', p: 'Data Controller: CustomerFlow AI Ltd | Email: connect@customerflow.tech | Phone: +44 7756 183 484' },
        ].map(({ h, p }) => (
          <div key={h}>
            <h3 className="font-semibold text-foreground">{h}</h3>
            <p className="mt-1">{p}</p>
          </div>
        ))}
      </div>
    ),
  },
  terms: {
    title: 'Terms of Service',
    subtitle: 'Effective: May 2026 | CustomerFlow AI Ltd',
    body: (
      <div className="space-y-5 text-sm leading-relaxed text-foreground/80">
        <p className="font-semibold text-foreground">
          By accessing or using CustomerFlow AI you agree to be bound by these Terms of Service.
          Please read them carefully. If you do not agree, do not use the service.
        </p>
        {[
          { h: '1. Service Description', p: 'CustomerFlow AI provides a SaaS platform for UK businesses including CRM, lead management, booking, marketing automation, review management, invoicing and AI-powered analytics. The service is provided on a subscription basis.' },
          { h: '2. Subscriptions and Payment', p: 'Subscriptions are billed monthly or annually. Payment is due in advance. We use Stripe for secure payment processing. Failed payments may result in service suspension. All prices are in GBP and exclusive of VAT unless stated.' },
          { h: '3. Free Trial', p: 'New accounts receive a 14-day free trial on the Growth plan. No credit card is required to start. At the end of the trial, your account converts to the plan you select, or access is suspended if no plan is chosen.' },
          { h: '4. Acceptable Use', p: 'You agree not to use CustomerFlow AI for unlawful purposes, to send spam or unsolicited communications, to upload malicious code, to attempt to access other tenants\' data, or to violate any applicable laws including UK GDPR.' },
          { h: '5. Data Ownership', p: 'You retain full ownership of all customer data you upload to CustomerFlow AI. We act as your data processor. You are responsible for ensuring you have lawful basis to process any data you input.' },
          { h: '6. Uptime and SLA', p: 'We target 99.9% monthly uptime for all paid plans. Scheduled maintenance is excluded. In the event of sustained downtime, credits may be applied at our discretion.' },
          { h: '7. Cancellation', p: 'You may cancel your subscription at any time from your account settings. Cancellation takes effect at the end of the current billing period. No refunds are issued for partial periods.' },
          { h: '8. Limitation of Liability', p: 'To the maximum extent permitted by law, CustomerFlow AI\'s liability is limited to the total fees paid by you in the 3 months preceding the claim. We exclude liability for indirect, consequential or incidental losses.' },
          { h: '9. Governing Law', p: 'These Terms are governed by the laws of England and Wales. Any disputes are subject to the exclusive jurisdiction of the courts of England and Wales.' },
        ].map(({ h, p }) => (
          <div key={h}><h3 className="font-semibold text-foreground">{h}</h3><p className="mt-1">{p}</p></div>
        ))}
      </div>
    ),
  },
  'gdpr-dpa': {
    title: 'GDPR & Data Processing Agreement',
    subtitle: 'CustomerFlow AI Ltd — Data Processor Agreement',
    body: (
      <div className="space-y-5 text-sm leading-relaxed text-foreground/80">
        <p className="font-semibold text-foreground">
          This Data Processing Agreement ("DPA") forms part of the Terms of Service between you ("Controller")
          and CustomerFlow AI Ltd ("Processor"). It governs how we process personal data on your behalf in
          accordance with UK GDPR Article 28.
        </p>
        {[
          { h: '1. Scope and Purpose', p: 'CustomerFlow AI processes personal data solely to deliver the services described in the Terms of Service. We will not process data for any other purpose without your explicit instruction.' },
          { h: '2. Data Security Measures', p: 'We implement appropriate technical and organisational measures including: TLS 1.3 encryption in transit, AES-256 encryption at rest, role-based access controls, 2FA enforcement, regular penetration testing, and UK-only data hosting.' },
          { h: '3. Sub-processors', p: 'We may engage sub-processors to deliver specific service components (e.g. Stripe for payments, Twilio for SMS, email delivery providers). All sub-processors are bound by equivalent data protection obligations. Current sub-processor list available on request.' },
          { h: '4. Data Subject Rights', p: 'We will assist you in responding to data subject rights requests (access, erasure, portability, rectification) within the timeframes required by UK GDPR. Our platform includes automated erasure workflows to simplify compliance.' },
          { h: '5. Breach Notification', p: 'We will notify you of any confirmed personal data breach affecting your data within 48 hours of our becoming aware, to allow you to meet your 72-hour ICO notification obligation.' },
          { h: '6. Data Retention and Deletion', p: 'Data is retained according to your configured settings. On subscription termination, your data is available to export for 30 days, then securely deleted. Deletion certificates are available on request.' },
          { h: '7. Audits', p: 'You may audit our data processing activities with 30 days written notice, subject to confidentiality obligations and reasonable frequency (once per 12 months).' },
          { h: '8. UK Data Residency', p: 'All data processing occurs within the United Kingdom. No transfers to third countries are made without your explicit consent and appropriate safeguards.' },
          { h: '9. Contact', p: 'Data Protection enquiries: connect@customerflow.tech | Phone: +44 7756 183 484' },
        ].map(({ h, p }) => (
          <div key={h}><h3 className="font-semibold text-foreground">{h}</h3><p className="mt-1">{p}</p></div>
        ))}
      </div>
    ),
  },
  cookies: {
    title: 'Cookie Policy',
    subtitle: 'Last updated: May 2026 | CustomerFlow AI Ltd',
    body: (
      <div className="space-y-5 text-sm leading-relaxed text-foreground/80">
        <p className="font-semibold text-foreground">
          CustomerFlow AI uses cookies and similar tracking technologies to operate the platform, remember your
          preferences and understand how visitors use our site. This policy explains what cookies we use and how
          to control them.
        </p>
        {[
          { h: 'What Are Cookies?', p: 'Cookies are small text files stored on your device when you visit a website. They help the site remember your settings and actions so you do not have to re-enter them on future visits.' },
          { h: 'Essential Cookies', p: 'These cookies are necessary for the platform to function. They include session tokens, CSRF protection and login state management. You cannot opt out of essential cookies without disrupting service functionality.' },
          { h: 'Functional Cookies', p: 'These remember your preferences — such as dark mode, dashboard layout and notification settings — to personalise your experience.' },
          { h: 'Analytics Cookies', p: 'We use privacy-first analytics (no third-party tracking) to understand which features are used and how the platform can be improved. Analytics data is aggregated and never sold.' },
          { h: 'Marketing Cookies', p: 'If you arrive via a paid channel, we may set a cookie to attribute your registration to the correct campaign. No marketing cookies are shared with advertising networks.' },
          { h: 'Third-Party Cookies', p: 'Our payment provider (Stripe) sets cookies during checkout for fraud prevention. These are governed by Stripe\'s own privacy policy.' },
          { h: 'Managing Cookies', p: 'You can control cookies via your browser settings. Note that disabling essential cookies will prevent you from logging in to CustomerFlow AI. For browsers: Chrome → Settings → Privacy → Cookies; Firefox → Options → Privacy & Security; Safari → Preferences → Privacy.' },
          { h: 'Contact', p: 'Questions about our cookie use: connect@customerflow.tech' },
        ].map(({ h, p }) => (
          <div key={h}><h3 className="font-semibold text-foreground">{h}</h3><p className="mt-1">{p}</p></div>
        ))}
      </div>
    ),
  },
}

function LegalModal({ id, open, onClose }: { id: ModalId; open: boolean; onClose: () => void }) {
  const content = id && LEGAL_CONTENT[id]
  if (!content) return null
  return (
    <ModalShell open={open} onClose={onClose} title={content.title} subtitle={content.subtitle}>
      {content.body}
    </ModalShell>
  )
}

// ── Footer ────────────────────────────────────────────────────────────────────

const trustBadges = [
  { label: 'GDPR Compliant', icon: Shield },
  { label: 'ISO 27001 Ready', icon: Lock },
  { label: 'Stripe Verified', icon: BadgeCheck },
  { label: 'UK Data Residency', icon: MapPin },
]

export function MarketingFooter() {
  const [modal, setModal] = useState<ModalId>(null)

  function open(id: ModalId) { setModal(id) }
  function close() { setModal(null) }

  return (
    <>
      {/* ── Footer ──────────────────────────────────────────────────── */}
      <footer className="border-t border-brand-forest-900/40 bg-brand-forest-950 py-16 text-brand-forest-foreground/60">
        <div className="container">
          <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-5">

            {/* Col 1 — Brand */}
            <div className="lg:col-span-1">
              <Link href="/" className="inline-flex items-center gap-2.5">
                <span className="relative inline-flex h-8 w-8 items-center justify-center rounded-md bg-brand-forest-700">
                  <TrendingUp className="h-4 w-4 text-white" strokeWidth={2.5} />
                  <span aria-hidden className="absolute -right-0.5 -bottom-0.5 h-2.5 w-2.5 rounded-full bg-brand-teal-400 ring-2 ring-brand-forest-950" />
                </span>
                <span className="font-display text-[17px] font-bold tracking-tight text-white">
                  CustomerFlow<span className="text-brand-teal-300">.</span>AI
                </span>
              </Link>
              <p className="mt-4 max-w-xs text-sm leading-relaxed text-white/55">
                The AI operating system for UK businesses. Lead generation,
                retention, reviews and money intelligence — unified and automated.
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                {trustBadges.map((b) => (
                  <span key={b.label} className="inline-flex items-center gap-1 rounded border border-white/10 bg-white/5 px-2 py-1 font-mono text-[10px] font-medium uppercase tracking-wider text-white/60">
                    <b.icon className="h-3 w-3 text-brand-teal-300" />
                    {b.label}
                  </span>
                ))}
              </div>
            </div>

            {/* Col 2 — Product */}
            <div>
              <h4 className="font-display text-sm font-bold text-white">Product</h4>
              <ul className="mt-4 space-y-2.5 text-sm">
                {[
                  { label: 'Features', href: '/#platform' },
                  { label: 'How it works', href: '/#how-it-works' },
                  { label: 'Pricing', href: '/#pricing' },
                  { label: 'Blog', href: '/blog' },
                  { label: 'Changelog', href: '#' },
                  { label: 'API docs', href: '#' },
                ].map((l) => (
                  <li key={l.label}>
                    <Link href={l.href} className="transition-colors hover:text-white">{l.label}</Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Col 3 — Industries */}
            <div>
              <h4 className="font-display text-sm font-bold text-white">Industries</h4>
              <ul className="mt-4 space-y-2.5 text-sm">
                {['Trades', 'Hospitality', 'Beauty & Wellness', 'Healthcare', 'Real Estate', 'B2B'].map((l) => (
                  <li key={l}>
                    <Link href="/#industries" className="transition-colors hover:text-white">
                      CustomerFlow for {l}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Col 4 — Company */}
            <div>
              <h4 className="font-display text-sm font-bold text-white">Company</h4>
              <ul className="mt-4 space-y-2.5 text-sm">
                <li><button onClick={() => open('about')} className="transition-colors hover:text-white text-left">About</button></li>
                <li><Link href="/blog" className="transition-colors hover:text-white">Blog</Link></li>
                <li><button onClick={() => open('careers')} className="transition-colors hover:text-white text-left">Careers</button></li>
                <li><button onClick={() => open('contact')} className="transition-colors hover:text-white text-left">Contact</button></li>
                <li><button onClick={() => open('partners')} className="transition-colors hover:text-white text-left">Partners</button></li>
              </ul>
            </div>

            {/* Col 5 — Legal */}
            <div>
              <h4 className="font-display text-sm font-bold text-white">Legal</h4>
              <ul className="mt-4 space-y-2.5 text-sm">
                <li><button onClick={() => open('privacy')} className="transition-colors hover:text-white text-left">Privacy Policy</button></li>
                <li><button onClick={() => open('terms')} className="transition-colors hover:text-white text-left">Terms of Service</button></li>
                <li><button onClick={() => open('gdpr-dpa')} className="transition-colors hover:text-white text-left">GDPR &amp; DPA</button></li>
                <li><button onClick={() => open('cookies')} className="transition-colors hover:text-white text-left">Cookie Policy</button></li>
              </ul>
            </div>
          </div>

          <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-white/10 pt-8 text-xs md:flex-row">
            <p className="text-white/40">
              © {new Date().getFullYear()} CustomerFlow AI Ltd · Registered in England &amp; Wales · Built for UK businesses.
            </p>
            <div className="flex items-center gap-3 text-white/40">
              <span className="inline-flex items-center gap-1.5">
                <Shield className="h-3.5 w-3.5 text-brand-teal-300" />
                GDPR Compliant
              </span>
              <span className="text-white/20">·</span>
              <span>ISO 27001 Ready</span>
              <span className="text-white/20">·</span>
              <span>UK Data Hosting</span>
            </div>
          </div>
        </div>
      </footer>

      {/* ── Modals ────────────────────────────────────────────────────── */}
      <AboutModal open={modal === 'about'} onClose={close} />
      <ContactModal open={modal === 'contact'} onClose={close} />
      <PartnersModal open={modal === 'partners'} onClose={close} />
      <CareersModal open={modal === 'careers'} onClose={close} />
      <LegalModal id={modal} open={['privacy', 'terms', 'gdpr-dpa', 'cookies'].includes(modal ?? '')} onClose={close} />
    </>
  )
}
