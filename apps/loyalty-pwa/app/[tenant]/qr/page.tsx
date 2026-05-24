'use client'

import { useQuery } from '@tanstack/react-query'
import { AuthGate } from '@/components/AuthGate'
import { loyaltyPortal } from '@/lib/api-client'

export default function QrPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['loyalty-qr', tenant],
    queryFn: () => loyaltyPortal.qr(tenant).then((r) => r.data),
    refetchInterval: 4 * 60 * 1000,
  })

  return (
    <AuthGate tenant={tenant}>
      <div className="space-y-4 text-center">
        <h1 className="text-lg font-semibold">In-store QR</h1>
        <p className="text-sm text-slate-600">Show this code to staff to identify your account.</p>
        {isLoading ? (
          <p className="text-sm text-slate-500">Generating QR…</p>
        ) : data ? (
          <div className="card mx-auto inline-block p-6">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={data.qr_data_url} alt="Loyalty QR code" className="mx-auto h-56 w-56" />
            <p className="mt-3 text-xs text-slate-500">
              Refreshes automatically · expires {formatWhen(data.expires_at)}
            </p>
          </div>
        ) : (
          <p className="text-sm text-red-600">Could not load QR code.</p>
        )}
        <button type="button" className="btn-secondary" disabled={isFetching} onClick={() => refetch()}>
          Refresh now
        </button>
      </div>
    </AuthGate>
  )
}

function formatWhen(iso: string) {
  return new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}
