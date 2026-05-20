'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { admin } from '@/lib/api-client'
import { logout as doLogout } from '@/lib/auth'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BellRing,
  BookOpen,
  Brain,
  Briefcase,
  Building2,
  FileSearch,
  CalendarClock,
  CreditCard,
  FileText,
  Gauge,
  Globe,
  HeadphonesIcon,
  HelpCircle,
  Inbox,
  LayoutDashboard,
  LogOut,
  Mail,
  MailOpen,
  Menu,
  Monitor,
  Play,
  Search,
  Settings,
  Settings2,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  Star,
  ToggleLeft,
  TrendingUp,
  Users,
  X,
} from 'lucide-react'

const NAV_GROUPS = [
  {
    label: 'Core',
    items: [
      { href: '/admin', label: 'Dashboard', icon: Activity, exact: true },
      { href: '/admin/tenants', label: 'Tenants', icon: Building2 },
      { href: '/admin/tenant-health', label: 'Tenant Pulse', icon: BellRing },
    ],
  },
  {
    label: 'Lead Engine',
    items: [
      { href: '/admin/marketplace', label: 'Marketplace', icon: ShoppingBag },
      { href: '/admin/lead-marketplace', label: 'Marketplace (Legacy)', icon: ShoppingBag },
      { href: '/admin/lead-requests', label: 'Lead Requests', icon: Inbox },
      { href: '/admin/ai-engine', label: 'AI Engine', icon: Brain },
    ],
  },
  {
    label: 'Scraper',
    items: [
      { href: '/admin/ai-scraper', label: 'AI Scraper (All)', icon: Sparkles },
      { href: '/admin/scraper/sources', label: 'Sources', icon: Globe },
      { href: '/admin/scraper/tasks', label: 'Tasks', icon: Play },
      { href: '/admin/scraper/results', label: 'Results', icon: Monitor },
    ],
  },
  {
    label: 'Platform',
    items: [
      { href: '/admin/referrals', label: 'Referrals', icon: TrendingUp },
      { href: '/admin/billing', label: 'Billing', icon: CreditCard },
      { href: '/admin/users', label: 'Users & Roles', icon: Users },
      { href: '/admin/communications', label: 'Communications', icon: Mail },
    ],
  },
  {
    label: 'Config',
    items: [
      { href: '/admin/marketing', label: 'Marketing CMS', icon: LayoutDashboard },
      { href: '/admin/marketing/adaptive-pages', label: 'Adaptive Pages', icon: Sparkles },
      { href: '/admin/reviews', label: 'Reviews', icon: Star },
      { href: '/admin/tool-configs', label: 'Module Visibility', icon: ToggleLeft },
      { href: '/admin/operations', label: 'Operations', icon: Monitor },
      { href: '/admin/settings', label: 'Settings', icon: Settings },
      { href: '/admin/support', label: 'Support', icon: HeadphonesIcon },
    ],
  },
  {
    label: 'Content',
    items: [
      { href: '/admin/content/faq', label: 'FAQ', icon: HelpCircle },
      { href: '/admin/content/blog', label: 'Blog Posts', icon: BookOpen },
      { href: '/admin/content/pages', label: 'Static Pages', icon: FileText },
      { href: '/admin/email-templates', label: 'Email Templates', icon: MailOpen },
    ],
  },
  {
    label: 'AI Social',
    items: [
      { href: '/admin/ai-social/settings', label: 'Global AI Settings', icon: Settings2 },
      { href: '/admin/ai-social/insights', label: 'Tenant Insights', icon: BarChart3 },
      { href: '/admin/ai-social/failures', label: 'Failure Logs', icon: AlertTriangle },
      { href: '/admin/ai-social/scheduler', label: 'Scheduler Status', icon: CalendarClock },
      { href: '/admin/ai-social/regenerate', label: 'Manual Regeneration', icon: Sparkles },
    ],
  },
  {
    label: 'Marketer Tools',
    items: [
      { href: '/admin/marketer/quotas', label: 'Quota Configuration', icon: Gauge },
      { href: '/admin/marketer/settings', label: 'Global Marketer Settings', icon: Settings2 },
      { href: '/admin/marketer/usage', label: 'Marketer Usage Logs', icon: Activity },
      { href: '/admin/marketer/competitor-queue', label: 'Competitor Queue Monitor', icon: Search },
    ],
  },
  {
    label: 'Freelancer Management',
    items: [
      { href: '/admin/freelancer-management/billing-inspector', label: 'Billing Inspector', icon: Briefcase },
      { href: '/admin/freelancer-management/module-visibility', label: 'Module Visibility', icon: ToggleLeft },
    ],
  },
  {
    label: 'Billing Inspector',
    items: [
      { href: '/admin/billing-inspector', label: 'Overview', icon: BarChart3, exact: true },
      { href: '/admin/billing-inspector/tenants', label: 'Tenants', icon: Building2 },
      { href: '/admin/billing-inspector/freelancers', label: 'Freelancers', icon: Briefcase },
      { href: '/admin/billing-inspector/audit-logs', label: 'Audit Logs', icon: FileSearch },
    ],
  },
]

// Flat list for backwards compat with active check
const NAV = NAV_GROUPS.flatMap(g => g.items)

interface AdminMe {
  id: string
  email: string
  full_name: string
}

interface AdminSidebarProps {
  pathname: string
  me: AdminMe | null
  onNavigate?: () => void
}

function AdminSidebar({ pathname, me, onNavigate }: AdminSidebarProps) {
  return (
    <aside className="flex h-full min-h-0 w-full max-w-full flex-col border-r border-gray-800 bg-gray-900 lg:w-64">
      <div className="flex h-16 shrink-0 items-center gap-3 border-b border-gray-800 px-5">
        <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
          <ShieldCheck className="w-4 h-4 text-amber-400" />
        </div>
        <div>
          <div className="text-sm font-bold tracking-tight">CustomerFlow AI</div>
          <div className="text-[10px] uppercase tracking-widest text-amber-400 font-semibold">
            Super Admin
          </div>
        </div>
      </div>

      <nav className="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain py-4 px-2">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <p className="px-3 mb-1 text-[10px] uppercase tracking-widest text-gray-600 font-semibold">{group.label}</p>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const Icon = item.icon
                const active = 'exact' in item && item.exact
                  ? pathname === item.href
                  : pathname === item.href || pathname.startsWith(item.href + '/')
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onNavigate}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      active
                        ? 'bg-amber-500/15 text-amber-300'
                        : 'text-gray-400 hover:text-white hover:bg-gray-800'
                    }`}
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span className="truncate">{item.label}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="shrink-0 border-t border-gray-800 px-3 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
        {me && (
          <div className="mb-3 px-2">
            <div className="text-sm font-medium truncate">{me.full_name}</div>
            <div className="text-xs text-gray-500 truncate">{me.email}</div>
          </div>
        )}
        <button
          onClick={() => doLogout()}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  )
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [me, setMe] = useState<AdminMe | null>(null)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    admin
      .me()
      .then((res) => {
        if (cancelled) return
        setMe(res.data)
        setReady(true)
      })
      .catch((err) => {
        if (cancelled) return
        // 401 → never authenticated; 403 → authenticated but not super-admin.
        const status = err?.response?.status
        if (status === 403) {
          router.replace('/dashboard')
        } else {
          router.replace('/login?next=/admin')
        }
      })
    return () => {
      cancelled = true
    }
  }, [router])

  useEffect(() => {
    setMobileNavOpen(false)
  }, [pathname])

  useEffect(() => {
    if (!mobileNavOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileNavOpen(false)
    }
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKeyDown)
    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [mobileNavOpen])

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="animate-spin w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="flex h-dvh bg-gray-950 text-gray-100 overflow-hidden">
      <div className="hidden lg:block">
        <AdminSidebar pathname={pathname} me={me} />
      </div>

      {mobileNavOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
          <button
            type="button"
            aria-label="Close navigation"
            className="absolute inset-0 bg-black/60"
            onClick={() => setMobileNavOpen(false)}
          />
          <div className="relative flex h-dvh max-h-dvh w-[min(18rem,88vw)] flex-col overflow-hidden shadow-2xl">
            <button
              type="button"
              onClick={() => setMobileNavOpen(false)}
              className="absolute right-3 top-3 z-10 inline-flex h-8 w-8 items-center justify-center rounded-md bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
              aria-label="Close navigation"
            >
              <X className="h-4 w-4" />
            </button>
            <AdminSidebar pathname={pathname} me={me} onNavigate={() => setMobileNavOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-16 shrink-0 items-center gap-3 border-b border-gray-800 bg-gray-950/85 px-3 backdrop-blur sm:px-6 lg:hidden">
          <button
            type="button"
            onClick={() => setMobileNavOpen(true)}
            className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-gray-800 bg-gray-900 text-gray-300 hover:bg-gray-800 hover:text-white"
            aria-label="Open navigation"
          >
            <Menu className="h-4 w-4" />
          </button>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-bold tracking-tight">CustomerFlow AI</div>
            <div className="text-[10px] uppercase tracking-widest text-amber-400 font-semibold">
              Super Admin
            </div>
          </div>
          <button
            type="button"
            onClick={() => doLogout()}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-gray-800 px-2.5 py-1.5 text-xs text-gray-300 hover:bg-gray-800 hover:text-white"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign out
          </button>
        </header>

        <main className="flex-1 overflow-y-auto overflow-x-hidden">
          <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 sm:py-6 lg:px-8 lg:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
