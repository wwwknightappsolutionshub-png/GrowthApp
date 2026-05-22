'use client'

import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bookings } from '@/lib/api-client'
import { staffCreateSchema, slotGenerateSchema } from '@/lib/booking-schemas'
import { toast } from 'sonner'
import { useState } from 'react'
import { formatDate } from '@/lib/utils'

type StaffRow = {
  id: string
  name: string
  email?: string | null
  phone?: string | null
  address?: string | null
  role: string
  is_active: boolean
  joined_at?: string | null
  created_at?: string | null
}

export default function BookingStaffPage() {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [joined, setJoined] = useState('')
  const [genFrom, setGenFrom] = useState('')
  const [genTo, setGenTo] = useState('')
  const [staffId, setStaffId] = useState('')

  const { data: staffList, isLoading } = useQuery({
    queryKey: ['bookings', 'staff'],
    queryFn: () => bookings.listStaff().then((r) => r.data as StaffRow[]),
  })

  const createStaff = useMutation({
    mutationFn: () => {
      const body = staffCreateSchema.parse({
        name,
        phone: phone || undefined,
        role: 'staff',
      })
      return bookings
        .createStaff({
          ...body,
          address: address || undefined,
          joined_at: joined ? new Date(joined).toISOString() : undefined,
        })
        .then((r) => r.data)
    },
    onSuccess: () => {
      toast.success('Staff added')
      setName('')
      setPhone('')
      setAddress('')
      setJoined('')
      qc.invalidateQueries({ queryKey: ['bookings', 'staff'] })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      const d = err.response?.data?.detail
      toast.error(typeof d === 'string' ? d : 'Failed to add staff')
    },
  })

  const generateSlots = useMutation({
    mutationFn: () => {
      const body = slotGenerateSchema.parse({
        staff_id: staffId || null,
        from_date: genFrom,
        to_date: genTo,
        slot_duration_minutes: 60,
        daily_start: '09:00',
        daily_end: '17:00',
      })
      return bookings.generateSlots(body).then((r) => r.data)
    },
    onSuccess: (d: { created?: number }) => toast.success(`Created ${d.created ?? 0} slots`),
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      const d = err.response?.data?.detail
      toast.error(typeof d === 'string' ? d : 'Slot generation failed')
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">
          ← Bookings
        </Link>
        <h1 className="text-2xl font-bold text-white">Staff roster</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-3">
          <h2 className="font-semibold text-white">Add staff</h2>
          <input
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm"
            placeholder="Full name *"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm"
            placeholder="Phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <input
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm"
            placeholder="Address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
          <label className="block text-xs text-brand-teal-100/70">Join date</label>
          <input
            type="date"
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm"
            value={joined}
            onChange={(e) => setJoined(e.target.value)}
          />
          <button
            type="button"
            onClick={() => createStaff.mutate()}
            disabled={!name.trim() || createStaff.isPending}
            className="px-4 py-2 rounded-lg bg-brand-forest-700 text-white text-sm font-semibold disabled:opacity-50"
          >
            Add staff
          </button>
        </div>

        <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-3">
          <h2 className="font-semibold text-white">Generate availability slots</h2>
          <select
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm"
            value={staffId}
            onChange={(e) => setStaffId(e.target.value)}
          >
            <option value="">Any staff</option>
            {(staffList ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <input
            type="date"
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm"
            value={genFrom}
            onChange={(e) => setGenFrom(e.target.value)}
          />
          <input
            type="date"
            className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm"
            value={genTo}
            onChange={(e) => setGenTo(e.target.value)}
          />
          <button
            type="button"
            onClick={() => generateSlots.mutate()}
            disabled={!genFrom || !genTo || generateSlots.isPending}
            className="px-4 py-2 rounded-lg bg-brand-forest-700 text-white text-sm font-semibold disabled:opacity-50"
          >
            Generate slots
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 overflow-hidden">
        <div className="px-5 py-4 border-b border-brand-forest-800">
          <h2 className="text-sm font-bold text-white">Team directory</h2>
        </div>
        {isLoading ? (
          <p className="p-8 text-center text-sm text-brand-teal-100/60">Loading staff…</p>
        ) : !staffList?.length ? (
          <p className="p-8 text-center text-sm text-brand-teal-100/60">No staff yet — add your first team member.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-brand-forest-800 text-brand-teal-100/60 text-xs uppercase">
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Phone</th>
                  <th className="px-5 py-3">Address</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Joined</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {staffList.map((s) => (
                  <tr key={s.id} className="border-b border-brand-forest-800/80 hover:bg-brand-forest-900">
                    <td className="px-5 py-3 font-medium text-white">{s.name}</td>
                    <td className="px-5 py-3 text-brand-teal-100/80">{s.phone || '—'}</td>
                    <td className="px-5 py-3 text-brand-teal-100/80 max-w-[200px] truncate">
                      {s.address || '—'}
                    </td>
                    <td className="px-5 py-3 capitalize text-brand-teal-100/80">{s.role}</td>
                    <td className="px-5 py-3 text-brand-teal-100/80">
                      {s.joined_at
                        ? formatDate(s.joined_at.slice(0, 10))
                        : s.created_at
                          ? formatDate(s.created_at.slice(0, 10))
                          : '—'}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          s.is_active
                            ? 'bg-brand-teal-500/20 text-brand-teal-200'
                            : 'bg-red-500/20 text-red-300'
                        }`}
                      >
                        {s.is_active ? 'Active' : 'On leave'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
