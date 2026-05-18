'use client'

import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Check, Code2, Copy, ExternalLink } from 'lucide-react'
import { tenants } from '@/lib/api-client'

type TenantInfo = { id: string; slug: string; name: string; primary_color: string | null }

export default function WidgetEmbedPage() {
  const { data } = useQuery<TenantInfo>({
    queryKey: ['tenant-me'],
    queryFn: () => tenants.get().then((r) => r.data),
  })

  const [copied, setCopied] = useState(false)
  const [label, setLabel] = useState('Get a free quote')
  const [color, setColor] = useState('#2563EB')

  useEffect(() => {
    if (data?.primary_color) setColor(data.primary_color)
  }, [data])

  const slug = data?.slug || 'your-tenant-slug'
  const apiBase =
    typeof window !== 'undefined'
      ? `${window.location.protocol}//${window.location.host}/api/v1`
      : 'https://your-api.example.com/api/v1'
  const widgetSrc = `${apiBase}/public/widget.js`

  const snippet = [
    `<!-- CustomerFlow AI widget -->`,
    `<script src="${widgetSrc}" defer`,
    `        data-tenant="${slug}"`,
    `        data-mode="lead"`,
    `        data-label="${label}"`,
    `        data-color="${color}"></script>`,
  ].join('\n')

  const copy = async () => {
    await navigator.clipboard.writeText(snippet)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <header>
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Code2 className="w-6 h-6 text-blue-600" /> Embeddable widget
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Drop a single <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">&lt;script&gt;</code> tag
          on any website to capture leads straight into CustomerFlow AI.
        </p>
      </header>

      <section className="rounded-xl border bg-card p-5 space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Customise
        </h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-foreground/80 uppercase tracking-wide">
              Button label
            </label>
            <input
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-foreground/80 uppercase tracking-wide">
              Primary colour
            </label>
            <div className="mt-1 flex items-center gap-2">
              <input
                type="color"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="h-10 w-14 rounded border"
              />
              <input
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="flex-1 rounded-md border px-3 py-2 text-sm font-mono"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-xl border bg-card p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Embed snippet
          </h2>
          <button
            onClick={copy}
            className="inline-flex items-center gap-1 text-sm rounded-lg border px-3 py-1.5 hover:bg-gray-50"
          >
            {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
        <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 text-xs overflow-x-auto leading-relaxed font-mono">
{snippet}
        </pre>
        <p className="text-xs text-muted-foreground">
          Paste this snippet just before <code>&lt;/body&gt;</code> on any page. A floating
          button will appear in the bottom-right corner.
        </p>
      </section>

      <section className="rounded-xl border bg-card p-5 space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Live preview
        </h2>
        <p className="text-xs text-muted-foreground">
          The button below is rendered by the live widget JS using the settings above.
        </p>
        <WidgetPreview src={widgetSrc} tenant={slug} label={label} color={color} />
        <p className="text-xs text-gray-400">
          Visit your public lead URL directly:{' '}
          <a
            href={`/p/${slug}/home`}
            target="_blank"
            rel="noreferrer"
            className="text-blue-600 hover:underline inline-flex items-center gap-0.5"
          >
            /p/{slug}/home <ExternalLink className="w-3 h-3" />
          </a>
        </p>
      </section>
    </div>
  )
}

function WidgetPreview({
  src,
  tenant,
  label,
  color,
}: {
  src: string
  tenant: string
  label: string
  color: string
}) {
  // Render in an iframe so the widget's <script> can mount safely without
  // colliding with the dashboard's React tree.
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
    body { font: 14px system-ui; padding: 24px; background: linear-gradient(135deg,#f8fafc,#eef2ff); margin:0; height:100vh; }
    .demo { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
  </style></head><body>
    <div class="demo">
      <h2 style="margin:0 0 8px;font-size:20px;">Your site</h2>
      <p style="color:#666;margin:0 0 12px;">This is what a visitor to your website will see. Click the floating button.</p>
      <p style="color:#666;margin:0;">The form submits straight into your <strong>Leads</strong> inbox.</p>
    </div>
    <script src="${src}" defer
            data-tenant="${tenant}"
            data-label="${label.replace(/"/g, '&quot;')}"
            data-color="${color}"></script>
  </body></html>`
  return (
    <iframe
      title="Widget preview"
      srcDoc={html}
      className="w-full h-72 rounded-lg border"
    />
  )
}
