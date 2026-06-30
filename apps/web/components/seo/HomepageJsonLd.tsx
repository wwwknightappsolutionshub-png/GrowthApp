import { SITE_URL } from '@/lib/seo'

const organization = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'CustomerFlowai',
  url: SITE_URL,
  logo: `${SITE_URL}/icons/icon.svg`,
  description:
    'AI operating system for UK businesses — lead generation, CRM, operations, invoicing and customer retention in one platform.',
  areaServed: { '@type': 'Country', name: 'United Kingdom' },
  contactPoint: {
    '@type': 'ContactPoint',
    contactType: 'customer support',
    email: 'hello@customerflowai.online',
    availableLanguage: 'English',
  },
}

const website = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'CustomerFlowai',
  url: SITE_URL,
  potentialAction: {
    '@type': 'SearchAction',
    target: `${SITE_URL}/blog?q={search_term_string}`,
    'query-input': 'required name=search_term_string',
  },
}

const software = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'CustomerFlowai',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
  offers: {
    '@type': 'Offer',
    price: '99',
    priceCurrency: 'GBP',
    priceValidUntil: '2027-12-31',
  },
  description:
    'All-in-one AI platform for UK SMBs: leads, CRM, bookings, invoicing, reviews and retention.',
}

export function HomepageJsonLd() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organization) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(website) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(software) }}
      />
    </>
  )
}
