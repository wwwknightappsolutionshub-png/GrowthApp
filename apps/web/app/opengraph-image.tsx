import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const alt = 'CustomerFlowai — AI operating system for UK businesses'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '72px',
          background: 'linear-gradient(135deg, #012a14 0%, #025422 45%, #0a6b3d 100%)',
          color: '#ffffff',
          fontFamily: 'system-ui, sans-serif',
        }}
      >
        <div
          style={{
            fontSize: 28,
            fontWeight: 600,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: '#7dffc0',
            marginBottom: 24,
          }}
        >
          CustomerFlowai
        </div>
        <div
          style={{
            fontSize: 64,
            fontWeight: 700,
            lineHeight: 1.1,
            maxWidth: 900,
          }}
        >
          The AI Operating System for UK Businesses
        </div>
        <div
          style={{
            marginTop: 32,
            fontSize: 28,
            lineHeight: 1.4,
            color: 'rgba(255,255,255,0.82)',
            maxWidth: 820,
          }}
        >
          Lead generation, CRM, bookings, invoicing and retention — unified in one platform.
        </div>
      </div>
    ),
    { ...size },
  )
}
