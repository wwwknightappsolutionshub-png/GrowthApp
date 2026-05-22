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

export function resolvePublicBookingSchema(raw: BookingFormPayload | null | undefined): FormSchema {
  const fields = raw?.fields
  if (Array.isArray(fields) && fields.length > 0) {
    return { version: raw?.version ?? 1, fields: fields as FormSchema['fields'] }
  }
  return DEFAULT_PUBLIC_BOOKING_SCHEMA
}
