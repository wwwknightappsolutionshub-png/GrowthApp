'use client'

import { Plus, Trash2, GripVertical } from 'lucide-react'

export type FormFieldDef = {
  id: string
  type: string
  label: string
  required?: boolean
  order?: number
  system?: boolean
  options?: string[]
  placeholder?: string
  hidden_when?: string
}

export type FormSchema = {
  version: number
  fields: FormFieldDef[]
}

const FIELD_TYPES = [
  { value: 'text', label: 'Text' },
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone' },
  { value: 'textarea', label: 'Long text' },
  { value: 'select', label: 'Dropdown' },
  { value: 'checkbox', label: 'Checkbox' },
  { value: 'date', label: 'Date' },
  { value: 'file', label: 'File link' },
]

const inputClass =
  'w-full border border-brand-forest-700 rounded-lg px-3 py-2 bg-brand-forest-900 text-white text-sm'
const labelClass = 'block text-xs font-medium text-brand-teal-100/70 mb-1'

type Props = {
  schema: FormSchema
  onChange: (schema: FormSchema) => void
  allowSystemEdit?: boolean
}

export function BookingFormBuilder({ schema, onChange, allowSystemEdit = false }: Props) {
  const fields = [...(schema.fields || [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0))

  const setFields = (next: FormFieldDef[]) => {
    onChange({
      version: schema.version || 1,
      fields: next.map((f, i) => ({ ...f, order: i })),
    })
  }

  const updateField = (index: number, patch: Partial<FormFieldDef>) => {
    const next = fields.map((f, i) => (i === index ? { ...f, ...patch } : f))
    setFields(next)
  }

  const removeField = (index: number) => {
    const f = fields[index]
    if (f.system && !allowSystemEdit) return
    setFields(fields.filter((_, i) => i !== index))
  }

  const addField = () => {
    const id = `custom_${Date.now()}`
    setFields([
      ...fields,
      {
        id,
        type: 'text',
        label: 'New question',
        required: false,
        order: fields.length,
      },
    ])
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-brand-teal-100/70">
          Drag order by sequence. System fields power booking + CRM.
        </p>
        <button
          type="button"
          onClick={addField}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-forest-700 text-white text-sm font-semibold"
        >
          <Plus className="w-4 h-4" />
          Add field
        </button>
      </div>
      <ul className="space-y-3">
        {fields.map((field, index) => (
          <li
            key={field.id}
            className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-4 space-y-3"
          >
            <div className="flex items-start gap-2">
              <GripVertical className="w-4 h-4 text-brand-teal-100/40 mt-2 shrink-0" />
              <div className="flex-1 grid gap-3 sm:grid-cols-2">
                <div>
                  <label className={labelClass}>Field ID</label>
                  <input
                    className={inputClass}
                    value={field.id}
                    disabled={field.system && !allowSystemEdit}
                    onChange={(e) => updateField(index, { id: e.target.value.replace(/\s/g, '_') })}
                  />
                </div>
                <div>
                  <label className={labelClass}>Type</label>
                  <select
                    className={inputClass}
                    value={field.type}
                    disabled={field.system && !allowSystemEdit}
                    onChange={(e) => updateField(index, { type: e.target.value })}
                  >
                    {FIELD_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                    {field.system && (
                      <>
                        <option value="service">Service picker</option>
                        <option value="slot">Slot picker</option>
                      </>
                    )}
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className={labelClass}>Label</label>
                  <input
                    className={inputClass}
                    value={field.label}
                    onChange={(e) => updateField(index, { label: e.target.value })}
                  />
                </div>
                {field.type === 'select' && (
                  <div className="sm:col-span-2">
                    <label className={labelClass}>Options (comma-separated)</label>
                    <input
                      className={inputClass}
                      value={(field.options || []).join(', ')}
                      onChange={(e) =>
                        updateField(index, {
                          options: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                        })
                      }
                    />
                  </div>
                )}
                <label className="flex items-center gap-2 text-sm text-brand-teal-100/80 sm:col-span-2">
                  <input
                    type="checkbox"
                    checked={!!field.required}
                    onChange={(e) => updateField(index, { required: e.target.checked })}
                  />
                  Required
                  {field.system ? (
                    <span className="text-xs text-brand-teal-300/60">(system field)</span>
                  ) : null}
                </label>
              </div>
              {(!field.system || allowSystemEdit) && (
                <button
                  type="button"
                  onClick={() => removeField(index)}
                  className="text-red-300 hover:text-red-200 p-1"
                  aria-label="Remove field"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
