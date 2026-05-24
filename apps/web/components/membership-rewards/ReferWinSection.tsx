'use client'

function qrImageUrl(data: string, size = 200) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`
}

export function ReferWinSection({ referWinUrl }: { referWinUrl: string }) {
  if (!referWinUrl) return null

  return (
    <section className="px-6 py-16 bg-white border-t border-gray-100">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl font-bold text-emerald-900 text-center mb-2">Refer &amp; Win</h2>
        <p className="text-sm text-gray-500 text-center mb-10 max-w-xl mx-auto">
          Share the love — refer friends and family and earn rewards when they book or visit.
        </p>
        <div className="grid md:grid-cols-2 gap-10 items-center">
          <div className="flex flex-col items-center">
            <img
              src={qrImageUrl(referWinUrl)}
              alt="Refer and Win QR code"
              width={200}
              height={200}
              className="rounded-lg bg-white p-2 border border-gray-200 shadow-sm"
            />
            <p className="mt-3 text-xs text-gray-400 text-center max-w-xs break-all">{referWinUrl}</p>
          </div>
          <div className="text-gray-600 text-sm leading-relaxed space-y-4">
            <p>
              Our Refer &amp; Win program rewards you for introducing new customers. Scan the QR code
              or tap the button below to share your referral — when someone books through your link,
              you earn loyalty points and they get a warm welcome.
            </p>
            <ul className="list-disc list-inside space-y-1 text-gray-500">
              <li>Share your unique referral link with friends</li>
              <li>They complete a quick form — added to our CRM</li>
              <li>You earn points when they become a customer</li>
            </ul>
            <a
              href={referWinUrl}
              className="inline-block rounded-lg bg-emerald-800 text-white font-semibold px-6 py-3 hover:bg-emerald-900"
            >
              Refer Now
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
