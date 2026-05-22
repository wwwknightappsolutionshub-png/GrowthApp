'use client'

import { Plus, Trash2, GripVertical } from 'lucide-react'
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { cn } from '@/lib/utils'

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
  { value: 'service', label: 'Service picker' },
  { value: 'slot', label: 'Time slot picker' },
]

function isTypeLocked(field: FormFieldDef, allowSystemEdit: boolean): boolean {
  if (allowSystemEdit) return false
  if (!field.system) return false
  return field.id === 'service_id' || field.id === 'slot_id' || field.type === 'service' || field.type === 'slot'
}

function isIdLocked(field: FormFieldDef, allowSystemEdit: boolean): boolean {
  return Boolean(field.system && !allowSystemEdit)
}

const inputClass =
  'w-full border border-brand-forest-600 rounded-lg px-3 py-2 bg-brand-forest-800 text-white text-sm placeholder:text-brand-teal-100/40 focus:ring-2 focus:ring-brand-teal-500/40 focus:border-brand-teal-500 [&>option]:bg-white [&>option]:text-slate-900'
const labelClass = 'block text-xs font-medium text-brand-teal-100/80 mb-1'

type Props = {
  schema: FormSchema
  onChange: (schema: FormSchema) => void
  allowSystemEdit?: boolean
}

type SortableFieldProps = {
  field: FormFieldDef
  index: number
  allowSystemEdit: boolean
  onUpdate: (index: number, patch: Partial<FormFieldDef>) => void
  onRemove: (index: number) => void
}

function SortableFieldRow({ field, index, allowSystemEdit, onUpdate, onRemove }: SortableFieldProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: field.id,
  })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={cn(
        'rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-4 space-y-3',
        isDragging && 'z-50 shadow-lg ring-2 ring-brand-teal-500/50 opacity-95',
      )}
    >
      <div className="flex items-start gap-2">
        <button
          type="button"
          className="flex shrink-0 cursor-grab touch-none items-center px-0.5 text-brand-teal-100/50 hover:text-brand-teal-200 active:cursor-grabbing mt-2"
          {...attributes}
          {...listeners}
          aria-label={`Drag to reorder ${field.label}`}
        >
          <GripVertical className="w-5 h-5" />
        </button>
        <div className="flex-1 grid gap-3 sm:grid-cols-2">
          <div>
            <label className={labelClass}>Field ID</label>
            <input
              className={inputClass}
              value={field.id}
              disabled={isIdLocked(field, allowSystemEdit)}
              onChange={(e) => onUpdate(index, { id: e.target.value.replace(/\s/g, '_') })}
            />
          </div>
          <div>
            <label className={labelClass}>Type</label>
            <select
              className={inputClass}
              value={field.type}
              disabled={isTypeLocked(field, allowSystemEdit)}
              onChange={(e) => onUpdate(index, { type: e.target.value })}
            >
              {FIELD_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
            {isTypeLocked(field, allowSystemEdit) ? (
              <p className="text-[10px] text-brand-teal-100/50 mt-1">
                Service and slot types are fixed for booking availability.
              </p>
            ) : null}
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass}>Label</label>
            <input
              className={inputClass}
              value={field.label}
              onChange={(e) => onUpdate(index, { label: e.target.value })}
            />
          </div>
          {field.type === 'select' && (
            <div className="sm:col-span-2">
              <label className={labelClass}>Options (comma-separated)</label>
              <input
                className={inputClass}
                value={(field.options || []).join(', ')}
                onChange={(e) =>
                  onUpdate(index, {
                    options: e.target.value
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
              />
            </div>
          )}
          <label className="flex items-center gap-2 text-sm text-brand-teal-100/90 sm:col-span-2">
            <input
              type="checkbox"
              className="rounded border-brand-forest-600 bg-brand-forest-800 text-brand-teal-500"
              checked={!!field.required}
              onChange={(e) => onUpdate(index, { required: e.target.checked })}
            />
            Required
            {field.system ? <span className="text-xs text-brand-teal-300/60">(system field)</span> : null}
          </label>
        </div>
        {(!field.system || allowSystemEdit) && (
          <button
            type="button"
            onClick={() => onRemove(index)}
            className="text-red-300 hover:text-red-200 p-1"
            aria-label="Remove field"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </li>
  )
}

export function BookingFormBuilder({ schema, onChange, allowSystemEdit = false }: Props) {
  const fields = [...(schema.fields || [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0))

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

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

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const oldIndex = fields.findIndex((f) => f.id === active.id)
    const newIndex = fields.findIndex((f) => f.id === over.id)
    if (oldIndex < 0 || newIndex < 0) return
    setFields(arrayMove(fields, oldIndex, newIndex))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-brand-teal-100/70">
          Drag the <GripVertical className="w-3.5 h-3.5 inline -mt-0.5" /> handle to reorder fields.
        </p>
        <button
          type="button"
          onClick={addField}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-forest-700 text-white text-sm font-semibold shrink-0"
        >
          <Plus className="w-4 h-4" />
          Add field
        </button>
      </div>
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={fields.map((f) => f.id)} strategy={verticalListSortingStrategy}>
          <ul className="space-y-3">
            {fields.map((field, index) => (
              <SortableFieldRow
                key={field.id}
                field={field}
                index={index}
                allowSystemEdit={allowSystemEdit}
                onUpdate={updateField}
                onRemove={removeField}
              />
            ))}
          </ul>
        </SortableContext>
      </DndContext>
    </div>
  )
}
