'use client'

import { useEffect } from 'react'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { toast } from 'sonner'
import {
  ArrowLeft,
  BadgePoundSterling,
  Bot,
  Calendar,
  Globe,
  Mail,
  Megaphone,
  MessageSquare,
  PhoneCall,
  Radar,
  Save,
  Sparkles,
  Star,
  Target,
  TrendingUp,
  Upload,
  Users,
  Zap,
  PieChart,
  GitBranch,
  Palette,
} from 'lucide-react'
import { useState } from 'react'
import { freelancerClients } from '@/lib/api-client'
import { useActiveClient } from '@/lib/freelancer-context'

interface ClientDetail {
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
}

interface ToolTile {
  href: string
  label: string
  description: string
  icon: React.ComponentType<{ className?: string }>
}

const TOOL_TILES: ToolTile[] = [
  {
    href: '/dashboard/leads',
    label: 'Leads',
    description: 'Capture and score enquiries',
    icon: Target,
  },
  {
    href: '/dashboard/crm',
    label: 'CRM',
    description: 'Manage their customer database',
    icon: Users,
  },
  {
    href: '/dashboard/bookings',
    label: 'Bookings',
    description: 'Their appointments and jobs',
    icon: Calendar,
  },
  {
    href: '/dashboard/money',
    label: 'Money',
    description: 'Revenue + cash flow',
    icon: BadgePoundSterling,
  },
  {
    href: '/dashboard/messages',
    label: 'Messages',
    description: 'Unified inbox',
    icon: MessageSquare,
  },
  {
    href: '/dashboard/whatsapp',
    label: 'WhatsApp',
    description: 'Two-way WhatsApp',
    icon: PhoneCall,
  },
  {
    href: '/dashboard/outreach',
    label: 'Outreach',
    description: 'Broadcast campaigns',
    icon: Megaphone,
  },
  {
    href: '/dashboard/ai-social/drafts',
    label: 'AI Social Posts',
    description: 'Generate + publish posts',
    icon: Sparkles,
  },
  {
    href: '/dashboard/ai-social/brand-identity',
    label: 'Brand Identity',
    description: 'Colours, tone, logo',
    icon: Palette,
  },
  {
    href: '/dashboard/ai-social/calendar',
    label: 'Social Calendar',
    description: 'Scheduled posts',
    icon: Calendar,
  },
  {
    href: '/dashboard/landing-pages',
    label: 'Landing Pages',
    description: 'AI-generated pages',
    icon: Globe,
  },
  {
    href: '/dashboard/automations',
    label: 'Automations',
    description: 'Trigger-based workflows',
    icon: Zap,
  },
  {
    href: '/dashboard/reviews',
    label: 'Reviews',
    description: 'Request + reply',
    icon: Star,
  },
  {
    href: '/dashboard/membership-rewards',
    label: 'Membership & Rewards',
    description: 'Loyalty points and memberships',
    icon: TrendingUp,
  },
  {
    href: '/dashboard/marketer/audience',
    label: 'Audience Research',
    description: 'Demographics + insights',
    icon: PieChart,
  },
  {
    href: '/dashboard/marketer/competitor',
    label: 'Competitor Scanner',
    description: 'Spy on competitor sites',
    icon: Radar,
  },
  {
    href: '/dashboard/marketer/funnel',
    label: 'Funnel Builder',
    description: '5-stage funnels',
    icon: GitBranch,
  },
  {
    href: '/dashboard/assistant',
    label: 'AI Assistant',
    description: 'Chat for instant answers',
    icon: Bot,
  },
]

export default function ClientDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const qc = useQueryClient()
  const { setActiveId } = useActiveClient()
  const id = params.id

  const client = useQuery<ClientDetail>({
    queryKey: ['freelancer-client', id],
    queryFn: () => freelancerClients.get(id).then((r) => r.data as ClientDetail),
    enabled: !!id,
  })

  useEffect(() => {
    if (id) setActiveId(id)
  }, [id, setActiveId])

  if (client.isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  if (client.isError || !client.data) {
    return (
      <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-6 text-sm">
        Client not found in your portfolio.{' '}
        <Link href="/dashboard/clients" className="underline">
          Back to clients
        </Link>
      </div>
    )
  }

  const c = client.data
  const handles = c.social_handles || {}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link
          href="/dashboard/clients"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" /> All clients
        </Link>
        <div className="mt-1 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">
              {c.name}
            </h1>
            <p className="mt-0.5 text-sm text-muted-foreground capitalize">
              {c.business_type ?? 'general'}
              {c.postcode && <> &middot; {c.postcode}</>}
            </p>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full bg-brand-forest-700 px-3 py-1 text-xs font-semibold text-brand-forest-foreground">
            <Sparkles className="h-3 w-3" />
            Active client context
          </span>
        </div>
      </div>

      {/* Contact + socials card */}
      <ClientProfileCard client={c} />

      {/* Tools grid */}
      <div>
        <h2 className="font-display text-lg font-semibold tracking-tight text-foreground mb-3">
          Tools for {c.name.split(' ')[0]}
        </h2>
        <p className="text-xs text-muted-foreground mb-3">
          Every tool below operates inside <strong>{c.name}</strong>&apos;s workspace. Selections,
          posts, customer records and automations created here belong to this client only.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {TOOL_TILES.map((t) => {
            const Icon = t.icon
            return (
              <Link
                key={t.href}
                href={t.href}
                className="group rounded-lg border border-border bg-card p-3 hover:border-brand-forest-400 hover:shadow-sm transition-all"
              >
                <div className="rounded-md bg-brand-forest-100 p-2 w-fit text-brand-forest-700 group-hover:bg-brand-forest-200 transition-colors">
                  <Icon className="h-4 w-4" />
                </div>
                <h3 className="mt-2 text-sm font-semibold text-foreground">{t.label}</h3>
                <p className="text-[11px] text-muted-foreground leading-snug mt-0.5">
                  {t.description}
                </p>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Reports placeholder */}
      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="font-display text-lg font-semibold tracking-tight text-foreground mb-1 flex items-center gap-2">
          <Upload className="h-4 w-4 text-brand-forest-600" />
          Generate report
        </h2>
        <p className="text-xs text-muted-foreground mb-3">
          Pull a snapshot of {c.name}&apos;s month in one click — leads, posts, revenue, automations.
        </p>
        <div className="flex flex-wrap gap-2">
          {['Monthly summary', 'Social performance', 'Lead funnel', 'Revenue & cash flow'].map(
            (kind) => (
              <button
                key={kind}
                onClick={() => toast.info(`${kind} report queued for ${c.name}`)}
                className="rounded-md border border-input bg-background px-3 py-1.5 text-xs hover:bg-muted"
              >
                {kind}
              </button>
            ),
          )}
        </div>
      </div>
    </div>
  )
}


function ClientProfileCard({ client }: { client: ClientDetail }) {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<ClientDetail>(client)

  useEffect(() => {
    setDraft(client)
  }, [client])

  const save = useMutation({
    mutationFn: () =>
      freelancerClients.update(client.id, {
        name: draft.name,
        business_type: draft.business_type,
        postcode: draft.postcode,
        email: draft.email,
        phone: draft.phone,
        website_url: draft.website_url,
        social_handles: draft.social_handles,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['freelancer-client', client.id] })
      qc.invalidateQueries({ queryKey: ['freelancer-clients'] })
      toast.success('Client updated.')
      setEditing(false)
    },
    onError: () => toast.error('Could not update.'),
  })

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Profile & social pages
        </h2>
        {!editing ? (
          <button
            onClick={() => setEditing(true)}
            className="text-xs text-brand-teal-700 hover:underline"
          >
            Edit
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setDraft(client)
                setEditing(false)
              }}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Cancel
            </button>
            <button
              onClick={() => save.mutate()}
              disabled={save.isPending}
              className="inline-flex items-center gap-1 rounded-md bg-brand-forest-700 px-3 py-1 text-xs font-semibold text-brand-forest-foreground hover:bg-brand-forest-800"
            >
              <Save className="h-3 w-3" />
              {save.isPending ? 'Saving…' : 'Save'}
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h3 className="text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
            Contact
          </h3>
          <Row
            label="Email"
            value={draft.email}
            editing={editing}
            onChange={(v) => setDraft({ ...draft, email: v })}
            placeholder="contact@client.com"
          />
          <Row
            label="Phone"
            value={draft.phone}
            editing={editing}
            onChange={(v) => setDraft({ ...draft, phone: v })}
            placeholder="07700 000000"
          />
          <Row
            label="Website"
            value={draft.website_url}
            editing={editing}
            onChange={(v) => setDraft({ ...draft, website_url: v })}
            placeholder="https://"
          />
        </div>
        <div>
          <h3 className="text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
            Social pages
          </h3>
          {(['instagram', 'facebook', 'tiktok', 'twitter', 'linkedin', 'youtube'] as const).map(
            (k) => (
              <Row
                key={k}
                label={k.charAt(0).toUpperCase() + k.slice(1)}
                value={draft.social_handles?.[k] ?? null}
                editing={editing}
                onChange={(v) =>
                  setDraft({
                    ...draft,
                    social_handles: { ...draft.social_handles, [k]: v ?? '' },
                  })
                }
                placeholder={k === 'facebook' ? 'page URL' : 'username'}
              />
            ),
          )}
        </div>
      </div>
    </div>
  )
}

function Row({
  label,
  value,
  editing,
  onChange,
  placeholder,
}: {
  label: string
  value: string | null
  editing: boolean
  onChange: (v: string | null) => void
  placeholder?: string
}) {
  return (
    <div className="flex items-center gap-3 py-1.5 border-b border-border/50 last:border-b-0">
      <span className="w-20 text-xs text-muted-foreground">{label}</span>
      {editing ? (
        <input
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value || null)}
          placeholder={placeholder}
          className="flex-1 h-8 rounded border border-input bg-background px-2 text-sm"
        />
      ) : (
        <span className="flex-1 text-sm text-foreground">
          {value || <span className="text-muted-foreground/60">—</span>}
        </span>
      )}
    </div>
  )
}
