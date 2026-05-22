import type { FormSchema } from '@/components/bookings/BookingFormBuilder'

/** Mirrors API default_schema_for_category — used when widget schema is missing or empty. */
export const DEFAULT_PUBLIC_BOOKING_SCHEMA: FormSchema = {
  version: 1,
  fields: [
    { id: 'customer_name', type: 'text', label: 'Your name', required: true, order: 0, system: true },
    { id: 'customer_email', type: 'email', label: 'Email', required: true, order: 1, system: true },
    { id: 'customer_phone', type: 'phone', label: 'Phone', required: false, order: 2, system: true },
    { id: 'service_id', type: 'service', label: 'Service', required: false, order: 3, system: true },
    { id: 'slot_id', type: 'slot', label: 'Available time', required: false, order: 4, system: true },
    {
      id: 'booking_date',
      type: 'date',
      label: 'Preferred date',
      required: false,
      order: 5,
      system: true,
      hidden_when: 'slot_id',
    },
    {
      id: 'start_time',
      type: 'text',
      label: 'Preferred time',
      required: false,
      order: 6,
      system: true,
      hidden_when: 'slot_id',
    },
    {
      id: 'service_description',
      type: 'textarea',
      label: 'What do you need?',
      required: false,
      order: 7,
      system: true,
    },
  ],
}

export type BookingFormPayload = {
  version?: number
  fields?: unknown[]
}

/** Normalize GET /bookings/form or admin template API payloads. */
export function schemaFromFormApi(data: Record<string, unknown> | null | undefined): FormSchema | null {
  if (!data) return null
  const raw = (data.schema ?? data.form_schema) as BookingFormPayload | undefined
  if (!raw || typeof raw !== 'object') return null
  return resolvePublicBookingSchema(raw)
}

export function resolvePublicBookingSchema(raw: BookingFormPayload | null | undefined): FormSchema {
  const fields = raw?.fields
  if (Array.isArray(fields) && fields.length > 0) {
    return { version: raw?.version ?? 1, fields: fields as FormSchema['fields'] }
  }
  return DEFAULT_PUBLIC_BOOKING_SCHEMA
}

/** Read booking form JSON from widget API (supports legacy/alternate keys). */
export function extractBookingFormFromWidget(
  widget: Record<string, unknown> | null | undefined,
): BookingFormPayload | undefined {
  if (!widget) return undefined
  const direct = widget.booking_form ?? widget.bookingForm
  if (direct && typeof direct === 'object' && !Array.isArray(direct)) {
    return direct as BookingFormPayload
  }
  const nested = widget.schema ?? widget.form_schema
  if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
    return nested as BookingFormPayload
  }
  return undefined
}

/** Merge tenant/category fields onto platform defaults so core inputs always render. */
export function mergePublicBookingFields(schema: FormSchema): FormSchema['fields'] {
  const byId = new Map<string, FormSchema['fields'][number]>()
  for (const f of DEFAULT_PUBLIC_BOOKING_SCHEMA.fields) {
    byId.set(f.id, { ...f })
  }
  for (const f of schema.fields || []) {
    if (!f?.id) continue
    const prev = byId.get(f.id)
    byId.set(f.id, prev ? { ...prev, ...f } : f)
  }
  return Array.from(byId.values()).sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
}
