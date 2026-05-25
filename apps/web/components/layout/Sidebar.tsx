'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { BrandIcon, BrandMark } from '@/components/brand/BrandMark'
import {
  LayoutDashboard,
  Users,
  Calendar,
  CalendarDays,
  CalendarRange,
  FileText,
  Settings,
  MessageSquare,
  Star,
  Share2,
  CreditCard,
  Zap,
  Target,
  LogOut,
  ChevronLeft,
  ChevronDown,
  ListTodo,
  Sparkles,
  PoundSterling,
  Megaphone,
  Search as SearchIcon,
  Inbox,
  Globe,
  TrendingUp,
  PhoneCall,
  Palette,
  Upload,
  GitBranch,
  Radar,
  Gauge,
  MessageCircle,
  BellRing,
  Briefcase,
  Link2,
  Package,
  Gift,
  type LucideIcon,
} from 'lucide-react'
import { logout as doLogout } from '@/lib/auth'
import { auth, freelancerClients, tenants } from '@/lib/api-client'

// AI Social and Marketer tools — universal, shown for every business category
const AI_SOCIAL_HREFS = [
  '/dashboard/ai-social/brand-identity',
  '/dashboard/ai-social/samples',
  '/dashboard/ai-social/preferences',
  '/dashboard/ai-social/drafts',
  '/dashboard/ai-social/approval',
  '/dashboard/ai-social/calendar',
]
const MARKETER_HREFS = [
  '/dashboard/marketer/funnel',
  '/dashboard/marketer/audience',
  '/dashboard/marketer/competitor',
  '/dashboard/marketer/quota',
]

const ALL_HREFS = [
  '/dashboard', '/dashboard/assistant', '/dashboard/leads', '/dashboard/crm',
  '/dashboard/tasks', '/dashboard/bookings', '/dashboard/quotes', '/dashboard/invoices',
  '/dashboard/accounts',
  '/dashboard/addons', '/dashboard/addons/booking', '/dashboard/addons/billing', '/dashboard/addons/crm',
  '/dashboard/money', '/dashboard/messages', '/dashboard/whatsapp', '/dashboard/auto-replies',
  '/dashboard/outreach', '/dashboard/site-builder', '/dashboard/ads', '/dashboard/seo',
  '/dashboard/automations', '/dashboard/reviews', '/dashboard/integrations', '/dashboard/membership-rewards', '/dashboard/notifications', '/dashboard/settings',
  ...AI_SOCIAL_HREFS, ...MARKETER_HREFS,
]

// ── Default enabled-tool sets (fallback when API unavailable) ─────────────────
// Mirrors CATEGORY_DEFAULTS in apps/api/app/modules/admin/tool_config.py exactly.
const CATEGORY_DEFAULTS: Record<string, string[]> = {
  tradesman: [
    '/dashboard', '/dashboard/leads', '/dashboard/crm',
    '/dashboard/tasks', '/dashboard/bookings', '/dashboard/quotes',
    '/dashboard/invoices', '/dashboard/accounts',
    '/dashboard/messages', '/dashboard/whatsapp', '/dashboard/auto-replies',
    '/dashboard/reviews', '/dashboard/integrations', '/dashboard/membership-rewards',
    '/dashboard/site-builder', '/dashboard/outreach', '/dashboard/automations',
    ...AI_SOCIAL_HREFS, ...MARKETER_HREFS,
    '/dashboard/notifications',
    '/dashboard/settings',
  ],
  salon_beauty: [
    '/dashboard', '/dashboard/leads', '/dashboard/crm',
    '/dashboard/tasks', '/dashboard/bookings', '/dashboard/invoices', '/dashboard/accounts',
    '/dashboard/addons', '/dashboard/addons/booking', '/dashboard/addons/billing', '/dashboard/addons/crm',
    '/dashboard/messages', '/dashboard/whatsapp', '/dashboard/auto-replies',
    '/dashboard/outreach', '/dashboard/reviews', '/dashboard/integrations', '/dashboard/membership-rewards',
    '/dashboard/automations',
    ...AI_SOCIAL_HREFS, ...MARKETER_HREFS,
    '/dashboard/notifications',
    '/dashboard/settings',
  ],
  healthcare: [
    '/dashboard', '/dashboard/leads', '/dashboard/crm',
    '/dashboard/tasks', '/dashboard/bookings', '/dashboard/invoices', '/dashboard/accounts',
    '/dashboard/messages', '/dashboard/auto-replies',
    '/dashboard/reviews', '/dashboard/integrations', '/dashboard/membership-rewards',
    '/dashboard/automations',
    ...AI_SOCIAL_HREFS, ...MARKETER_HREFS,
    '/dashboard/notifications',
    '/dashboard/settings',
  ],
  restaurant_food: [
    '/dashboard', '/dashboard/leads', '/dashboard/crm',
    '/dashboard/tasks', '/dashboard/bookings', '/dashboard/accounts',
    '/dashboard/messages', '/dashboard/whatsapp', '/dashboard/auto-replies',
    '/dashboard/outreach', '/dashboard/reviews', '/dashboard/integrations', '/dashboard/membership-rewards',
    '/dashboard/ads', '/dashboard/seo',
    '/dashboard/automations',
    ...AI_SOCIAL_HREFS, ...MARKETER_HREFS,
    '/dashboard/notifications',
    '/dashboard/settings',
  ],
  retail: [
    '/dashboard', '/dashboard/leads', '/dashboard/crm',
    '/dashboard/tasks', '/dashboard/accounts',
    '/dashboard/messages', '/dashboard/whatsapp', '/dashboard/auto-replies',
    '/dashboard/outreach', '/dashboard/reviews', '/dashboard/integrations', '/dashboard/membership-rewards',
    '/dashboard/ads', '/dashboard/seo',
    '/dashboard/automations',
    ...AI_SOCIAL_HREFS, ...MARKETER_HREFS,
    '/dashboard/notifications',
    '/dashboard/settings',
  ],
  fitness_wellness: [
    '/dashboard', '/dashboard/leads', '/dashboard/crm',
    '/dashboard/tasks', '/dashboard/bookings', '/dashboard/invoices', '/dashboard/accounts',
    '/dashboard/messages', '/dashboard/whatsapp', '/dashboard/auto-replies',
    '/dashboard/outreach', '/dashboard/reviews', '/dashboard/integrations', '/dashboard/membership-rewards',
    '/dashboard/automations',
    ...AI_SOCIAL_HREFS, ...MARKETER_HREFS,
    '/dashboard/notifications',
    '/dashboard/settings',
  ],
  professional_services: ALL_HREFS,
  general: ALL_HREFS,
}

// ── Client-side business-type → category classifier ───────────────────────────
// Mirrors classifyBusiness_py in tool_config.py — used when API hasn't loaded yet.
const BIZ_PATTERNS: [string, RegExp][] = [
  ['tradesman', /plumb|electri|carpent|builder|roofer|painter|glazier|locksmith|hvac|plaster|trades|handyman|gas|heating|boiler|joiner|tiler|flooring|landscap|garden|cleaner|cleaning|window.?clean|pressure.?wash|pest.?control|drain|remov|fencing|paving|bricklay|plasterer|decorator/i],
  ['salon_beauty', /salon|beauty|hair|nail|spa|barber|makeup|aesthet|lash|brow|wax|tanning|tattoo|piercing|cosmetic|skin.?care|massage|holistic/i],
  ['healthcare', /clinic|doctor|gp|dentist|physio|health|medic|therap|chiro|optom|nurse|pharma|dental|hospital|osteopath|podiat|audiolog|psychology|counsell|acupunctur|vet|care.?home/i],
  ['restaurant_food', /restaurant|café|cafe|food|takeaway|catering|baker|bistro|pub|diner|kitchen|pizza|burger|sushi|curry|kebab|chippy|fish.?chip|sandwich|deli|coffee|canteen/i],
  ['retail', /shop|retail|boutique|store|fashion|clothing|jewel|florist|gift|market|newsagent|off.?licence|pet.?shop|toy|book.?shop|hardware|diy|antique/i],
  ['fitness_wellness', /gym|fitness|yoga|pilates|personal.?train|sport|wellness|coach|crossfit|martial|dance|swim|tennis|golf|boxing|running|cycling|bootcamp/i],
  ['professional_services', /account|solicitor|architect|consult|lawyer|finance|advisor|agent|pr |design|market|recruit|insurance|mortgage|estate.?agent|letting|surveyor|it.?support|web.?develop|software|media|photograp|videograph|translat|event|wedding/i],
]

function classifyBusiness(businessType: string): string {
  const bt = businessType.toLowerCase()
  for (const [cat, pattern] of BIZ_PATTERNS) {
    if (pattern.test(bt)) return cat
  }
  return 'general'
}

// ── Nav item definition ───────────────────────────────────────────────────────
type NavGroup = 'overview' | 'pipeline' | 'engage' | 'grow' | 'ai_social' | 'marketer' | 'system'

type NavItem = {
  href: string
  label: string
  description: string
  icon: LucideIcon
  group: NavGroup
  exact?: boolean
}

const navItems: NavItem[] = [
  // ── Overview ──────────────────────────────────────────────────────────────
  {
    href: '/dashboard',
    label: 'Dashboard',
    description: 'Your daily snapshot — revenue, tasks, and live alerts',
    icon: LayoutDashboard,
    group: 'overview',
    exact: true,
  },
  { href: '/dashboard/clients', label: 'Clients', description: 'Your managed clients — switch context to work inside any of them', icon: Briefcase, group: 'overview' },
  { href: '/dashboard/assistant', label: 'AI Assistant', description: 'Chat with your AI business co-pilot for instant answers and drafts', icon: Sparkles, group: 'overview' },

  // ── Pipeline ──────────────────────────────────────────────────────────────
  { href: '/dashboard/leads',    label: 'Leads',    description: 'Incoming enquiries from your forms, ads, and Refer & Win',          icon: Target,         group: 'pipeline' },
  { href: '/dashboard/crm',      label: 'CRM',      description: 'Manage customers, track visits, deals, and follow-ups',             icon: Users,          group: 'pipeline' },
  { href: '/dashboard/tasks',    label: 'Tasks',    description: 'Personal and team task board to stay on top of your workload',       icon: ListTodo,       group: 'pipeline' },
  { href: '/dashboard/bookings', label: 'Bookings', description: 'Schedule and manage appointments, jobs, and consultations',          icon: Calendar,       group: 'pipeline' },
  { href: '/dashboard/quotes',   label: 'Quotes',   description: 'Create, send, and track professional price quotes',                  icon: FileText,       group: 'pipeline' },
  { href: '/dashboard/invoices', label: 'Invoices', description: 'Issue invoices, record payments, and track outstanding balances',    icon: CreditCard,     group: 'pipeline' },
  { href: '/dashboard/accounts', label: 'Accounts', description: 'Cash in, pending, collections, and business reporting',              icon: PoundSterling,  group: 'pipeline' },
  { href: '/dashboard/addons', label: 'Industry Add-ons', description: 'Salon or garage premium booking, billing, and CRM tools',           icon: Package,        group: 'pipeline' },
  { href: '/dashboard/addons/booking', label: 'Industry Booking', description: 'Multi-service scheduling, bays, parts checks, gap-fill',            icon: Calendar,     group: 'pipeline' },
  { href: '/dashboard/addons/billing', label: 'Industry Billing', description: 'Tips, memberships, VIN invoices, parts markup, warranties',         icon: CreditCard,   group: 'pipeline' },
  { href: '/dashboard/addons/crm', label: 'Industry CRM', description: 'Stylist notes, vehicle history, maintenance alerts, CLV scores',      icon: Users,        group: 'pipeline' },

  // ── Engagement ────────────────────────────────────────────────────────────
  { href: '/dashboard/messages',     label: 'Messages',    description: 'SMS and email conversations with customers in one inbox',               icon: MessageSquare, group: 'engage' },
  { href: '/dashboard/whatsapp',     label: 'WhatsApp',    description: 'Two-way WhatsApp conversations and AI-suggested replies',                icon: PhoneCall,     group: 'engage' },
  { href: '/dashboard/auto-replies', label: 'AI Replies',  description: 'AI-drafted responses to reviews and messages for your approval',        icon: Inbox,         group: 'engage' },
  { href: '/dashboard/outreach',     label: 'Outreach',    description: 'Broadcast campaigns, win-back sequences, and drip automations',          icon: Megaphone,     group: 'engage' },

  // ── Growth ────────────────────────────────────────────────────────────────
  { href: '/dashboard/site-builder', label: 'Business Page', description: 'Your branded lead page, subdomain URL, and QR code',                         icon: Globe,        group: 'grow' },
  { href: '/dashboard/ads',           label: 'Ads',           description: 'AI-written ad copy for Google, Facebook, and Instagram campaigns',           icon: Megaphone,    group: 'grow' },
  { href: '/dashboard/seo',           label: 'SEO',           description: 'On-page SEO audit and recommendations to rank higher locally',               icon: SearchIcon,   group: 'grow' },
  { href: '/dashboard/automations',   label: 'Automations',   description: 'Trigger-based workflows — follow-ups, reminders, and nurture sequences',     icon: Zap,          group: 'grow' },
  { href: '/dashboard/reviews',       label: 'Reviews',       description: 'Request, monitor, and respond to Google reviews automatically',              icon: Star,         group: 'grow' },
  { href: '/dashboard/integrations',  label: 'Integrations',  description: 'Connect Google Business Profile and other channels',                       icon: Link2,        group: 'grow' },
  { href: '/dashboard/membership-rewards', label: 'Membership & Rewards', description: 'Membership plans, loyalty points, tiers, and public memberships page', icon: Gift,        group: 'grow' },

  // ── AI Social ─────────────────────────────────────────────────────────────
  { href: '/dashboard/ai-social/brand-identity', label: 'Brand Identity',     description: 'Set your colours, fonts, tone, and logo for AI-generated posts',     icon: Palette,        group: 'ai_social' },
  { href: '/dashboard/ai-social/samples',        label: 'Upload Samples',     description: 'Upload reference posts so the AI learns your style',                  icon: Upload,         group: 'ai_social' },
  { href: '/dashboard/ai-social/preferences',    label: 'Posting Preferences',description: 'How often, which days, and what time the AI should publish',          icon: CalendarRange,  group: 'ai_social' },
  { href: '/dashboard/ai-social/drafts',         label: 'Draft Review',       description: 'Review AI-generated drafts and send them for approval',               icon: Sparkles,       group: 'ai_social' },
  { href: '/dashboard/ai-social/approval',       label: 'Approval Flow',      description: 'Approve or revise drafts received via email or WhatsApp',             icon: MessageCircle,  group: 'ai_social' },
  { href: '/dashboard/ai-social/calendar',       label: 'Scheduling Calendar',description: 'See and manage every scheduled and published AI-Social post',         icon: CalendarDays,   group: 'ai_social' },

  // ── Marketer Tools ────────────────────────────────────────────────────────
  { href: '/dashboard/marketer/funnel',     label: 'Funnel Builder',           description: 'Generate a 5-stage marketing funnel blueprint',                     icon: GitBranch,      group: 'marketer' },
  { href: '/dashboard/marketer/audience',   label: 'Audience Research',        description: 'Demographics, pain points, and opportunities for your industry',     icon: Users,          group: 'marketer' },
  { href: '/dashboard/marketer/competitor', label: 'Competitor Intelligence',  description: 'Scan a competitor website and extract strengths, gaps, pricing',     icon: Radar,          group: 'marketer' },
  { href: '/dashboard/marketer/quota',      label: 'Monthly Quota',            description: 'See how many marketer reports you have left this month',             icon: Gauge,          group: 'marketer' },

  // ── System ────────────────────────────────────────────────────────────────
  { href: '/dashboard/notifications', label: 'Notifications', description: 'Review alerts and manage mobile push preferences', icon: BellRing, group: 'system' },
  { href: '/dashboard/settings', label: 'Settings', description: 'Business profile, team members, integrations, and billing', icon: Settings, group: 'system' },
]

const groupLabels: Record<NavGroup, string> = {
  overview: 'Overview',
  pipeline: 'Pipeline',
  engage: 'Engagement',
  grow: 'Growth',
  ai_social: 'AI Social',
  marketer: 'Marketer Tools',
  system: 'System',
}

const ALL_NAV_GROUPS: NavGroup[] = [
  'overview',
  'pipeline',
  'engage',
  'grow',
  'ai_social',
  'marketer',
  'system',
]

const SIDEBAR_GROUPS_STORAGE_KEY = 'cf:sidebar:collapsed-groups'

/** Default: every group folded to keep the nav compact. */
function loadCollapsedGroups(): Set<NavGroup> {
  if (typeof window === 'undefined') return new Set(ALL_NAV_GROUPS)
  try {
    const raw = window.localStorage.getItem(SIDEBAR_GROUPS_STORAGE_KEY)
    if (!raw) return new Set(ALL_NAV_GROUPS)
    const parsed = JSON.parse(raw) as NavGroup[]
    return new Set(parsed)
  } catch {
    return new Set(ALL_NAV_GROUPS)
  }
}

function saveCollapsedGroups(collapsed: Set<NavGroup>) {
  try {
    window.localStorage.setItem(
      SIDEBAR_GROUPS_STORAGE_KEY,
      JSON.stringify(Array.from(collapsed)),
    )
  } catch {
    /* ignore quota */
  }
}

// ── Component ─────────────────────────────────────────────────────────────────

interface SidebarProps {
  collapsed?: boolean
  onToggle?: () => void
  onNavigate?: () => void
}

export function Sidebar({ collapsed, onToggle, onNavigate }: SidebarProps) {
  const pathname = usePathname()

  const { data: me } = useQuery<{
    user_type?: 'tenant' | 'freelancer'
    full_name?: string
  }>({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const isFreelancer = me?.user_type === 'freelancer'

  // Fetch the tenant profile (for the business-type badge display).
  // Freelancers don't have a tenant — skip this query for them.
  const { data: tenantData } = useQuery({
    queryKey: ['tenant', 'me'],
    queryFn: () => tenants.get().then((r) => r.data),
    staleTime: 5 * 60 * 1000,
    retry: false,
    enabled: !isFreelancer,
  })

  // Fetch the admin-controlled tool config for this tenant's category.
  // Same — only tenant accounts have a category-driven tool config.
  const { data: toolConfig } = useQuery({
    queryKey: ['tenant', 'tool-config'],
    queryFn: () => tenants.getToolConfig().then((r) => r.data),
    staleTime: 2 * 60 * 1000,
    retry: false,
    enabled: !isFreelancer,
  })

  const { data: freelancerVisibility } = useQuery({
    queryKey: ['freelancer', 'module-visibility'],
    queryFn: () => freelancerClients.moduleVisibility().then((r) => r.data),
    staleTime: 2 * 60 * 1000,
    retry: false,
    enabled: isFreelancer,
  })

  // Determine visible tools.
  // Freelancers use a separate Super Admin-controlled visibility profile.
  // Tenants honour the admin-controlled tool config.
  const resolvedTools = (): string[] => {
    if (isFreelancer) return freelancerVisibility?.enabled_tools?.length
      ? freelancerVisibility.enabled_tools
      : navItems.map((n) => n.href)
    if (toolConfig?.enabled_tools?.length) return toolConfig.enabled_tools
    if (tenantData?.business_type) {
      const cat = toolConfig?.category ?? classifyBusiness(tenantData.business_type)
      return CATEGORY_DEFAULTS[cat] ?? CATEGORY_DEFAULTS.general
    }
    return CATEGORY_DEFAULTS.general
  }
  const enabledSet = new Set<string>(resolvedTools())
  if (enabledSet.has('/dashboard/money')) enabledSet.add('/dashboard/accounts')

  // Hide the "Clients" entry for non-freelancers (it's freelancer-only).
  const visibleItems = navItems
    .filter((item) => item.href !== '/dashboard/money')
    .filter((item) => enabledSet.has(item.href))
    .filter((item) => (item.href === '/dashboard/clients' ? isFreelancer : true))

  // Group items (memoised — stable reference for activeGroup)
  const groups = useMemo(() => {
    const out: Array<{ key: NavGroup; items: NavItem[] }> = []
    for (const item of visibleItems) {
      const last = out[out.length - 1]
      if (last?.key === item.group) {
        last.items.push(item)
      } else {
        out.push({ key: item.group, items: [item] })
      }
    }
    return out
  }, [visibleItems])

  const activeGroup = useMemo(() => {
    for (const g of groups) {
      if (
        g.items.some((item) =>
          item.exact ? pathname === item.href : pathname.startsWith(item.href),
        )
      ) {
        return g.key
      }
    }
    return null
  }, [groups, pathname])

  const [collapsedGroups, setCollapsedGroups] = useState<Set<NavGroup>>(() => new Set())

  useEffect(() => {
    setCollapsedGroups(loadCollapsedGroups())
  }, [])

  useEffect(() => {
    if (!activeGroup || collapsed) return
    setCollapsedGroups((prev) => {
      if (!prev.has(activeGroup)) return prev
      const next = new Set(prev)
      next.delete(activeGroup)
      saveCollapsedGroups(next)
      return next
    })
  }, [activeGroup, collapsed])

  const toggleGroup = useCallback((key: NavGroup) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      saveCollapsedGroups(next)
      return next
    })
  }, [])

  const handleLogout = async () => {
    await doLogout()
  }

  return (
    <aside
      className={cn(
        'flex h-full min-h-0 flex-col border-r border-brand-forest-800/30 bg-brand-forest-950 text-brand-forest-foreground/85 transition-all duration-200',
        collapsed ? 'w-[68px]' : 'w-64',
      )}
    >
      {/* Brand header */}
      <div className="flex h-16 items-center justify-between border-b border-white/[0.06] px-4">
        {!collapsed ? (
          <Link href="/dashboard" className="inline-flex items-center gap-2.5">
            <BrandMark variant="light" iconSize={32} textClassName="text-[15px] text-white" />
          </Link>
        ) : (
          <Link
            href="/dashboard"
            className="mx-auto inline-flex h-8 w-8 items-center justify-center"
            aria-label="CustomerFlowai"
          >
            <BrandIcon size={32} />
          </Link>
        )}

        {!collapsed && onToggle && (
          <button
            onClick={onToggle}
            className="rounded-md p-1.5 text-white/40 transition-colors hover:bg-white/5 hover:text-white"
            aria-label="Collapse sidebar"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Business type badge (expanded only) */}
      {!collapsed && tenantData?.business_type && (
        <div className="mx-3 mt-3 rounded-md bg-white/[0.04] px-3 py-1.5 text-xs text-white/40">
          <span className="font-semibold capitalize text-white/60">
            {tenantData.business_type}
          </span>
          {toolConfig?.category && (
            <span className="ml-1">· {toolConfig.category.replace(/_/g, ' ')}</span>
          )}
        </div>
      )}

      {/* Nav */}
      <nav className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-2 py-4">
        {groups.map((group, gi) => {
          const isGroupCollapsed = collapsedGroups.has(group.key)
          return (
          <div key={group.key} className={cn(gi > 0 && 'mt-3')}>
            {!collapsed ? (
              <button
                type="button"
                onClick={() => toggleGroup(group.key)}
                className="mb-1 flex w-full items-center justify-between rounded-md px-2 py-1.5 font-mono text-[10px] font-medium uppercase tracking-[0.16em] text-white/35 transition-colors hover:bg-white/[0.04] hover:text-white/55"
                aria-expanded={!isGroupCollapsed}
              >
                <span>{groupLabels[group.key]}</span>
                <ChevronDown
                  className={cn(
                    'h-3.5 w-3.5 shrink-0 transition-transform duration-200',
                    isGroupCollapsed && '-rotate-90',
                  )}
                />
              </button>
            ) : (
              gi > 0 && <div className="my-2 border-t border-white/[0.06]" aria-hidden />
            )}
            {(!isGroupCollapsed || collapsed) && (
            <ul className="space-y-0.5">
              {group.items.map((item, i) => {
                const active = item.exact
                  ? pathname === item.href
                  : pathname.startsWith(item.href)
                const Icon = item.icon

                return (
                  <motion.li
                    key={item.href}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: (gi * 3 + i) * 0.012, duration: 0.16 }}
                  >
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      title={collapsed ? `${item.label} — ${item.description}` : item.description}
                      className={cn(
                        'group relative flex items-center gap-3 rounded-md px-2.5 py-2 text-sm font-medium transition-all',
                        active
                          ? 'bg-brand-teal-400/[0.12] text-white'
                          : 'text-white/55 hover:bg-white/[0.04] hover:text-white',
                        collapsed && 'justify-center px-0',
                      )}
                    >
                      {active && (
                        <span
                          aria-hidden
                          className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-brand-teal-400"
                        />
                      )}
                      <Icon
                        className={cn(
                          'h-4 w-4 shrink-0 transition-colors',
                          active ? 'text-brand-teal-300' : 'text-white/50 group-hover:text-white',
                        )}
                        strokeWidth={2.2}
                      />
                      {!collapsed && (
                        <div className="min-w-0 flex-1">
                          <div className="truncate leading-tight">{item.label}</div>
                          <div className="mt-0.5 truncate text-[10px] font-normal leading-tight text-white/30 group-hover:text-white/50">
                            {item.description}
                          </div>
                        </div>
                      )}
                    </Link>
                  </motion.li>
                )
              })}
            </ul>
            )}
          </div>
        )})}
      </nav>

      {/* Footer */}
      <div className="shrink-0 border-t border-white/[0.06] p-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        {collapsed && onToggle && (
          <button
            onClick={onToggle}
            className="mx-auto mb-1 flex h-8 w-8 items-center justify-center rounded-md text-white/40 transition-colors hover:bg-white/5 hover:text-white"
            aria-label="Expand sidebar"
          >
            <ChevronLeft className="h-4 w-4 rotate-180" />
          </button>
        )}
        <button
          onClick={handleLogout}
          className={cn(
            'flex w-full items-center gap-3 rounded-md px-2.5 py-2 text-sm font-medium text-white/55 transition-colors hover:bg-white/5 hover:text-white',
            collapsed && 'justify-center px-0',
          )}
          title={collapsed ? 'Logout' : undefined}
        >
          <LogOut className="h-4 w-4 shrink-0" strokeWidth={2.2} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  )
}
