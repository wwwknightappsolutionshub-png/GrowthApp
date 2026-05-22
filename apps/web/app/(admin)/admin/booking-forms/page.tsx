'use client'

import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { LayoutGrid } from 'lucide-react'
import { toast } from 'sonner'
import { admin } from '@/lib/api-client'
import { BookingFormBuilder, type FormSchema } from '@/components/bookings/BookingFormBuilder'

export default function AdminBookingFormsPage() {
  const qc = useQueryClient()
  const [category, setCategory] = useState('general')
  const [schema, setSchema] = useState<FormSchema>({ version: 1, fields: [] })

  const { data: categories } = useQuery({
    queryKey: ['admin', 'booking-form-categories'],
    queryFn: () => admin.listBookingFormCategories().then((r) => r.data),
  })

  const { data: template, isLoading } = useQuery({
    queryKey: ['admin', 'booking-form', category],
    queryFn: () => admin.getBookingFormTemplate(category).then((r) => r.data),
    enabled: !!category,
  })

  useEffect(() => {
    if (template?.schema) {
      setSchema(template.schema as FormSchema)
    }
  }, [template])

  const save = useMutation({
    mutationFn: () =>
      admin.updateBookingFormTemplate(category, {
        name: template?.name,
        schema,
      }),
    onSuccess: () => {
      toast.success('Template saved')
      qc.invalidateQueries({ queryKey: ['admin', 'booking-form', category] })
    },
    onError: () => toast.error('Save failed'),
  })

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <LayoutGrid className="w-7 h-7 text-brand-teal-300" />
          Booking form templates
        </h1>
        <p className="text-sm text-brand-teal-100/65 mt-1">
          Default public booking forms per business category. Tenants can customise their copy.
        </p>
      </div>

      <select
        className="rounded-lg border border-brand-forest-700 bg-brand-forest-950 px-3 py-2 text-sm text-white max-w-xs"
        value={category}
        onChange={(e) => setCategory(e.target.value)}
      >
        {(categories?.categories ?? ['general']).map((c: string) => (
          <option key={c} value={c}>
            {c.replace(/_/g, ' ')}
          </option>
        ))}
      </select>

      {isLoading ? (
        <p className="text-sm text-brand-teal-100/60">Loading…</p>
      ) : (
        <>
          <BookingFormBuilder schema={schema} onChange={setSchema} allowSystemEdit />
          <button
            type="button"
            onClick={() => save.mutate()}
            disabled={save.isPending}
            className="px-5 py-2.5 rounded-lg bg-brand-teal-600 text-white font-semibold text-sm disabled:opacity-50"
          >
            Save category template
          </button>
        </>
      )}
    </div>
  )
}
