'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import {
  ArrowRight,
  Briefcase,
  Building2,
  ChevronRight,
  Facebook,
  Instagram,
  Linkedin,
  Plus,
  Search,
  Trash2,
  Youtube,
} from 'lucide-react'
import { freelancerClients } from '@/lib/api-client'
import { useActiveClient } from '@/lib/freelancer-context'

interface ClientRow {
  id: string
  slug: string
  name: string
  business_type: string | null
  postcode: string | null
  email: string | null
  phone: string | null
  website_url: string | null
  is_active: boolean
  social_handles: Record<string, string>
  created_at: string
  updated_at: string
}

export default function FreelancerClientsPage() {
  const router = useRouter()
  const qc = useQueryClient()
  const { activeId, setActiveId } = useActiveClient()
  const [query, setQuery] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const list = useQuery<ClientRow[]>({
    queryKey: ['freelancer-clients'],
    queryFn: () => freelancerClients.list().then((r) => r.data as ClientRow[]),
  })

  const remove = useMutation({
    mutationFn: (id: string) => freelancerClients.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['freelancer-clients'] })
      toast.success('Client deactivated.')
    },
    onError: () => toast.error('Could not deactivate.'),
  })

  const filtered = (list.data ?? []).filter((c) =>
    c.name.toLowerCase().includes(query.toLowerCase()),
  )

  const openClient = (id: string) => {
    setActiveId(id)
    router.push(`/dashboard/clients/${id}`)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">
            Your Clients
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage every client you service. Switch into any client to run their CRM, social,
            automations and analytics independently.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-2 rounded-md bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground hover:bg-brand-forest-800"
        >
          <Plus className="h-4 w-4" />
          Add client
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search clients…"
          className="h-10 w-full rounded-md border border-input bg-background pl-10 pr-3 text-sm"
        />
      </div>

      {list.isLoading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-6 h-6 border-4 border-primary border-t-transparent rounded-full" />
        </div>
      )}

      {!list.isLoading && filtered.length === 0 && (
        <div className="rounded-xl border border-dashed border-border bg-card/40 p-10 text-center">
          <Briefcase className="mx-auto h-10 w-10 text-muted-foreground/60" />
          <h3 className="mt-3 text-lg font-semibold text-foreground">No clients yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Add your first client to start running campaigns, automations and analytics on their
            behalf.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground hover:bg-brand-forest-800"
          >
            <Plus className="h-4 w-4" />
            Add your first client
          </button>
        </div>
      )}

      {filtered.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {filtered.map((c) => {
            const isActive = activeId === c.id
            const handles = c.social_handles || {}
            return (
              <div
                key={c.id}
                className={`rounded-xl border p-4 hover:shadow-md transition-shadow ${
                  isActive ? 'border-brand-forest-500 bg-brand-forest-50/40' : 'border-border bg-card'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="rounded-md bg-brand-forest-100 p-2 text-brand-forest-700">
                      <Building2 className="h-4 w-4" />
                    </div>
                    <div>
                      <Link
                        href={`/dashboard/clients/${c.id}`}
                        onClick={() => setActiveId(c.id)}
                        className="font-semibold text-foreground hover:underline"
                      >
                        {c.name}
                      </Link>
                      <p className="text-xs text-muted-foreground capitalize">
                        {c.business_type ?? 'general'}
                      </p>
                    </div>
                  </div>
                  {isActive && (
                    <span className="rounded-full bg-brand-forest-700 px-2 py-0.5 text-[9px] font-semibold uppercase text-brand-forest-foreground">
                      Active
                    </span>
                  )}
                </div>

                <div className="mt-3 flex items-center gap-2">
                  {handles.instagram && (
                    <span className="text-pink-500" title={`@${handles.instagram}`}>
                      <Instagram className="h-3.5 w-3.5" />
                    </span>
                  )}
                  {handles.facebook && (
                    <span className="text-blue-600" title={handles.facebook}>
                      <Facebook className="h-3.5 w-3.5" />
                    </span>
                  )}
                  {handles.linkedin && (
                    <span className="text-sky-700" title={handles.linkedin}>
                      <Linkedin className="h-3.5 w-3.5" />
                    </span>
                  )}
                  {handles.youtube && (
                    <span className="text-red-600" title={handles.youtube}>
                      <Youtube className="h-3.5 w-3.5" />
                    </span>
                  )}
                  {Object.keys(handles).length === 0 && (
                    <span className="text-[10px] uppercase tracking-widest text-muted-foreground/70">
                      No socials linked
                    </span>
                  )}
                </div>

                <div className="mt-4 flex items-center gap-2">
                  <button
                    onClick={() => openClient(c.id)}
                    className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-md bg-brand-forest-700 px-3 py-1.5 text-xs font-semibold text-brand-forest-foreground hover:bg-brand-forest-800"
                  >
                    Open <ArrowRight className="h-3 w-3" />
                  </button>
                  <button
                    onClick={() => {
                      if (window.confirm(`Deactivate ${c.name}? Data is preserved.`)) {
                        remove.mutate(c.id)
                      }
                    }}
                    className="inline-flex items-center justify-center rounded-md border border-input p-1.5 text-muted-foreground hover:bg-muted hover:text-destructive"
                    title="Deactivate"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showCreate && (
        <CreateClientModal
          onClose={() => setShowCreate(false)}
          onCreated={(id) => {
            qc.invalidateQueries({ queryKey: ['freelancer-clients'] })
            setActiveId(id)
            setShowCreate(false)
            router.push(`/dashboard/clients/${id}`)
          }}
        />
      )}
    </div>
  )
}


function CreateClientModal({
  onClose,
  onCreated,
}: {
  onClose: () => void
  onCreated: (id: string) => void
}) {
  const [name, setName] = useState('')
  const [contactName, setContactName] = useState('')
  const [businessType, setBusinessType] = useState('other')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [website, setWebsite] = useState('')
  const [postcode, setPostcode] = useState('')
  const [instagram, setInstagram] = useState('')
  const [facebook, setFacebook] = useState('')
  const [tiktok, setTiktok] = useState('')
  const [twitter, setTwitter] = useState('')
  const [linkedin, setLinkedin] = useState('')
  const [googleBusiness, setGoogleBusiness] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async () => {
    if (!name.trim()) {
      toast.error('Enter a client name')
      return
    }
    setSubmitting(true)
    try {
      const res = await freelancerClients.create({
        name,
        contact_name: contactName || null,
        business_type: businessType,
        postcode: postcode || null,
        email: email || null,
        phone: phone || null,
        website_url: website || null,
        social_handles: {
          instagram: instagram || null,
          facebook: facebook || null,
          tiktok: tiktok || null,
          twitter: twitter || null,
          linkedin: linkedin || null,
          google_business: googleBusiness || null,
        },
      })
      toast.success(`${name} added to your portfolio.`)
      onCreated(res.data.id)
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to create client')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-xl border border-border bg-background p-6 shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Add a new client</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            ✕
          </button>
        </div>

        <div className="space-y-3">
          <FieldRow label="Client / business name" required>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              placeholder="e.g. Smith Plumbing Ltd"
            />
          </FieldRow>
          <FieldRow label="Contact Name">
            <input
              value={contactName}
              onChange={(e) => setContactName(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              placeholder="e.g. Jane Smith"
            />
          </FieldRow>
          <div className="grid grid-cols-2 gap-3">
            <FieldRow label="Industry / trade">
              <select
                value={businessType}
                onChange={(e) => setBusinessType(e.target.value)}
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              >
                {[
                  'salon',
                  'plumber',
                  'electrician',
                  'cleaner',
                  'roofer',
                  'painter',
                  'builder',
                  'landscaper',
                  'handyman',
                  'hvac',
                  'locksmith',
                  'restaurant',
                  'cafe',
                  'gym',
                  'consultancy',
                  'ecommerce',
                  'other',
                ].map((bt) => (
                  <option key={bt} value={bt} className="capitalize">
                    {bt}
                  </option>
                ))}
              </select>
            </FieldRow>
            <FieldRow label="Postcode">
              <input
                value={postcode}
                onChange={(e) => setPostcode(e.target.value.toUpperCase())}
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm uppercase"
                placeholder="SW1A 1AA"
              />
            </FieldRow>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <FieldRow label="Client email">
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                placeholder="contact@client.com"
              />
            </FieldRow>
            <FieldRow label="Client phone">
              <input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                type="tel"
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                placeholder="07700 000000"
              />
            </FieldRow>
          </div>
          <FieldRow label="Website">
            <input
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              type="url"
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              placeholder="https://"
            />
          </FieldRow>

          <div className="border-t border-border pt-3 mt-2">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">
              Social media pages
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <FieldRow label="Instagram handle">
                <input
                  value={instagram}
                  onChange={(e) => setInstagram(e.target.value.replace(/^@/, ''))}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  placeholder="username"
                />
              </FieldRow>
              <FieldRow label="Facebook page">
                <input
                  value={facebook}
                  onChange={(e) => setFacebook(e.target.value)}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  placeholder="page name or URL"
                />
              </FieldRow>
              <FieldRow label="TikTok handle">
                <input
                  value={tiktok}
                  onChange={(e) => setTiktok(e.target.value.replace(/^@/, ''))}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  placeholder="username"
                />
              </FieldRow>
              <FieldRow label="X / Twitter">
                <input
                  value={twitter}
                  onChange={(e) => setTwitter(e.target.value.replace(/^@/, ''))}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  placeholder="username"
                />
              </FieldRow>
              <FieldRow label="LinkedIn page">
                <input
                  value={linkedin}
                  onChange={(e) => setLinkedin(e.target.value)}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  placeholder="company URL"
                />
              </FieldRow>
              <FieldRow label="Google My Business page">
                <input
                  value={googleBusiness}
                  onChange={(e) => setGoogleBusiness(e.target.value)}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  placeholder="Google Business Profile URL"
                />
              </FieldRow>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 mt-5 pt-4 border-t border-border">
          <button onClick={onClose} className="text-sm text-muted-foreground hover:text-foreground">
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={submitting}
            className="inline-flex items-center gap-2 rounded-md bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground hover:bg-brand-forest-800 disabled:opacity-60"
          >
            {submitting ? 'Creating…' : 'Create client'}
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

function FieldRow({
  label,
  required,
  children,
}: {
  label: string
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div>
      <label className="mb-1 block text-[10px] uppercase tracking-widest font-semibold text-muted-foreground">
        {label}
        {required && <span className="ml-0.5 text-destructive">*</span>}
      </label>
      {children}
    </div>
  )
}
