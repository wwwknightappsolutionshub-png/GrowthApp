'use client'

import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { publicBooking } from '@/lib/api-client'
import { formatCurrency } from '@/lib/utils'
import type { FormFieldDef, FormSchema } from './BookingFormBuilder'

const fieldClass =
  'w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-emerald-600/30 focus:border-emerald-700'

type Service = { id: string; name: string; duration_minutes?: number; deposit_pence?: number }
type Slot = { id: string; date: string; start: string }

type Props = {
  slug: string
  schema: FormSchema
  services: Service[]
  depositEnabled?: boolean
  defaultDepositPence?: number
  accent: string
  onSubmit: (payload: Record<string, unknown>) => void
  isPending?: boolean
}

export function DynamicPublicBookingForm({
  slug,
  schema,
  services,
  depositEnabled,
  defaultDepositPence = 0,
  accent,
  onSubmit,
  isPending,
}: Props) {
  const [values, setValues] = useState<Record<string, string>>({})

  const fields = useMemo(
    () => [...(schema.fields || [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    [schema],
  )

  const serviceId = values.service_id || ''
  const { data: availability } = useQuery({
    queryKey: ['public-booking-availability', slug, serviceId],
    queryFn: () =>
      publicBooking.availability(slug, { service_id: serviceId || undefined }).then((r) => r.data),
    enabled: !!slug,
  })

  const slots: Slot[] = availability?.slots ?? []
  const selectedService = services.find((s) => s.id === serviceId)
  const depositPence = useMemo(() => {
    if (!depositEnabled) return 0
    const svc = selectedService?.deposit_pence
    if (typeof svc === 'number' && svc > 0) return svc
    return defaultDepositPence
  }, [depositEnabled, selectedService, defaultDepositPence])

  const set = (id: string, v: string) => setValues((prev) => ({ ...prev, [id]: v }))

  const hidden = (f: FormFieldDef) => {
    if (f.hidden_when && values[f.hidden_when]) return true
    return false
  }

  const validate = (): boolean => {
    for (const f of fields) {
      if (hidden(f) || f.type === 'slot' || f.type === 'service') continue
      if (f.required && !String(values[f.id] || '').trim()) return false
    }
    if (fields.some((f) => f.type === 'slot' || f.id === 'slot_id') && !values.slot_id) {
      const hasManual = values.booking_date && values.start_time
      if (!hasManual && slots.length > 0) return false
    }
    return true
  }

  const handleSubmit = () => {
    const payload: Record<string, unknown> = { ...values, channel: 'widget' }
    if (values.slot_id) {
      const slot = slots.find((s) => s.id === values.slot_id)
      if (slot) {
        payload.booking_date = slot.date
        payload.start_time = slot.start?.slice(0, 5)
      }
    }
    for (const f of fields) {
      if (!f.system && f.type !== 'service' && f.type !== 'slot') {
        payload[f.id] = values[f.id] ?? ''
      }
    }
    onSubmit(payload)
  }

  return (
    <div className="space-y-4">
      {fields.map((f) => {
        if (hidden(f)) return null
        if (f.type === 'service' || f.id === 'service_id') {
          if (!services.length) return null
          return (
            <div key={f.id}>
              <label className="block text-xs font-medium text-slate-600 mb-1">{f.label}</label>
              <select
                className={fieldClass}
                value={values.service_id || ''}
                onChange={(e) => set('service_id', e.target.value)}
              >
                <option value="">Select service</option>
                {services.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
          )
        }
        if (f.type === 'slot' || f.id === 'slot_id') {
          if (slots.length > 0) {
            return (
              <div key={f.id}>
                <label className="block text-xs font-medium text-slate-600 mb-1">{f.label}</label>
                <select
                  className={fieldClass}
                  value={values.slot_id || ''}
                  onChange={(e) => set('slot_id', e.target.value)}
                >
                  <option value="">Choose a time *</option>
                  {slots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.date} {s.start?.slice(0, 5)}
                    </option>
                  ))}
                </select>
              </div>
            )
          }
          return null
        }
        if (f.id === 'booking_date' && slots.length > 0) return null
        if (f.id === 'start_time' && slots.length > 0) return null

        const common = {
          className: fieldClass,
          value: values[f.id] || '',
          onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
            set(f.id, e.target.value),
        }

        return (
          <div key={f.id}>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              {f.label}
              {f.required ? ' *' : ''}
            </label>
            {f.type === 'textarea' ? (
              <textarea rows={3} {...common} />
            ) : f.type === 'select' ? (
              <select {...common}>
                <option value="">Select…</option>
                {(f.options || []).map((o) => (
                  <option key={o} value={o}>
                    {o}
                  </option>
                ))}
              </select>
            ) : f.type === 'checkbox' ? (
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={values[f.id] === 'true'}
                  onChange={(e) => set(f.id, e.target.checked ? 'true' : '')}
                />
                {f.placeholder || 'Yes'}
              </label>
            ) : (
              <input
                type={f.type === 'email' ? 'email' : f.type === 'phone' ? 'tel' : f.type === 'date' ? 'date' : 'text'}
                placeholder={f.placeholder}
                {...common}
              />
            )}
          </div>
        )
      })}

      {depositPence > 0 && (
        <p className="text-xs text-slate-600 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">
          Deposit <strong>{formatCurrency(depositPence)}</strong> may be required to secure your slot.
        </p>
      )}

      <button
        type="button"
        disabled={isPending || !validate()}
        onClick={handleSubmit}
        className="w-full py-3.5 rounded-xl text-white font-semibold text-sm disabled:opacity-50 shadow-md"
        style={{ backgroundColor: accent }}
      >
        {isPending ? 'Submitting…' : depositPence > 0 ? 'Confirm & secure slot' : 'Confirm booking'}
      </button>
    </div>
  )
}
