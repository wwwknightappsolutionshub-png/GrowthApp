import './loyalty-portal.css'

export default function RewardsRootLayout({ children }: { children: React.ReactNode }) {
  return <div className="rewards-portal min-h-dvh bg-slate-50 text-slate-900">{children}</div>
}
