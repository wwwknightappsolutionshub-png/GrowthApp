'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import {
  ArrowRight,
  BadgePoundSterling,
  Bot,
  Briefcase,
  Calendar,
  CheckCircle2,
  CreditCard,
  FileText,
  Gauge,
  Globe,
  Inbox,
  LayoutDashboard,
  Megaphone,
  MessageCircle,
  MessageSquare,
  Palette,
  PhoneCall,
  Radar,
  Sparkles,
  Star,
  Target,
  TrendingUp,
  Upload,
  Users,
  Zap,
  CalendarRange,
  GitBranch,
  Globe2,
} from 'lucide-react'
import { auth } from '@/lib/api-client'

interface Me {
  id: string
  email: string
  full_name: string
  user_type: 'tenant' | 'freelancer'
  onboarding_completed: boolean
}

interface ModuleCard {
  group: string
  title: string
  icon: React.ComponentType<{ className?: string }>
  what: string
  how: string[]
  ideal_for: ('tenant' | 'freelancer')[]
}

const MODULES: ModuleCard[] = [
  {
    group: 'Get started',
    title: 'Dashboard',
    icon: LayoutDashboard,
    what:
      'Your home base. Daily snapshot of revenue, open jobs, pending tasks, recent leads and live alerts.',
    how: [
      'Visit /dashboard each morning to see what needs your attention',
      'Click any KPI tile to drill into that module',
      'The activity feed shows everything happening across your business in real time',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Get started',
    title: 'AI Assistant',
    icon: Sparkles,
    what:
      'A chat-style copilot that can answer questions, draft messages, score leads, and explain trends in your data.',
    how: [
      'Open /dashboard/assistant from the sidebar',
      'Ask "Which leads should I call first?" or "Draft a follow-up SMS to John"',
      'It uses your real data — leads, customers, invoices — to give you specific answers',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  // ── Clients / Pipeline ────────────────────────────────────────────────
  {
    group: 'Pipeline',
    title: 'Clients',
    icon: Briefcase,
    what:
      "Manage every client you service. Each client gets their own workspace where you can run their CRM, social, automations and analytics independently.",
    how: [
      'Click "Add Client" on the clients page',
      "Enter their business name, contact info and social handles (Instagram, Facebook, TikTok, X)",
      'Switch context into a client to run any tool on their behalf',
    ],
    ideal_for: ['freelancer'],
  },
  {
    group: 'Pipeline',
    title: 'Leads',
    icon: Target,
    what:
      'Every incoming enquiry from your forms, ads, and referrals. Each lead is scored 0–100 by AI based on intent and fit.',
    how: [
      'New leads appear in the inbox automatically when they fill in a form or call the AI receptionist',
      'Click any lead to see the full conversation, score breakdown, and next-best action',
      'Convert hot leads to customers with one click',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Pipeline',
    title: 'CRM',
    icon: Users,
    what:
      'Your customer database. Track contact details, visit history, follow-up reminders, special notes, deals and lifetime value.',
    how: [
      'Add a customer manually or import from a CSV',
      'Set a "next visit date" or "follow-up reminder" — CustomerFlow will notify you',
      'Use segments to target specific customer groups in outreach campaigns',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Pipeline',
    title: 'Tasks',
    icon: CheckCircle2,
    what:
      'A team task board for everything that needs to get done. Personal lanes plus shared lanes per project.',
    how: [
      'Create a task with title, owner, due date and priority',
      'Drag between "To do / In progress / Done"',
      'AI Assistant auto-suggests tasks based on recent customer activity',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Pipeline',
    title: 'Bookings',
    icon: Calendar,
    what: 'Calendar of every appointment, job, and consultation. Customers can self-book online.',
    how: [
      'Share your booking link in emails / WhatsApp — customers pick a slot themselves',
      'Add manual bookings for phone callers',
      'Automatic 24h SMS reminders cut no-shows by up to 50%',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Pipeline',
    title: 'Quotes',
    icon: FileText,
    what: 'Create branded PDF quotes, send them by email/WhatsApp, and track open + accept events.',
    how: [
      'Build a quote from a customer record — line items pull from your saved services',
      'Send → customer signs digitally → status flips to "Accepted"',
      'Convert any accepted quote to an invoice in one click',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Pipeline',
    title: 'Invoices',
    icon: CreditCard,
    what:
      'Issue invoices, record payments (cash, bank transfer, Stripe), and chase overdue balances automatically.',
    how: [
      'Create an invoice from a job, quote or manually',
      'Email it with a "Pay Now" button — customer pays online with card or Apple Pay',
      'Overdue invoices trigger automatic polite reminder sequences',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Pipeline',
    title: 'Money',
    icon: BadgePoundSterling,
    what:
      'Revenue dashboard — cash flow, MRR, monthly P&L, top-paying customers, and outstanding balance.',
    how: [
      'Open /dashboard/money for the full picture',
      'Filter by period, customer, or service type',
      'Export CSV for your accountant',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  // ── Engagement ────────────────────────────────────────────────────────
  {
    group: 'Engagement',
    title: 'Messages',
    icon: MessageSquare,
    what: 'Unified inbox combining SMS, email and form messages from all your customers.',
    how: [
      'Reply directly from the inbox — no need to switch apps',
      'AI suggests draft replies you can approve in one tap',
      'Threads link automatically to the matching CRM record',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Engagement',
    title: 'WhatsApp',
    icon: PhoneCall,
    what:
      'Two-way WhatsApp Business conversations with AI-suggested replies and automatic CRM logging.',
    how: [
      'Connect your WhatsApp Business number in Settings',
      'Incoming messages appear in /dashboard/whatsapp',
      'AI suggests on-brand replies trained on your past conversations',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Engagement',
    title: 'AI Auto-Replies',
    icon: Inbox,
    what:
      'AI-drafted responses to reviews and messages, queued for your approval before they go out.',
    how: [
      'Approve each draft with a thumbs-up or tweak the wording',
      'Set rules for what gets auto-approved (e.g. 5-star reviews only)',
      'AI learns your tone from your past replies',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Engagement',
    title: 'Outreach',
    icon: Megaphone,
    what:
      'Broadcast campaigns, win-back sequences, and seasonal promotions across SMS, email and WhatsApp.',
    how: [
      'Pick a segment of customers (e.g. "Last booked 6+ months ago")',
      'Choose a channel and message template — or have AI write it',
      'Schedule send and watch results stream in',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  // ── Growth ────────────────────────────────────────────────────────────
  {
    group: 'Growth',
    title: 'Landing Pages',
    icon: Globe,
    what:
      'AI-generated service landing pages, ranked locally, designed to convert visitors into leads.',
    how: [
      'Tell the AI which service you want to promote (e.g. "Emergency boiler repairs")',
      'It writes copy, picks images, and publishes a live page in seconds',
      'Every lead from that page lands straight in your inbox',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Growth',
    title: 'Ads',
    icon: Megaphone,
    what: 'AI-written ad copy for Google, Facebook and Instagram campaigns with audience targeting.',
    how: [
      'Brief the AI on your offer and audience',
      'It writes 3 ad variants you can edit and approve',
      'Publish straight to Meta / Google with your connected ad account',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Growth',
    title: 'SEO',
    icon: Globe2,
    what:
      'On-page SEO audit + recommendations to rank higher in local search and Google Maps.',
    how: [
      'Run an audit on any page — gets a score 0–100 with concrete fixes',
      'AI suggests title tags, meta descriptions and H1 rewrites',
      'Tracks ranking changes weekly so you see what\'s working',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Growth',
    title: 'Automations',
    icon: Zap,
    what:
      'Trigger-based workflows — when X happens, do Y. Reminders, nurture sequences, escalations.',
    how: [
      'Pick a trigger ("Lead scored 80+", "Invoice 7 days overdue", "Customer last seen 60 days ago")',
      'Add actions (send SMS, create task, notify staff, etc.)',
      'CustomerFlow runs it forever — no manual work',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Growth',
    title: 'Reviews',
    icon: Star,
    what:
      'Request, monitor and respond to Google reviews automatically. Boosts your local ranking.',
    how: [
      'Auto-request a review 24h after job completion via SMS',
      'New review notifications hit your inbox',
      'AI drafts a personalised public reply within seconds',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Growth',
    title: 'Referrals',
    icon: TrendingUp,
    what:
      'Reward customers for sending you new business — track who referred who, automate payouts.',
    how: [
      'Define a reward (e.g. £25 off next service, or a £10 Amazon voucher)',
      'Each customer gets a personalised referral link to share',
      'New leads via that link auto-credit the referrer when they convert',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  // ── AI Social ────────────────────────────────────────────────────────
  {
    group: 'AI Social',
    title: 'Brand Identity',
    icon: Palette,
    what:
      'Define your colours, fonts, tone-of-voice and logo so AI-generated posts always feel on-brand.',
    how: [
      'Upload your logo and pick your primary/secondary colours',
      "Choose tone: professional / friendly / playful / authoritative",
      'AI applies this style to every draft, image prompt and caption',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'AI Social',
    title: 'Upload Samples',
    icon: Upload,
    what: 'Upload reference posts (images, videos, PDFs) so the AI learns your visual style.',
    how: [
      'Drop in 5–10 of your best previous posts',
      'AI extracts visual themes — colours, layouts, fonts used',
      'Future drafts will mirror that style automatically',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'AI Social',
    title: 'Posting Preferences',
    icon: CalendarRange,
    what:
      'Tell the AI how often to post, which days, and what time. It plans your calendar automatically.',
    how: [
      'Set frequency (e.g. 3 posts per week)',
      'Pick days and a time range (e.g. Mon/Wed/Fri 9–11am)',
      'AI schedules and queues content within those windows',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'AI Social',
    title: 'Draft Review',
    icon: Sparkles,
    what:
      'Generated drafts wait here for your review. Approve to schedule, request revisions, or delete.',
    how: [
      'Click any draft to preview the post as it would appear on each platform',
      'One-tap approve → automatically scheduled to your queue',
      '"Revise" with a comment → AI regenerates based on your feedback',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'AI Social',
    title: 'Approval Flow',
    icon: MessageCircle,
    what:
      'Get a daily email/WhatsApp summary of pending drafts. Reply "approve" or "revise" without opening the app.',
    how: [
      "We send you one digest per day — you don't need to log in to approve",
      'Reply directly from email or WhatsApp',
      'Approved posts publish at their scheduled time',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'AI Social',
    title: 'Scheduling Calendar',
    icon: Calendar,
    what:
      'See every scheduled and published post across all platforms (Facebook, Instagram, TikTok, X) in one view.',
    how: [
      'Drag posts around to reschedule',
      'Filter by platform or status',
      'Click any past post to see engagement metrics',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  // ── Marketer Tools ────────────────────────────────────────────────────
  {
    group: 'Marketer Tools',
    title: 'Funnel Builder',
    icon: GitBranch,
    what:
      'AI generates a 5-stage marketing funnel blueprint: Landing → Lead Magnet → Nurture → Offer → Upsell.',
    how: [
      'Pick your funnel type (lead-gen, sales, webinar, etc.)',
      'AI returns the full blueprint with copy and step-by-step instructions',
      'Use it as a playbook to build each stage',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Marketer Tools',
    title: 'Audience Research',
    icon: Users,
    what:
      'Demographic, psychographic and pain-point research for any industry, delivered as a report.',
    how: [
      'Enter the industry/niche',
      'AI returns demographics, pain points, opportunities — sourced and dated',
      'Use insights to write better ads, landing pages and outreach',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Marketer Tools',
    title: 'Competitor Intelligence',
    icon: Radar,
    what:
      'Scan a competitor website and get a report on strengths, weaknesses, pricing and positioning gaps.',
    how: [
      'Paste a competitor URL',
      'AI crawls and analyses the site',
      'Returns a structured report you can act on within minutes',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  {
    group: 'Marketer Tools',
    title: 'Monthly Quota',
    icon: Gauge,
    what: 'See how many marketer reports you have left this month and your renewal date.',
    how: [
      'Every plan includes a monthly quota of audience + competitor reports',
      'Use them anytime — unused reports roll into the next month (up to your plan cap)',
      'Upgrade for unlimited if you outgrow your quota',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
  // ── System ────────────────────────────────────────────────────────────
  {
    group: 'System',
    title: 'AI Assistant (sales support)',
    icon: Bot,
    what:
      "A dedicated AI chat available 24/7 inside the app — for questions about CustomerFlow itself.",
    how: [
      'Click the chat bubble at the bottom-right of any page',
      'Ask "How do I import contacts?" or "What does this metric mean?"',
      'It pulls live answers from the help docs',
    ],
    ideal_for: ['tenant', 'freelancer'],
  },
]

const GROUP_ORDER = [
  'Get started',
  'Pipeline',
  'Engagement',
  'Growth',
  'AI Social',
  'Marketer Tools',
  'System',
]

export default function OnboardingPage() {
  const router = useRouter()
  const qc = useQueryClient()

  const me = useQuery<Me>({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data),
    retry: false,
  })

  const complete = useMutation({
    mutationFn: () => auth.completeOnboarding(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['me'] })
      toast.success("You're all set! Next: launch your business page.")
      const isFreelancer = me.data?.user_type === 'freelancer'
      router.push(isFreelancer ? '/dashboard' : '/dashboard/site-builder')
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? 'Could not complete onboarding')
    },
  })

  // If already completed, send straight to dashboard.
  if (me.isSuccess && me.data?.onboarding_completed) {
    router.replace('/dashboard')
    return null
  }

  // If unauthenticated, kick to login.
  if (me.isError) {
    if (typeof window !== 'undefined') router.replace('/login?next=/onboarding')
    return null
  }

  const userType = me.data?.user_type ?? 'tenant'
  const firstName = (me.data?.full_name ?? '').split(' ')[0] || 'there'

  const grouped = GROUP_ORDER.map((g) => ({
    group: g,
    modules: MODULES.filter((m) => m.group === g && m.ideal_for.includes(userType)),
  })).filter((g) => g.modules.length > 0)

  return (
    <div className="pb-4">
      {/* Sticky actions — always reachable on tablet / short viewports */}
      <div className="sticky top-0 z-30 -mx-4 mb-6 border-b border-border/80 bg-background/95 px-4 py-3 backdrop-blur sm:-mx-0 sm:rounded-xl sm:border sm:px-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-muted-foreground">
            Finish the tour or jump straight into your workspace.
          </p>
          <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto sm:justify-end">
            <Link
              href={userType === 'freelancer' ? '/dashboard' : '/dashboard/site-builder'}
              className="inline-flex flex-1 items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm text-foreground hover:bg-muted sm:flex-none"
            >
              Skip for now
            </Link>
            <button
              type="button"
              onClick={() => complete.mutate()}
              disabled={complete.isPending}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-brand-forest-foreground shadow-brand hover:bg-brand-forest-800 disabled:opacity-60 sm:flex-none"
            >
              {complete.isPending ? 'Saving…' : 'Go to dashboard'}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="mb-8 text-center md:mb-10">
        <span className="inline-flex items-center gap-2 rounded-full border border-brand-teal-400/30 bg-brand-teal-400/10 px-3 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.16em] text-brand-teal-700">
          <Sparkles className="h-3 w-3" />
          Welcome to CustomerFlow AI
        </span>
        <h1 className="mt-4 font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl md:text-4xl">
          Hi {firstName} — let&apos;s give you the tour.
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-sm text-muted-foreground">
          {userType === 'freelancer'
            ? 'Here is everything you can do inside your freelancer workspace. Each module lives in the sidebar after you finish this tour — read what each does and how to use it before you dive in.'
            : 'Here is everything you can do inside CustomerFlow AI. Read through what each module does and how to use it. You can revisit this page anytime from Settings.'}
        </p>
      </div>

      {/* Quick stats */}
      <div className="mb-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Modules', value: grouped.reduce((sum, g) => sum + g.modules.length, 0) },
          { label: 'AI assistants', value: '5+' },
          { label: 'Automations', value: 'Unlimited' },
          { label: 'Setup time', value: '~10 min' },
        ].map((s) => (
          <div key={s.label} className="rounded-lg border border-border bg-card p-4">
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
              {s.label}
            </div>
            <div className="mt-1 text-2xl font-bold tabular-nums text-foreground">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Module groups */}
      {grouped.map(({ group, modules }) => (
        <section key={group} className="mb-10">
          <div className="mb-3 flex items-center gap-3">
            <h2 className="font-display text-xl font-semibold tracking-tight text-foreground">
              {group}
            </h2>
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground">
              {modules.length} module{modules.length === 1 ? '' : 's'}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {modules.map((m) => (
              <ModuleTile key={m.title} module={m} />
            ))}
          </div>
        </section>
      ))}

      {/* Footer CTA */}
      <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-border bg-card/95 p-4 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-[0_-8px_30px_rgba(0,0,0,0.08)] backdrop-blur sm:sticky sm:bottom-6 sm:mt-10 sm:rounded-xl sm:border sm:shadow-lg">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="font-display text-lg font-semibold text-foreground">
            Ready to start?
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            You can revisit this guide anytime from <strong>Settings → Help & Tour</strong>.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-4 py-2 text-sm text-foreground hover:bg-muted"
          >
            Skip for now
          </Link>
          <button
            onClick={() => complete.mutate()}
            disabled={complete.isPending}
            className="inline-flex items-center gap-2 rounded-md bg-brand-forest-700 px-5 py-2 text-sm font-semibold text-brand-forest-foreground shadow-brand transition-all hover:bg-brand-forest-800 disabled:opacity-60"
          >
            {complete.isPending ? 'Saving…' : 'Take me to my dashboard'}
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
        </div>
      </div>
    </div>
  )
}


function ModuleTile({ module }: { module: ModuleCard }) {
  const Icon = module.icon
  return (
    <div className="rounded-lg border border-border bg-card p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="rounded-md bg-brand-forest-100 p-2 text-brand-forest-700">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-foreground">{module.title}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{module.what}</p>
          <p className="mt-3 mb-1 text-[10px] uppercase tracking-widest text-muted-foreground/80">
            How to use
          </p>
          <ul className="space-y-1 text-xs text-foreground/80">
            {module.how.map((step, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-brand-forest-600" />
                {step}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
