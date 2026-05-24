'use client'

function qrImageUrl(data: string, size = 180) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`
}

type Props = {
  tenantName: string
  rewardsPortalUrl: string
}

export function RewardsWalletSection({ tenantName, rewardsPortalUrl }: Props) {
  return (
    <section className="border-y border-emerald-100 bg-emerald-50/60 px-6 py-14">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-8 md:flex-row md:items-start md:justify-between">
        <div className="text-center md:text-left md:max-w-md">
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-700">
            Rewards wallet
          </p>
          <h2 className="mt-2 text-2xl font-bold text-emerald-950">
            Download the {tenantName} rewards app
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-emerald-900/80">
            Check your points balance, redeem rewards, and show your in-store QR code from your
            phone. Add to your home screen for quick access.
          </p>
          <a
            href={rewardsPortalUrl}
            className="mt-6 inline-flex rounded-lg bg-emerald-800 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-900"
          >
            Open rewards wallet
          </a>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-white p-4 shadow-sm text-center">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={qrImageUrl(rewardsPortalUrl)}
            alt={`QR code for ${tenantName} rewards wallet`}
            width={180}
            height={180}
            className="mx-auto"
          />
          <p className="mt-3 text-xs text-gray-500">Scan to open on your phone</p>
        </div>
      </div>
    </section>
  )
}
