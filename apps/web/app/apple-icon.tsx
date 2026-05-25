import { ImageResponse } from 'next/og'

export const size = { width: 512, height: 512 }
export const contentType = 'image/png'

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(145deg, #025422 0%, #013318 55%, #02140a 100%)',
          position: 'relative',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 72,
            right: 72,
            width: 72,
            height: 72,
            borderRadius: 999,
            background: '#20ccce',
            boxShadow: '0 0 40px rgba(32,204,206,0.55)',
          }}
        />
        <svg width="320" height="240" viewBox="0 0 320 240" fill="none">
          <path
            d="M32 168 C 96 56, 176 24, 288 8"
            stroke="white"
            strokeWidth="28"
            strokeLinecap="round"
          />
          <path
            d="M48 192 C 104 144, 176 128, 264 152"
            stroke="#20ccce"
            strokeWidth="24"
            strokeLinecap="round"
          />
          <path
            d="M32 216 H 272"
            stroke="white"
            strokeOpacity="0.88"
            strokeWidth="20"
            strokeLinecap="round"
          />
        </svg>
      </div>
    ),
    { ...size },
  )
}
