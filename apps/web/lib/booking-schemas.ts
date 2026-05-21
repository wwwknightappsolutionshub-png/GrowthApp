import { z } from 'zod'

export const publicBookingSchema = z.object({
  customer_name: z.string().min(1).max(255),
  customer_email: z.string().email().optional().or(z.literal('')),
  customer_phone: z.string().max(50).optional(),
  service_description: z.string().max(2000).optional(),
  booking_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  start_time: z.string().regex(/^\d{2}:\d{2}(:\d{2})?$/),
  slot_id: z.string().uuid().optional().nullable(),
  staff_id: z.string().uuid().optional().nullable(),
  service_id: z.string().uuid().optional().nullable(),
  notes: z.string().max(2000).optional(),
  channel: z.string().max(50).optional(),
})

export const bookingSettingsSchema = z.object({
  timezone: z.string().max(64).optional(),
  default_duration_minutes: z.number().int().min(15).max(480).optional(),
  deposit_enabled: z.boolean().optional(),
  default_deposit_pence: z.number().int().min(0).optional(),
  no_show_fee_pence: z.number().int().min(0).optional(),
  service_fee_percent: z.number().min(0).max(100).optional(),
  allow_self_reschedule: z.boolean().optional(),
  allow_self_cancel: z.boolean().optional(),
  min_notice_hours: z.number().int().min(0).max(168).optional(),
  overbooking_allowed: z.boolean().optional(),
  google_pixel_id: z.string().max(100).optional().nullable(),
  meta_pixel_id: z.string().max(100).optional().nullable(),
  widget_primary_color: z.string().max(20).optional().nullable(),
})

export const slotGenerateSchema = z.object({
  staff_id: z.string().uuid().optional().nullable(),
  location_id: z.string().uuid().optional().nullable(),
  from_date: z.string(),
  to_date: z.string(),
  slot_duration_minutes: z.number().int().min(15).max(240).default(60),
  daily_start: z.string().default('09:00'),
  daily_end: z.string().default('17:00'),
  exclude_weekends: z.boolean().default(true),
})

export const staffCreateSchema = z.object({
  name: z.string().min(1).max(255),
  email: z.string().email().optional().or(z.literal('')),
  phone: z.string().max(50).optional(),
  role: z.enum(['staff', 'manager', 'admin']).default('staff'),
})
