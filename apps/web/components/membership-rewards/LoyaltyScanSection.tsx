'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { CheckCircle2, Loader2, QrCode, ScanLine } from 'lucide-react'
import { toast } from 'sonner'

import { membershipRewards } from '@/lib/api-client'

type ScanResult = {
  scan_id: string
  customer_id: string
  customer_name: string | null
  points_awarded: number
  points_balance: number
  tier_code: string
  message: string
}

export function LoyaltyScanSection() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [payload, setPayload] = useState('')
  const [lastResult, setLastResult] = useState<ScanResult | null>(null)
  const [cameraActive, setCameraActive] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const detectTimerRef = useRef<number | null>(null)

  const scan = useMutation({
    mutationFn: (value: string) => membershipRewards.scanQr(value.trim()).then((r) => r.data),
    onSuccess: (data) => {
      setLastResult(data)
      setPayload('')
      toast.success(data.message)
      inputRef.current?.focus()
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail ?? 'Scan failed')
      setPayload('')
      inputRef.current?.focus()
    },
  })

  const submitPayload = useCallback(
    (value: string) => {
      const trimmed = value.trim()
      if (!trimmed || scan.isPending) return
      scan.mutate(trimmed)
    },
    [scan],
  )

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const stopCamera = useCallback(() => {
    if (detectTimerRef.current) {
      window.clearInterval(detectTimerRef.current)
      detectTimerRef.current = null
    }
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    setCameraActive(false)
  }, [])

  useEffect(() => () => stopCamera(), [stopCamera])

  async function startCamera() {
    if (typeof window === 'undefined') return
    const Detector = (window as Window & { BarcodeDetector?: new (opts: { formats: string[] }) => {
      detect: (source: HTMLVideoElement) => Promise<Array<{ rawValue: string }>>
    } }).BarcodeDetector
    if (!Detector || !navigator.mediaDevices?.getUserMedia) {
      toast.message('Camera scan unavailable', {
        description: 'Use a USB scanner or paste the QR payload manually.',
      })
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setCameraActive(true)

      const detector = new Detector({ formats: ['qr_code'] })
      detectTimerRef.current = window.setInterval(async () => {
        if (!videoRef.current || scan.isPending) return
        try {
          const codes = await detector.detect(videoRef.current)
          const hit = codes.find((c) => c.rawValue?.includes('cf-loyalty'))
          if (hit?.rawValue) {
            stopCamera()
            submitPayload(hit.rawValue)
          }
        } catch {
          /* ignore frame errors */
        }
      }, 500)
    } catch {
      toast.error('Could not access camera')
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white">Scan member QR</h2>
        <p className="mt-1 text-sm text-slate-400">
          Scan a customer&apos;s wallet QR to check them in and award visit points. USB barcode
          scanners work when this field is focused.
        </p>
      </div>

      <div className="rounded-xl border border-white/10 bg-white/5 p-5 space-y-4">
        <label className="block text-xs font-medium uppercase tracking-wide text-slate-400">
          QR payload
        </label>
        <input
          ref={inputRef}
          type="text"
          value={payload}
          onChange={(e) => setPayload(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submitPayload(payload)
          }}
          placeholder="Scan or paste cf-loyalty:…"
          className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-3 text-sm text-white placeholder:text-slate-500 focus:border-brand-teal-500 focus:outline-none focus:ring-2 focus:ring-brand-teal-500/30"
          autoComplete="off"
          disabled={scan.isPending}
        />

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => submitPayload(payload)}
            disabled={!payload.trim() || scan.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
          >
            {scan.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ScanLine className="h-4 w-4" />
            )}
            Process scan
          </button>
          {cameraActive ? (
            <button
              type="button"
              onClick={stopCamera}
              className="inline-flex items-center gap-2 rounded-lg border border-white/15 px-4 py-2 text-sm text-slate-200 hover:bg-white/5"
            >
              Stop camera
            </button>
          ) : (
            <button
              type="button"
              onClick={() => void startCamera()}
              className="inline-flex items-center gap-2 rounded-lg border border-white/15 px-4 py-2 text-sm text-slate-200 hover:bg-white/5"
            >
              <QrCode className="h-4 w-4" />
              Use camera
            </button>
          )}
        </div>

        {cameraActive ? (
          <video
            ref={videoRef}
            className="aspect-video w-full rounded-lg border border-white/10 bg-black object-cover"
            muted
            playsInline
          />
        ) : null}
      </div>

      {lastResult ? (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/30 p-5">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
            <div className="space-y-1 text-sm">
              <p className="font-semibold text-white">{lastResult.customer_name ?? 'Member'}</p>
              <p className="text-emerald-100/90">{lastResult.message}</p>
              <p className="text-slate-300">
                Balance: <span className="font-medium text-white">{lastResult.points_balance}</span>{' '}
                pts · {lastResult.tier_code} tier
              </p>
              {lastResult.points_awarded > 0 ? (
                <p className="text-emerald-300">+{lastResult.points_awarded} visit points</p>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
