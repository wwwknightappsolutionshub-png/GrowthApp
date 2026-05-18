import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: { DEFAULT: '1.5rem', md: '2rem', lg: '2.5rem' },
      screens: {
        sm: '640px',
        md: '768px',
        lg: '1024px',
        xl: '1200px',
        '2xl': '1320px',
      },
    },
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)'],
        display: ['var(--font-display)'],
        mono: ['var(--font-mono)'],
      },
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',

        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        success: {
          DEFAULT: 'hsl(var(--success))',
          foreground: 'hsl(var(--success-foreground))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          foreground: 'hsl(var(--warning-foreground))',
        },

        /**
         * Brand surfaces — use sparingly for moments that *must* read as
         * "CustomerFlow brand" (logo, hero CTA, login panel, sidebar).
         */
        brand: {
          forest: {
            DEFAULT: 'hsl(var(--brand-forest))',
            foreground: 'hsl(var(--brand-forest-foreground))',
            50: 'hsl(141 50% 96%)',
            100: 'hsl(141 45% 90%)',
            200: 'hsl(141 42% 80%)',
            300: 'hsl(141 42% 64%)',
            400: 'hsl(141 50% 42%)',
            500: 'hsl(141 70% 28%)',
            600: 'hsl(141 85% 22%)',
            700: 'hsl(141 95% 17%)' /* #025422 */,
            800: 'hsl(141 90% 13%)',
            900: 'hsl(141 90% 9%)',
            950: 'hsl(141 90% 5%)',
          },
          teal: {
            DEFAULT: 'hsl(var(--brand-teal))',
            foreground: 'hsl(var(--brand-teal-foreground))',
            50: 'hsl(181 70% 96%)',
            100: 'hsl(181 70% 90%)',
            200: 'hsl(181 68% 78%)',
            300: 'hsl(181 70% 65%)',
            400: 'hsl(181 73% 47%)' /* #20ccce */,
            500: 'hsl(181 80% 38%)',
            600: 'hsl(181 85% 30%)',
            700: 'hsl(181 90% 22%)',
            800: 'hsl(181 90% 15%)',
            900: 'hsl(181 90% 9%)',
          },
        },
      },
      boxShadow: {
        // Subtle enterprise depth — not the candy-shop "shadow-2xl" look.
        soft: '0 1px 2px 0 hsl(220 14% 7% / 0.04), 0 1px 1px 0 hsl(220 14% 7% / 0.03)',
        elevated: '0 4px 14px -4px hsl(220 14% 7% / 0.08), 0 2px 6px -2px hsl(220 14% 7% / 0.04)',
        ring: '0 0 0 1px hsl(var(--border)), 0 1px 2px hsl(220 14% 7% / 0.03)',
        brand:
          '0 1px 2px 0 hsl(var(--brand-forest) / 0.18), 0 8px 24px -10px hsl(var(--brand-forest) / 0.35)',
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        'fade-in': { from: { opacity: '0' }, to: { opacity: '1' } },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-ring': {
          '0%': { boxShadow: '0 0 0 0 hsl(var(--brand-teal) / 0.45)' },
          '70%': { boxShadow: '0 0 0 12px hsl(var(--brand-teal) / 0)' },
          '100%': { boxShadow: '0 0 0 0 hsl(var(--brand-teal) / 0)' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fade-in 200ms ease-out',
        'slide-up': 'slide-up 240ms cubic-bezier(0.16, 1, 0.3, 1)',
        'pulse-ring': 'pulse-ring 1.8s cubic-bezier(0.66, 0, 0, 1) infinite',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
}

export default config
