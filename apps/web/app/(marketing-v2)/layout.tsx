import { CompareBanner } from '@/components/marketing-v2/CompareBanner'

export default function MarketingV2Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <CompareBanner />
      <div className="pt-10">{children}</div>
    </div>
  )
}
