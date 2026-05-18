'use client'

import { useEffect, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { X } from 'lucide-react'
import { fetchMe } from '@/lib/auth'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopBar } from '@/components/layout/TopBar'
import { CommandPalette } from '@/components/search/CommandPalette'
import { PageTransition } from '@/components/layout/PageTransition'
import { TooltipProvider } from '@/components/ui/tooltip'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetchMe().then((me) => {
      if (cancelled) return
      if (!me) {
        router.replace('/login')
      } else if (me.is_superadmin) {
        router.replace('/admin')
      } else if (me.onboarding_completed === false) {
        router.replace('/onboarding')
      } else {
        setReady(true)
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
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className="flex h-dvh bg-background text-foreground overflow-hidden">
        <div className="hidden lg:block">
          <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
        </div>

        {mobileNavOpen && (
          <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
            <button
              type="button"
              aria-label="Close navigation"
              className="absolute inset-0 bg-black/60"
              onClick={() => setMobileNavOpen(false)}
            />
            <div className="relative h-full w-[min(18rem,88vw)] shadow-2xl">
              <button
                type="button"
                onClick={() => setMobileNavOpen(false)}
                className="absolute right-3 top-3 z-10 inline-flex h-8 w-8 items-center justify-center rounded-md bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
                aria-label="Close navigation"
              >
                <X className="h-4 w-4" />
              </button>
              <Sidebar onNavigate={() => setMobileNavOpen(false)} />
            </div>
          </div>
        )}

        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <TopBar onMenuClick={() => setMobileNavOpen(true)} />
          <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6">
            <PageTransition>{children}</PageTransition>
          </main>
        </div>
        <CommandPalette />
      </div>
    </TooltipProvider>
  )
}
