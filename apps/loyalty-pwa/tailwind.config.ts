import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        tenant: 'var(--tenant-primary, #2563EB)',
      },
    },
  },
  plugins: [],
}

export default config
