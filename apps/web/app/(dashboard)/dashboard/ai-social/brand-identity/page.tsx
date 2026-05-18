'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Image as ImageIcon, Palette, Save, Upload } from 'lucide-react'
import { social } from '@/lib/api-client'
import { toast } from 'sonner'

const TONES = ['friendly', 'professional', 'witty', 'authoritative', 'casual', 'inspirational']

export default function BrandIdentityPage() {
  const [primary, setPrimary] = useState('#2563eb')
  const [secondary, setSecondary] = useState('#f59e0b')
  const [accent, setAccent] = useState('#10b981')
  const [headingFont, setHeadingFont] = useState('Inter')
  const [bodyFont, setBodyFont] = useState('Inter')
  const [tone, setTone] = useState('friendly')
  const [logoUrl, setLogoUrl] = useState('')
  const [logoFileName, setLogoFileName] = useState('')

  const saveMut = useMutation({
    mutationFn: () =>
      social.setBrandIdentity({
        brand_colors: { primary, secondary, accent },
        brand_fonts: { heading: headingFont, body: bodyFont },
        tone_of_voice: tone,
        logo_url: logoUrl || undefined,
      }),
    onSuccess: () => toast.success('Brand identity saved'),
    onError: () => toast.error('Failed to save brand identity'),
  })

  function handleLogoFile(file: File | undefined) {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      toast.error('Choose an image file for your logo')
      return
    }

    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result !== 'string') {
        toast.error('Could not read this logo file')
        return
      }
      setLogoUrl(reader.result)
      setLogoFileName(file.name)
      toast.success('Local logo selected')
    }
    reader.onerror = () => toast.error('Could not read this logo file')
    reader.readAsDataURL(file)
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Palette className="h-6 w-6 text-primary" /> Brand Identity
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Define your brand colours, fonts, tone, and logo. The AI Social engine will use this
          to generate posts that look and sound like you.
        </p>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 space-y-6 shadow-sm">
        <section>
          <h2 className="text-sm font-semibold mb-3 text-foreground">Brand colours</h2>
          <div className="grid grid-cols-3 gap-3">
            <ColorInput label="Primary" value={primary} onChange={setPrimary} />
            <ColorInput label="Secondary" value={secondary} onChange={setSecondary} />
            <ColorInput label="Accent" value={accent} onChange={setAccent} />
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold mb-3 text-foreground">Typography</h2>
          <div className="grid grid-cols-2 gap-3">
            <FontInput label="Heading font" value={headingFont} onChange={setHeadingFont} />
            <FontInput label="Body font" value={bodyFont} onChange={setBodyFont} />
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold mb-3 text-foreground">Tone of voice</h2>
          <div className="flex flex-wrap gap-2">
            {TONES.map((t) => (
              <button
                key={t}
                onClick={() => setTone(t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold border capitalize ${
                  tone === t
                    ? 'bg-primary/10 text-primary border-primary/40'
                    : 'bg-card text-muted-foreground border-border hover:border-foreground/30'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-foreground">Logo</h2>
          <div className="rounded-xl border border-dashed border-brand-forest-300 bg-brand-forest-50/40 p-4">
            <label className="mb-2 flex items-center gap-2 text-sm font-semibold text-brand-forest-800">
              <Upload className="h-4 w-4" />
              Upload logo from local device
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handleLogoFile(e.target.files?.[0])}
              className="block w-full cursor-pointer rounded-lg border border-brand-forest-200 bg-white text-sm text-muted-foreground file:mr-4 file:border-0 file:bg-brand-forest-700 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-brand-forest-foreground hover:file:bg-brand-forest-800"
            />
            <p className="mt-2 text-xs text-brand-forest-700/80">
              Select a logo from your computer, or paste a hosted logo URL below.
            </p>
            {logoFileName && (
              <p className="mt-2 rounded-lg bg-white px-3 py-2 text-xs font-medium text-brand-forest-800">
                Selected: {logoFileName}
              </p>
            )}
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1">
              Logo URL or selected local logo
            </label>
            <input
              value={logoUrl}
              onChange={(e) => {
                setLogoUrl(e.target.value)
                setLogoFileName('')
              }}
              placeholder="https://cdn.yoursite.com/logo.png"
              className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm"
            />
          </div>
          {logoUrl && (
            <div className="flex items-center gap-3 rounded-xl border border-border bg-background p-3">
              <div className="relative flex h-14 w-14 items-center justify-center overflow-hidden rounded-lg bg-brand-forest-50 text-brand-forest-700">
                <img
                  src={logoUrl}
                  alt="Brand logo preview"
                  className="absolute inset-0 z-10 h-full w-full object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
                <ImageIcon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">Logo preview</p>
                <p className="text-xs text-muted-foreground">
                  This logo will be sent with your AI Social brand identity.
                </p>
              </div>
            </div>
          )}
        </section>

        <button
          onClick={() => saveMut.mutate()}
          disabled={saveMut.isPending}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
        >
          <Save className="h-4 w-4" />
          {saveMut.isPending ? 'Saving…' : 'Save brand identity'}
        </button>
      </div>
    </div>
  )
}

function ColorInput({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div>
      <label className="block text-xs text-muted-foreground mb-1">{label}</label>
      <div className="flex gap-2">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="h-9 w-12 rounded border border-border bg-background"
        />
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 rounded-lg bg-background border border-border px-3 py-2 text-sm font-mono"
        />
      </div>
    </div>
  )
}

function FontInput({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div>
      <label className="block text-xs text-muted-foreground mb-1">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm"
      />
    </div>
  )
}
