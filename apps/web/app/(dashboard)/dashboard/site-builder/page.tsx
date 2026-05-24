'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowRight,
  Download,
  ExternalLink,
  Gift,
  Globe,
  Loader2,
  QrCode,
  Sparkles,
} from 'lucide-react'
import { toast } from 'sonner'
import { businessSite, marketingTemplates, tenants } from '@/lib/api-client'

const NICHE_LABEL: Record<string, string> = {
  trades: 'Trades & services',
  beauty: 'Beauty & wellness',
  healthcare: 'Healthcare',
  hospitality: 'Hospitality',
  generic: 'Professional',
  real_estate: 'Property',
}

export default function SiteBuilderPage() {
  const router = useRouter()
  const qc = useQueryClient()

  const { data: tenant } = useQuery({
    queryKey: ['tenant', 'me'],
    queryFn: () => tenants.get().then((r) => r.data),
  })

  const { data: site, isLoading } = useQuery({
    queryKey: ['business-site'],
    queryFn: () => businessSite.getStatus().then((r) => r.data),
  })

  const { data: templates, isLoading: templatesLoading } = useQuery({
    queryKey: ['landing-templates', 'site-builder'],
    queryFn: () => marketingTemplates.list().then((r) => r.data),
    enabled: !site?.primary_page_id,
  })

  const bootstrap = useMutation({
    mutationFn: (templateSlug: string) =>
      businessSite.bootstrap(templateSlug).then((r) => r.data),
    onSuccess: (data) => {
      toast.success('Enterprise page created — customize it next')
      qc.invalidateQueries({ queryKey: ['business-site'] })
      if (data.redirect_to) router.push(data.redirect_to)
    },
    onError: () => toast.error('Could not create page'),
  })

  const publish = useMutation({
    mutationFn: () => businessSite.publish().then((r) => r.data),
    onSuccess: () => {
      toast.success('Site published! QR code sent to your email.')
      qc.invalidateQueries({ queryKey: ['business-site'] })
    },
    onError: () => toast.error('Publish failed — add a lead form section first'),
  })

  const downloadQr = () => {
    window.open('/api/v1/tenants/me/business-site/qr.png', '_blank')
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-24 text-muted-foreground">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <p className="text-xs font-mono uppercase tracking-widest text-brand-teal-100/60 mb-2">
          Post-onboarding · Lead capture
        </p>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Globe className="w-7 h-7 text-brand-teal-300" />
          Your business page
        </h1>
        <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
          Launch a professional, category-matched page with CTAs and enquiry forms. When you publish,
          you get a unique link{' '}
          <code className="text-xs bg-brand-forest-900 px-1 rounded">
            {tenant?.slug || 'your-business'}.customerflowai.online
          </code>{' '}
          plus a QR code by email.
        </p>
      </div>

      {site?.is_published && (
        <div className="rounded-xl border border-green-800/40 bg-green-950/30 p-6 space-y-4">
          <p className="font-semibold text-green-100 flex items-center gap-2">
            <Sparkles className="w-4 h-4" /> Live on the web
          </p>
          <p className="text-sm text-green-100/80 break-all">{site.public_url}</p>
          <div className="flex flex-wrap gap-3">
            <a
              href={site.public_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-green-200 hover:underline"
            >
              <ExternalLink className="w-4 h-4" /> Open site
            </a>
            <button
              type="button"
              onClick={downloadQr}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-green-200 hover:underline"
            >
              <Download className="w-4 h-4" /> Download QR
            </button>
            {site.edit_url && (
              <Link
                href={site.edit_url}
                className="inline-flex items-center gap-1.5 text-sm font-medium text-green-200 hover:underline"
              >
                Edit page <ArrowRight className="w-4 h-4" />
              </Link>
            )}
          </div>
          {site.qr_png_base64 && (
            <div className="pt-2">
              <img
                src={`data:image/png;base64,${site.qr_png_base64}`}
                alt="Business page QR code"
                width={160}
                height={160}
                className="rounded-lg bg-white p-2"
              />
            </div>
          )}
        </div>
      )}

      {(site as { memberships_url?: string | null })?.memberships_url && (
        <div className="rounded-xl border border-brand-teal-500/30 bg-brand-teal-600/10 p-5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <Gift className="w-5 h-5 text-brand-teal-300 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-white text-sm">Memberships page</p>
              <p className="text-xs text-brand-teal-100/75 mt-1 break-all">
                {(site as { memberships_url?: string }).memberships_url}
              </p>
              <p className="text-[10px] text-brand-teal-100/50 mt-1">
                Alias: /p/{site.tenant_slug}/loyalty
              </p>
            </div>
          </div>
          <Link
            href="/dashboard/membership-rewards?section=landing"
            className="text-sm font-medium text-brand-teal-300 hover:text-white"
          >
            Edit landing →
          </Link>
        </div>
      )}

      {(site as { rewards_portal_url?: string | null })?.rewards_portal_url && (
        <div className="rounded-xl border border-brand-teal-500/30 bg-brand-teal-600/10 p-5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <QrCode className="w-5 h-5 text-brand-teal-300 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-white text-sm">Customer rewards wallet</p>
              <p className="text-xs text-brand-teal-100/75 mt-1 break-all">
                {(site as { rewards_portal_url?: string }).rewards_portal_url}
              </p>
            </div>
          </div>
          <Link
            href="/dashboard/membership-rewards/scan"
            className="text-sm font-medium text-brand-teal-300 hover:text-white"
          >
            Staff QR scan →
          </Link>
        </div>
      )}

      {!site?.primary_page_id ? (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-white">Choose an enterprise template</h2>
          <p className="text-sm text-muted-foreground">
            Matched to <strong className="text-white">{tenant?.business_type || 'your trade'}</strong>.
            You can edit every section, CTA, and form before publishing.
          </p>
          {templatesLoading ? (
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          ) : (
            <ul className="grid gap-4 sm:grid-cols-2">
              {(templates as Array<{
                slug: string
                name: string
                niche: string
                description: string | null
              }>)?.map((t) => (
                <li
                  key={t.slug}
                  className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-5 flex flex-col"
                >
                  <span className="text-[10px] font-mono uppercase tracking-wider text-brand-teal-100/50">
                    {NICHE_LABEL[t.niche] || t.niche}
                  </span>
                  <h3 className="font-semibold text-white mt-1">{t.name}</h3>
                  <p className="text-xs text-brand-teal-100/60 mt-2 flex-1">
                    {t.description || 'Lead-focused layout with hero, trust, FAQ, and enquiry form.'}
                  </p>
                  <button
                    type="button"
                    disabled={bootstrap.isPending}
                    onClick={() => bootstrap.mutate(t.slug)}
                    className="mt-4 w-full py-2 rounded-lg bg-brand-forest-700 text-sm font-medium text-white hover:bg-brand-forest-800 disabled:opacity-50"
                  >
                    {bootstrap.isPending ? 'Creating…' : 'Use this template'}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white">
            {site.primary_page_title || 'Your page'}
          </h2>
          <p className="text-sm text-brand-teal-100/70">
            Customize sections, headlines, and the lead form in the visual editor. Publish when you are
            ready to share your link and QR code.
          </p>
          <div className="flex flex-wrap gap-3">
            {site.edit_url && (
              <Link
                href={site.edit_url}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-forest-700 text-sm font-medium text-white hover:bg-brand-forest-800"
              >
                Open editor <ArrowRight className="w-4 h-4" />
              </Link>
            )}
            {!site.is_published && (
              <button
                type="button"
                onClick={() => publish.mutate()}
                disabled={publish.isPending}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-teal-600 text-sm font-semibold text-white hover:bg-brand-teal-700 disabled:opacity-50"
              >
                {publish.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <QrCode className="w-4 h-4" />
                )}
                Publish & get QR
              </button>
            )}
          </div>
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Use Membership &amp; Rewards for a public memberships page and loyalty offers.
      </p>
    </div>
  )
}
