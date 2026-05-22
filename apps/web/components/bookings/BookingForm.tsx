'use client'

import { useQuery } from '@tanstack/react-query'
import { bookings, crm } from '@/lib/api-client'

const inputClass =
  'w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm'
const labelClass = 'block text-xs font-medium text-brand-teal-100/70 mb-1'

export type BookingFormValues = {
  customer_name: string
  customer_email: string
  customer_phone: string
  customer_id: string
  service_id: string
  staff_id: string
  slot_id: string
  booking_date: string
  start_time: string
  service_description: string
  notes: string
  status: string
  notify_customer: boolean
}

type Props = {
  values: BookingFormValues
  onChange: (v: BookingFormValues) => void
  showStatus?: boolean
  showNotify?: boolean
}

export function BookingForm({ values, onChange, showStatus, showNotify }: Props) {
  const set = (patch: Partial<BookingFormValues>) => onChange({ ...values, ...patch })

  const { data: services } = useQuery({
    queryKey: ['bookings', 'services'],
    queryFn: () => bookings.listServices().then((r) => r.data),
  })
  const { data: staffList } = useQuery({
    queryKey: ['bookings', 'staff'],
    queryFn: () => bookings.listStaff().then((r) => r.data),
  })
  const { data: slots } = useQuery({
    queryKey: ['bookings', 'slots', values.staff_id],
    queryFn: () =>
      bookings.listSlots({ only_available: true, staff_id: values.staff_id || undefined }).then((r) => r.data),
  })
  const { data: customers } = useQuery({
    queryKey: ['crm', 'customers', 'picker'],
    queryFn: () => crm.listCustomers({ page: 1, page_size: 100 }).then((r) => r.data),
  })

  return (
    <div className="space-y-4">
      <div>
        <label className={labelClass}>Customer name *</label>
        <input className={inputClass} value={values.customer_name} onChange={(e) => set({ customer_name: e.target.value })} />
      </div>
      <div>
        <label className={labelClass}>Link existing customer</label>
        <select className={inputClass} value={values.customer_id} onChange={(e) => set({ customer_id: e.target.value })}>
          <option value="">New contact (use fields below)</option>
          {(customers?.items ?? []).map((c: { id: string; first_name: string; last_name?: string }) => (
            <option key={c.id} value={c.id}>
              {c.first_name} {c.last_name ?? ''}
            </option>
          ))}
        </select>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className={labelClass}>Email</label>
          <input type="email" className={inputClass} value={values.customer_email} onChange={(e) => set({ customer_email: e.target.value })} />
        </div>
        <div>
          <label className={labelClass}>Phone</label>
          <input className={inputClass} value={values.customer_phone} onChange={(e) => set({ customer_phone: e.target.value })} />
        </div>
      </div>
      <div>
        <label className={labelClass}>Service</label>
        <select className={inputClass} value={values.service_id} onChange={(e) => set({ service_id: e.target.value })}>
          <option value="">Select service</option>
          {(services ?? []).map((s: { id: string; name: string }) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>
      <div>
        <label className={labelClass}>Staff</label>
        <select className={inputClass} value={values.staff_id} onChange={(e) => set({ staff_id: e.target.value, slot_id: '' })}>
          <option value="">Any staff</option>
          {(staffList ?? []).map((s: { id: string; name: string }) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className={labelClass}>Date *</label>
          <input type="date" className={inputClass} value={values.booking_date} onChange={(e) => set({ booking_date: e.target.value })} />
        </div>
        <div>
          <label className={labelClass}>Time *</label>
          {(slots ?? []).length > 0 ? (
            <select
              className={inputClass}
              value={values.slot_id}
              onChange={(e) => {
                const slot = (slots as { id: string; slot_date: string; start_time: string }[]).find((s) => s.id === e.target.value)
                set({
                  slot_id: e.target.value,
                  booking_date: slot?.slot_date?.slice(0, 10) ?? values.booking_date,
                  start_time: slot?.start_time?.slice(0, 5) ?? values.start_time,
                })
              }}
            >
              <option value="">Pick slot</option>
              {(slots as { id: string; slot_date: string; start_time: string }[]).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.slot_date} {s.start_time?.slice(0, 5)}
                </option>
              ))}
            </select>
          ) : (
            <input type="time" className={inputClass} value={values.start_time} onChange={(e) => set({ start_time: e.target.value })} />
          )}
        </div>
      </div>
      <div>
        <label className={labelClass}>Description</label>
        <textarea className={inputClass} rows={2} value={values.service_description} onChange={(e) => set({ service_description: e.target.value })} />
      </div>
      <div>
        <label className={labelClass}>Internal notes</label>
        <textarea className={inputClass} rows={2} value={values.notes} onChange={(e) => set({ notes: e.target.value })} />
      </div>
      {showStatus && (
        <div>
          <label className={labelClass}>Status</label>
          <select className={inputClass} value={values.status} onChange={(e) => set({ status: e.target.value })}>
            <option value="confirmed">Confirmed</option>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="no_show">No show</option>
          </select>
        </div>
      )}
      {showNotify && (
        <label className="flex items-center gap-2 text-sm text-brand-teal-100/80">
          <input type="checkbox" checked={values.notify_customer} onChange={(e) => set({ notify_customer: e.target.checked })} />
          Email client when date/time changes
        </label>
      )}
    </div>
  )
}
