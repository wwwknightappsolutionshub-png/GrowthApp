import Link from 'next/link'
import { CheckCircle } from 'lucide-react'
import type { Metadata } from 'next'
import { canonical, DEFAULT_OG_IMAGE } from '@/lib/seo'

export const metadata: Metadata = {
  title: 'Pricing — Honest, Predictable Plans for UK Businesses',
  description:
    'CustomerFlowai pricing from £99/month. Starter, Growth and Pro plans with 14-day free trial. No setup fees, no long contracts. CRM, leads, bookings and review automation for UK SMBs.',
  keywords:
    'CustomerFlowai pricing, UK CRM pricing, SMB SaaS UK cost, lead generation software price, review automation pricing UK',
  openGraph: {
    title: 'CustomerFlowai Pricing — Plans from £99/month',
    description: '14-day free trial on every plan. Starter, Growth and Pro for UK businesses.',
    type: 'website',
    images: [DEFAULT_OG_IMAGE],
  },
  alternates: { canonical: canonical('/pricing') },
  robots: { index: true, follow: true },
}

const plans = [
  {
    name: 'Starter',
    price: 99,
    desc: 'Perfect for sole traders just getting started',
    features: ['1 location', '500 leads/month', '1,000 SMS/month', 'CRM pipeline', 'Quote & invoice', 'Review automation', '1 user', 'Email support'],
    cta: 'Start free trial',
    highlighted: false,
  },
  {
    name: 'Growth',
    price: 149,
    desc: 'For growing businesses ready to scale',
    features: ['3 locations', '2,000 leads/month', '5,000 SMS/month', 'Everything in Starter', 'Social media posting', 'Advanced automations', '5 users', 'Priority support'],
    cta: 'Start free trial',
    highlighted: true,
  },
  {
    name: 'Pro',
    price: 199,
    desc: 'For established businesses dominating their market',
    features: ['Unlimited locations', '10,000 leads/month', '20,000 SMS/month', 'Everything in Growth', 'AI content generation', 'White-label widget', '20 users', 'Dedicated support'],
    cta: 'Start free trial',
    highlighted: false,
  },
]

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="flex items-center justify-between px-6 py-4 border-b bg-white max-w-6xl mx-auto">
        <Link href="/" className="text-xl font-bold text-blue-600">CustomerFlow AI</Link>
        <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">Sign in</Link>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Simple, transparent pricing</h1>
          <p className="text-xl text-gray-500">No setup fees. No long contracts. Cancel anytime.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map(plan => (
            <div key={plan.name} className={`rounded-2xl border-2 p-8 ${plan.highlighted ? 'border-blue-600 bg-white shadow-xl relative' : 'border-gray-200 bg-white'}`}>
              {plan.highlighted && <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs px-4 py-1.5 rounded-full font-semibold">Most Popular</div>}
              <h2 className="text-xl font-bold text-gray-900">{plan.name}</h2>
              <p className="text-gray-500 text-sm mt-1 mb-6">{plan.desc}</p>
              <div className="flex items-end gap-1 mb-8">
                <span className="text-4xl font-bold text-gray-900">£{plan.price}</span>
                <span className="text-gray-500 mb-1">/month</span>
              </div>
              <Link href="/register" className={`block text-center py-3 rounded-xl font-semibold text-sm mb-8 ${plan.highlighted ? 'bg-blue-600 text-white hover:bg-blue-700' : 'border border-gray-300 text-gray-700 hover:bg-gray-50'}`}>
                {plan.cta}
              </Link>
              <ul className="space-y-3">
                {plan.features.map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                    <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-gray-400 mt-10">All plans include a 14-day free trial. VAT may apply. UK businesses only.</p>
      </div>
    </div>
  )
}
