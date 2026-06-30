import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { RESERVED_PUBLIC_SLUGS } from '@/lib/seo'

interface Props {
  params: { tenantSlug: string }
}

async function getTenantData(slug: string) {
  const API_URL = process.env.INTERNAL_API_URL
  if (!API_URL) return null
  try {
    const res = await fetch(`${API_URL}/api/v1/public/tenants/${slug}`, {
      next: { revalidate: 300 },
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  if (RESERVED_PUBLIC_SLUGS.has(params.tenantSlug.toLowerCase())) {
    return {}
  }
  const tenant = await getTenantData(params.tenantSlug)
  return {
    title: tenant ? `${tenant.name} — Get a Free Quote` : 'Get a Free Quote',
    description: tenant ? `Contact ${tenant.name} for professional ${tenant.business_type} services in ${tenant.city || 'your area'}.` : undefined,
  }
}

function LeadForm({ tenantSlug, tenantName }: { tenantSlug: string; tenantName: string }) {
  return (
    <form
      id="lead-form"
      action={`/api/v1/public/leads/${tenantSlug}`}
      method="post"
      className="space-y-4"
      onSubmit={undefined}
    >
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">First name *</label>
          <input name="first_name" required className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Last name</label>
          <input name="last_name" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Phone number *</label>
        <input name="phone" type="tel" required className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="07700 000000" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
        <input name="email" type="email" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="optional" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">What do you need help with? *</label>
        <input name="service_needed" required className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g. Leaking pipe, boiler service..." />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Your postcode *</label>
        <input name="postcode" required className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="SW1A 1AA" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Message (optional)</label>
        <textarea name="message" rows={3} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Any extra details..." />
      </div>
      <input type="hidden" name="source" value="landing_page" />
      <button
        type="submit"
        className="w-full bg-blue-600 text-white rounded-lg py-3 text-sm font-semibold hover:bg-blue-700 transition-colors shadow-sm"
      >
        Get My Free Quote
      </button>
      <p className="text-xs text-gray-400 text-center">We'll call you back within 1 hour. No spam — ever.</p>
    </form>
  )
}

export default async function TenantLandingPage({ params }: Props) {
  if (RESERVED_PUBLIC_SLUGS.has(params.tenantSlug.toLowerCase())) {
    notFound()
  }

  const tenant = await getTenantData(params.tenantSlug)

  if (!tenant) {
    notFound()
  }

  const primaryColor = tenant.primary_color || '#2563EB'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {tenant.logo_url && (
              <img src={tenant.logo_url} alt={tenant.name} className="h-10 w-auto object-contain" />
            )}
            <div>
              <h1 className="font-bold text-gray-900 text-lg">{tenant.name}</h1>
              {tenant.city && <p className="text-xs text-gray-500">{tenant.city}</p>}
            </div>
          </div>
          {tenant.phone && (
            <a href={`tel:${tenant.phone}`} className="text-sm font-semibold text-blue-600 hover:underline">
              {tenant.phone}
            </a>
          )}
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 py-12 grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 leading-tight mb-4">
            Professional {tenant.business_type} services{tenant.city ? ` in ${tenant.city}` : ''}
          </h2>
          <p className="text-gray-500 mb-6 leading-relaxed">
            Get a free, no-obligation quote today. We respond within 1 hour.
          </p>

          {/* Trust signals */}
          <div className="space-y-3">
            {['Fast response — we call you back within 1 hour', 'Fully insured and professionally trained', 'No hidden fees — transparent pricing', 'Locally based — serving your area'].map(point => (
              <div key={point} className="flex items-center gap-2.5 text-sm text-gray-700">
                <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                  <svg className="w-3 h-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                {point}
              </div>
            ))}
          </div>
        </div>

        {/* Lead Form */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-7">
          <h3 className="text-xl font-bold text-gray-900 mb-5">Get your free quote</h3>
          <LeadForm tenantSlug={params.tenantSlug} tenantName={tenant.name} />
        </div>
      </section>

      <footer className="text-center py-8 text-xs text-gray-400 border-t border-gray-200 bg-white mt-10">
        © {new Date().getFullYear()} {tenant.name}. All rights reserved.
        {tenant.city && ` • ${tenant.city}, UK`}
      </footer>

      {/* JSON-LD structured data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'LocalBusiness',
            name: tenant.name,
            telephone: tenant.phone,
            address: tenant.city ? { '@type': 'PostalAddress', addressLocality: tenant.city, addressCountry: 'GB' } : undefined,
            url: tenant.website_url,
          }),
        }}
      />
    </div>
  )
}
