'use client'

import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bookings } from '@/lib/api-client'
import { staffCreateSchema, slotGenerateSchema } from '@/lib/booking-schemas'
import { toast } from 'sonner'
import { useState } from 'react'

export default function BookingStaffPage() {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [genFrom, setGenFrom] = useState('')
  const [genTo, setGenTo] = useState('')

  const { data: staffList, isLoading } = useQuery({
    queryKey: ['bookings', 'staff'],
    queryFn: () => bookings.listStaff().then((r) => r.data),
  })

  const createStaff = useMutation({
    mutationFn: () => {
      const body = staffCreateSchema.parse({ name, role: 'staff' })
      return bookings.createStaff(body).then((r) => r.data)
    },
    onSuccess: () => {
      toast.success('Staff added')
      setName('')
      qc.invalidateQueries({ queryKey: ['bookings', 'staff'] })
    },
    onError: () => toast.error('Failed to add staff'),
  })

  const generateSlots = useMutation({
    mutationFn: () => {
      const body = slotGenerateSchema.parse({
        from_date: genFrom,
        to_date: genTo,
        slot_duration_minutes: 60,
      })
      return bookings.generateSlots(body).then((r) => r.data)
    },
    onSuccess: (d) => toast.success(`Created ${d.created} slots`),
    onError: () => toast.error('Slot generation failed'),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">← Bookings</Link>
        <h1 className="text-2xl font-bold text-foreground">Staff & availability</h1>
      </div>
      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-3 max-w-lg">
        <h2 className="font-semibold text-white">Add staff</h2>
        <input className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
        <button type="button" onClick={() => createStaff.mutate()} disabled={!name || createStaff.isPending} className="px-4 py-2 rounded-lg bg-brand-forest-700 text-white text-sm">Add</button>
      </div>
      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-3 max-w-lg">
        <h2 className="font-semibold text-white">Generate slots</h2>
        <input type="date" className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm" value={genFrom} onChange={(e) => setGenFrom(e.target.value)} />
        <input type="date" className="w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm" value={genTo} onChange={(e) => setGenTo(e.target.value)} />
        <button type="button" onClick={() => generateSlots.mutate()} disabled={!genFrom || !genTo} className="px-4 py-2 rounded-lg bg-brand-forest-700 text-white text-sm">Generate</button>
      </div>
      {isLoading ? (
        <p className="text-muted-foreground text-sm">Loading staff…</p>
      ) : (
        <ul className="space-y-2">
          {staffList?.map((s: { id: string; name: string; role: string; is_active: boolean }) => (
            <li key={s.id} className="rounded-lg border border-brand-forest-800 px-4 py-3 text-white text-sm">
              {s.name} <span className="text-brand-teal-100/60">({s.role})</span>
              {!s.is_active && <span className="text-red-400 ml-2">inactive</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
