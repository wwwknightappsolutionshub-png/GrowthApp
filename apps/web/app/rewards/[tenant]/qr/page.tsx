'use client'

import { useQuery } from '@tanstack/react-query'
import { LoyaltyAuthGate } from '@/components/loyalty-portal/LoyaltyAuthGate'
import { loyaltyPortalCustomer } from '@/lib/api-client'

function formatWhen(iso: string) {
  return new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

export default function RewardsQrPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['loyalty-qr', tenant],
    queryFn: () => loyaltyPortalCustomer.qr(tenant).then((r) => r.data),
    refetchInterval: 4 * 60 * 1000,
  })

  return (
    <LoyaltyAuthGate tenant={tenant}>
      <div className="space-y-4 text-center">
        <h1 className="text-lg font-semibold text-brand">In-store QR</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Show this code to staff to identify your account.
        </p>
        {isLoading ? (
          <p className="text-sm text-[hsl(var(--muted-foreground))]">Generating QR…</p>
        ) : data ? (
          <div className="card card-accent mx-auto inline-block p-6">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={data.qr_data_url} alt="Loyalty QR code" className="mx-auto h-56 w-56 rounded-lg" />
            <p className="mt-3 text-xs text-[hsl(var(--muted-foreground))]">
              Refreshes automatically · expires {formatWhen(data.expires_at)}
            </p>
          </div>
        ) : (
          <p className="text-sm text-red-600">Could not load QR code.</p>
        )}
        <button
          type="button"
          className="btn-secondary"
          disabled={isFetching}
          onClick={() => void refetch()}
        >
          Refresh now
        </button>
      </div>
    </LoyaltyAuthGate>
  )
}
