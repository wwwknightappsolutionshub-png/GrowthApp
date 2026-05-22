'use client'

import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bookings, auth, tenants } from '@/lib/api-client'
import { staffCreateSchema, slotGenerateSchema } from '@/lib/booking-schemas'
import { toast } from 'sonner'
import { useState } from 'react'
import { formatDate } from '@/lib/utils'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'
import { Pencil, Trash2 } from 'lucide-react'

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

const inputClass =
  'w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm'

export default function BookingStaffPage() {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [joined, setJoined] = useState('')
  const [genFrom, setGenFrom] = useState('')
  const [genTo, setGenTo] = useState('')
  const [staffId, setStaffId] = useState('')
  const [editId, setEditId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editPhone, setEditPhone] = useState('')
  const [editActive, setEditActive] = useState(true)
  const [boStaffId, setBoStaffId] = useState('')
  const [boStart, setBoStart] = useState('')
  const [boEnd, setBoEnd] = useState('')
  const [boReason, setBoReason] = useState('')

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data as { full_name?: string }),
  })
  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: () => tenants.get().then((r) => r.data as { name?: string }),
  })

  const { data: staffList, isLoading } = useQuery({
    queryKey: ['bookings', 'staff'],
    queryFn: () => bookings.listStaff().then((r) => r.data as StaffRow[]),
  })

  const { data: blackouts } = useQuery({
    queryKey: ['bookings', 'blackouts'],
    queryFn: () => bookings.listBlackouts().then((r) => r.data),
  })

  const createStaff = useMutation({
    mutationFn: () => {
      const body = staffCreateSchema.parse({ name, phone: phone || undefined, role: 'staff' })
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
      toast.error(err.response?.data?.detail ?? 'Failed to add staff')
    },
  })

  const updateStaff = useMutation({
    mutationFn: () =>
      bookings.updateStaff(editId!, {
        name: editName,
        phone: editPhone || null,
        is_active: editActive,
      }),
    onSuccess: () => {
      toast.success('Staff updated')
      setEditId(null)
      qc.invalidateQueries({ queryKey: ['bookings', 'staff'] })
    },
    onError: () => toast.error('Update failed'),
  })

  const deleteStaff = useMutation({
    mutationFn: (id: string) => bookings.deleteStaff(id),
    onSuccess: () => {
      toast.success('Staff removed')
      qc.invalidateQueries({ queryKey: ['bookings', 'staff'] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Cannot delete staff with future bookings'),
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
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(err.response?.data?.detail ?? 'Slot generation failed'),
  })

  const createBlackout = useMutation({
    mutationFn: () =>
      bookings.createBlackout({
        staff_id: boStaffId || null,
        start_at: new Date(boStart).toISOString(),
        end_at: new Date(boEnd).toISOString(),
        reason: boReason || null,
      }),
    onSuccess: () => {
      toast.success('Blackout saved')
      setBoStart('')
      setBoEnd('')
      setBoReason('')
      qc.invalidateQueries({ queryKey: ['bookings', 'blackouts'] })
    },
    onError: () => toast.error('Blackout failed'),
  })

  const startEdit = (s: StaffRow) => {
    setEditId(s.id)
    setEditName(s.name)
    setEditPhone(s.phone ?? '')
    setEditActive(s.is_active)
  }

  return (
    <div className="space-y-6">
      <TenantWelcomeHeader
        tenantName={tenant?.name}
        userName={me?.full_name}
        subtitle="Staff roster, availability slots, and blackouts"
      />
      <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">
        ← Bookings hub
      </Link>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-3">
          <h2 className="font-semibold text-white">Add staff</h2>
          <input className={inputClass} placeholder="Full name *" value={name} onChange={(e) => setName(e.target.value)} />
          <input className={inputClass} placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <input className={inputClass} placeholder="Address" value={address} onChange={(e) => setAddress(e.target.value)} />
          <label className="block text-xs text-brand-teal-100/70">Join date</label>
          <input type="date" className={inputClass} value={joined} onChange={(e) => setJoined(e.target.value)} />
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
          <select className={inputClass} value={staffId} onChange={(e) => setStaffId(e.target.value)}>
            <option value="">Any staff</option>
            {(staffList ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <input type="date" className={inputClass} value={genFrom} onChange={(e) => setGenFrom(e.target.value)} />
          <input type="date" className={inputClass} value={genTo} onChange={(e) => setGenTo(e.target.value)} />
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

      {editId && (
        <div className="rounded-xl border border-brand-teal-400/30 bg-brand-forest-950 p-6 space-y-3">
          <h2 className="font-semibold text-white">Edit staff</h2>
          <input className={inputClass} value={editName} onChange={(e) => setEditName(e.target.value)} />
          <input className={inputClass} value={editPhone} onChange={(e) => setEditPhone(e.target.value)} />
          <label className="flex items-center gap-2 text-sm text-brand-teal-100/80">
            <input type="checkbox" checked={editActive} onChange={(e) => setEditActive(e.target.checked)} />
            Active on roster
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => updateStaff.mutate()}
              className="px-4 py-2 rounded-lg bg-brand-teal-600 text-white text-sm font-semibold"
            >
              Save
            </button>
            <button type="button" onClick={() => setEditId(null)} className="px-4 py-2 text-sm text-brand-teal-100/70">
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-3">
        <h2 className="font-semibold text-white">Staff blackouts</h2>
        <p className="text-xs text-brand-teal-100/60">Block time when staff are unavailable (leave, training, etc.).</p>
        <select className={inputClass} value={boStaffId} onChange={(e) => setBoStaffId(e.target.value)}>
          <option value="">All staff</option>
          {(staffList ?? []).map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <input type="datetime-local" className={inputClass} value={boStart} onChange={(e) => setBoStart(e.target.value)} />
        <input type="datetime-local" className={inputClass} value={boEnd} onChange={(e) => setBoEnd(e.target.value)} />
        <input className={inputClass} placeholder="Reason" value={boReason} onChange={(e) => setBoReason(e.target.value)} />
        <button
          type="button"
          disabled={!boStart || !boEnd || createBlackout.isPending}
          onClick={() => createBlackout.mutate()}
          className="px-4 py-2 rounded-lg bg-brand-forest-700 text-white text-sm font-semibold disabled:opacity-50"
        >
          Add blackout
        </button>
        <ul className="divide-y divide-brand-forest-800 text-sm">
          {(blackouts ?? []).length === 0 ? (
            <li className="py-3 text-brand-teal-100/50">No blackouts scheduled.</li>
          ) : (
            (blackouts as { id: string; start_at: string; end_at: string; reason?: string }[]).map((b) => (
              <li key={b.id} className="py-2 text-brand-teal-100/80">
                {new Date(b.start_at).toLocaleString('en-GB')} → {new Date(b.end_at).toLocaleString('en-GB')}
                {b.reason ? ` · ${b.reason}` : ''}
              </li>
            ))
          )}
        </ul>
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
                  <th className="px-5 py-3">Joined</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {staffList.map((s) => (
                  <tr key={s.id} className="border-b border-brand-forest-800/80 hover:bg-brand-forest-900">
                    <td className="px-5 py-3 font-medium text-white">{s.name}</td>
                    <td className="px-5 py-3 text-brand-teal-100/80">{s.phone || '—'}</td>
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
                          s.is_active ? 'bg-brand-teal-500/20 text-brand-teal-200' : 'bg-red-500/20 text-red-300'
                        }`}
                      >
                        {s.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right space-x-2">
                      <button type="button" onClick={() => startEdit(s)} className="text-brand-teal-300 hover:text-white">
                        <Pencil className="w-4 h-4 inline" />
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          if (confirm(`Remove ${s.name} from roster?`)) deleteStaff.mutate(s.id)
                        }}
                        className="text-red-300 hover:text-red-200"
                      >
                        <Trash2 className="w-4 h-4 inline" />
                      </button>
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
