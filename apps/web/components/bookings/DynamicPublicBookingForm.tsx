'use client'

import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { publicBooking } from '@/lib/api-client'
import { formatCurrency } from '@/lib/utils'
import { mergePublicBookingFields } from '@/lib/booking-form-defaults'
import { PUBLIC_FIELD_CLASS, PUBLIC_LABEL_CLASS } from '@/lib/public-booking-ui'
import type { FormFieldDef, FormSchema } from './BookingFormBuilder'

const fieldClass = PUBLIC_FIELD_CLASS

const CORE_IDS = new Set([
  'customer_name',
  'customer_email',
  'customer_phone',
  'booking_date',
  'start_time',
  'service_description',
  'service_id',
  'slot_id',
])

type Service = { id: string; name: string; duration_minutes?: number; deposit_pence?: number }
type Slot = { id: string; date: string; start: string }

type Props = {
  slug: string
  schema: FormSchema
  services: Service[]
  depositEnabled?: boolean
  defaultDepositPence?: number
  accent: string
  loyaltyProgramAvailable?: boolean
  loyaltyProgramLabel?: string
  onSubmit: (payload: Record<string, unknown>) => void
  isPending?: boolean
}

function labelFor(fieldsById: Record<string, FormFieldDef>, id: string, fallback: string) {
  return fieldsById[id]?.label || fallback
}

export function DynamicPublicBookingForm({
  slug,
  schema,
  services,
  depositEnabled,
  defaultDepositPence = 0,
  accent,
  loyaltyProgramAvailable = false,
  loyaltyProgramLabel = 'Join our rewards program — earn points on every visit',
  onSubmit,
  isPending,
}: Props) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [joinLoyalty, setJoinLoyalty] = useState(true)

  const fields = useMemo(() => mergePublicBookingFields(schema), [schema])
  const fieldsById = useMemo(() => Object.fromEntries(fields.map((f) => [f.id, f])), [fields])
  const customFields = useMemo(
    () => fields.filter((f) => f.id && !CORE_IDS.has(f.id)),
    [fields],
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

  const validate = (): boolean => {
    if (!String(values.customer_name || '').trim()) return false
    const hasSlot = Boolean(String(values.slot_id || '').trim())
    const hasManual = Boolean(values.booking_date?.trim() && values.start_time?.trim())
    if (slots.length > 0 && !hasSlot && !hasManual) return false
    if (slots.length === 0 && !hasManual) return false
    return true
  }

  const handleSubmit = () => {
    const payload: Record<string, unknown> = { ...values, channel: 'widget' }
    if (loyaltyProgramAvailable) {
      payload.join_loyalty_program = joinLoyalty
    }
    if (values.slot_id) {
      const slot = slots.find((s) => s.id === values.slot_id)
      if (slot) {
        payload.booking_date = slot.date
        payload.start_time = slot.start?.slice(0, 5)
      }
    }
    for (const f of customFields) {
      payload[f.id] = values[f.id] ?? ''
    }
    onSubmit(payload)
  }

  const showService = Boolean(fieldsById.service_id) && services.length > 0
  const showSlotPicker = Boolean(fieldsById.slot_id) && slots.length > 0
  const hideManualDateTime = Boolean(String(values.slot_id || '').trim())

  return (
    <div className="space-y-4">
      <div>
        <label className={PUBLIC_LABEL_CLASS}>
          {labelFor(fieldsById, 'customer_name', 'Your name')} *
        </label>
        <input
          className={fieldClass}
          required
          value={values.customer_name || ''}
          onChange={(e) => set('customer_name', e.target.value)}
        />
      </div>

      <div>
        <label className={PUBLIC_LABEL_CLASS}>
          {labelFor(fieldsById, 'customer_email', 'Email')}
        </label>
        <input
          className={fieldClass}
          type="email"
          value={values.customer_email || ''}
          onChange={(e) => set('customer_email', e.target.value)}
        />
      </div>

      <div>
        <label className={PUBLIC_LABEL_CLASS}>
          {labelFor(fieldsById, 'customer_phone', 'Phone')}
        </label>
        <input
          className={fieldClass}
          type="tel"
          value={values.customer_phone || ''}
          onChange={(e) => set('customer_phone', e.target.value)}
        />
      </div>

      {showService ? (
        <div>
          <label className={PUBLIC_LABEL_CLASS}>
            {labelFor(fieldsById, 'service_id', 'Service')}
          </label>
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
      ) : null}

      {showSlotPicker ? (
        <div>
          <label className={PUBLIC_LABEL_CLASS}>
            {labelFor(fieldsById, 'slot_id', 'Available time')} *
          </label>
          <select
            className={fieldClass}
            value={values.slot_id || ''}
            onChange={(e) => set('slot_id', e.target.value)}
          >
            <option value="">Choose a time</option>
            {slots.map((s) => (
              <option key={s.id} value={s.id}>
                {s.date} {s.start?.slice(0, 5)}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      {!hideManualDateTime ? (
        <>
          <div>
            <label className={PUBLIC_LABEL_CLASS}>
              {labelFor(fieldsById, 'booking_date', 'Preferred date')} *
            </label>
            <input
              className={fieldClass}
              type="date"
              value={values.booking_date || ''}
              onChange={(e) => set('booking_date', e.target.value)}
            />
          </div>
          <div>
            <label className={PUBLIC_LABEL_CLASS}>
              {labelFor(fieldsById, 'start_time', 'Preferred time')} *
            </label>
            <input
              className={fieldClass}
              type="time"
              value={values.start_time || ''}
              onChange={(e) => set('start_time', e.target.value)}
            />
          </div>
        </>
      ) : null}

      <div>
        <label className={PUBLIC_LABEL_CLASS}>
          {labelFor(fieldsById, 'service_description', 'What do you need?')}
        </label>
        <textarea
          className={fieldClass}
          rows={3}
          value={values.service_description || ''}
          onChange={(e) => set('service_description', e.target.value)}
        />
      </div>

      {customFields.map((f) => {
        const common = {
          className: fieldClass,
          value: values[f.id] || '',
          onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
            set(f.id, e.target.value),
        }
        return (
          <div key={f.id}>
            <label className={PUBLIC_LABEL_CLASS}>
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
            ) : (
              <input
                type={
                  f.type === 'email' ? 'email' : f.type === 'phone' ? 'tel' : f.type === 'date' ? 'date' : 'text'
                }
                placeholder={f.placeholder}
                {...common}
              />
            )}
          </div>
        )
      })}

      {depositPence > 0 ? (
        <p className="text-xs text-slate-600 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">
          Deposit <strong>{formatCurrency(depositPence)}</strong> may be required to secure your slot.
        </p>
      ) : null}

      {loyaltyProgramAvailable ? (
        <label className="flex items-start gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700 cursor-pointer">
          <input
            type="checkbox"
            checked={joinLoyalty}
            onChange={(e) => setJoinLoyalty(e.target.checked)}
            className="mt-0.5 rounded border-slate-300"
          />
          <span>{loyaltyProgramLabel}</span>
        </label>
      ) : null}

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
