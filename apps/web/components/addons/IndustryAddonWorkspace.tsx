'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { AddonGate } from '@/components/addons/AddonGate'
import { industryAddons } from '@/lib/api-client'
import { apiClient } from '@/lib/api-client'

type Tab = 'booking' | 'billing' | 'crm'

export function IndustryAddonWorkspace({ tab }: { tab: Tab }) {
  const qc = useQueryClient()
  const statusQ = useQuery({
    queryKey: ['addons', 'status'],
    queryFn: async () => (await industryAddons.status()).data,
  })
  const vertical = statusQ.data?.vertical ?? 'salon'
  const isSalon = vertical === 'salon'
  const isGarage = vertical === 'garage'

  const grantMut = useMutation({
    mutationFn: () => apiClient.post('/addons/dev/grant-all'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['addons'] }),
  })

  const setVerticalMut = useMutation({
    mutationFn: (v: 'salon' | 'garage') => industryAddons.setVertical(v),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['addons'] }),
  })

  const feature =
    tab === 'booking' ? 'industry_booking' : tab === 'billing' ? 'industry_billing' : 'industry_crm'

  return (
    <AddonGate feature={feature}>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-4">
          <span className="text-sm text-slate-300">
            Vertical: <strong className="capitalize text-white">{vertical}</strong>
          </span>
          <button
            type="button"
            onClick={() => setVerticalMut.mutate('salon')}
            className="rounded-lg border border-white/20 px-3 py-1 text-xs text-white hover:bg-white/10"
          >
            Salon
          </button>
          <button
            type="button"
            onClick={() => setVerticalMut.mutate('garage')}
            className="rounded-lg border border-white/20 px-3 py-1 text-xs text-white hover:bg-white/10"
          >
            Garage
          </button>
          <button
            type="button"
            onClick={() => grantMut.mutate()}
            className="rounded-lg bg-brand-teal-600 px-3 py-1 text-xs font-medium text-white hover:bg-brand-teal-500"
          >
            Grant all add-ons (dev)
          </button>
        </div>

        {tab === 'booking' && <BookingPanel isSalon={isSalon} isGarage={isGarage} />}
        {tab === 'billing' && <BillingPanel isSalon={isSalon} isGarage={isGarage} />}
        {tab === 'crm' && <CrmPanel isSalon={isSalon} isGarage={isGarage} />}
      </div>
    </AddonGate>
  )
}

function BookingPanel({ isSalon, isGarage }: { isSalon: boolean; isGarage: boolean }) {
  const [bookingId, setBookingId] = useState('')
  const [serviceId, setServiceId] = useState('')
  const [result, setResult] = useState<string>('')

  const productsQ = useQuery({
    queryKey: ['addons', 'products'],
    queryFn: async () => (await apiClient.get('/addons/booking/products')).data,
  })
  const partsQ = useQuery({
    queryKey: ['addons', 'parts'],
    queryFn: async () => (await apiClient.get('/addons/booking/parts')).data,
    enabled: isGarage,
  })
  const vehiclesQ = useQuery({
    queryKey: ['addons', 'vehicles'],
    queryFn: async () => (await apiClient.get('/addons/booking/vehicles')).data,
    enabled: isGarage,
  })

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Section title="Shared tools">
        <Field label="Booking ID" value={bookingId} onChange={setBookingId} />
        <Field label="Service ID" value={serviceId} onChange={setServiceId} />
        <Btn
          label="Staff skill match"
          onClick={async () => {
            const r = await apiClient.get('/addons/booking/staff/match', { params: { service_id: serviceId } })
            setResult(JSON.stringify(r.data, null, 2))
          }}
        />
        <Btn
          label="Gap-fill suggestions (today)"
          onClick={async () => {
            const d = new Date().toISOString().slice(0, 10)
            const r = await apiClient.get('/addons/booking/gap-fill', { params: { target_date: d } })
            setResult(JSON.stringify(r.data, null, 2))
          }}
        />
      </Section>

      {isSalon && (
        <Section title="Salon booking">
          <Btn
            label="List retail products"
            onClick={() => setResult(JSON.stringify(productsQ.data, null, 2))}
          />
          <p className="text-xs text-slate-500">Multi-service sessions, booth allocation, upsells via API.</p>
        </Section>
      )}

      {isGarage && (
        <Section title="Garage booking">
          <Btn
            label="List parts inventory"
            onClick={() => setResult(JSON.stringify(partsQ.data, null, 2))}
          />
          <Btn
            label="List vehicles"
            onClick={() => setResult(JSON.stringify(vehiclesQ.data, null, 2))}
          />
          <Btn
            label="Estimate duration (Ford Focus MOT)"
            onClick={async () => {
              const r = await apiClient.get('/addons/booking/estimate-duration', {
                params: { make: 'Ford', model: 'Focus', service_code: 'mot' },
              })
              setResult(JSON.stringify(r.data, null, 2))
            }}
          />
        </Section>
      )}

      <pre className="col-span-full max-h-64 overflow-auto rounded-lg bg-black/40 p-3 text-xs text-slate-300">
        {result || 'Run an action to see API results…'}
      </pre>
    </div>
  )
}

function BillingPanel({ isSalon, isGarage }: { isSalon: boolean; isGarage: boolean }) {
  const [result, setResult] = useState('')
  const membershipsQ = useQuery({
    queryKey: ['addons', 'memberships'],
    queryFn: async () => (await apiClient.get('/addons/billing/memberships')).data,
    enabled: isSalon,
  })
  const templatesQ = useQuery({
    queryKey: ['addons', 'templates'],
    queryFn: async () => (await apiClient.get('/addons/billing/templates')).data,
    enabled: isGarage,
  })

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {isSalon && (
        <Section title="Salon billing">
          <Btn label="List memberships" onClick={() => setResult(JSON.stringify(membershipsQ.data, null, 2))} />
          <p className="text-xs text-slate-500">Combo invoices, tips, packages, recurring memberships.</p>
        </Section>
      )}
      {isGarage && (
        <Section title="Garage billing">
          <Btn label="List invoice templates" onClick={() => setResult(JSON.stringify(templatesQ.data, null, 2))} />
          <Btn
            label="VIN invoice lookup (demo)"
            onClick={async () => {
              const r = await apiClient.get('/addons/billing/vin/WBA12345678901234/invoices')
              setResult(JSON.stringify(r.data, null, 2))
            }}
          />
          <p className="text-xs text-slate-500">Parts+labor templates, markup rules, warranties.</p>
        </Section>
      )}
      <pre className="col-span-full max-h-64 overflow-auto rounded-lg bg-black/40 p-3 text-xs text-slate-300">
        {result || 'Run an action…'}
      </pre>
    </div>
  )
}

function CrmPanel({ isSalon, isGarage }: { isSalon: boolean; isGarage: boolean }) {
  const [customerId, setCustomerId] = useState('')
  const [vehicleId, setVehicleId] = useState('')
  const [result, setResult] = useState('')

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {isSalon && (
        <Section title="Salon CRM">
          <Field label="Customer ID" value={customerId} onChange={setCustomerId} />
          <Btn
            label="Salon segment tags"
            onClick={async () => {
              const r = await apiClient.get('/addons/crm/salon/segments')
              setResult(JSON.stringify(r.data, null, 2))
            }}
          />
          <Btn
            label="Schedule rebook reminder"
            onClick={async () => {
              const r = await apiClient.post(`/addons/crm/salon/rebook/${customerId}`)
              setResult(JSON.stringify(r.data, null, 2))
            }}
          />
        </Section>
      )}
      {isGarage && (
        <Section title="Garage CRM">
          <Field label="Vehicle ID" value={vehicleId} onChange={setVehicleId} />
          <Field label="Customer ID (scores)" value={customerId} onChange={setCustomerId} />
          <Btn
            label="Vehicle repair history"
            onClick={async () => {
              const r = await apiClient.get(`/addons/crm/garage/vehicles/${vehicleId}/history`)
              setResult(JSON.stringify(r.data, null, 2))
            }}
          />
          <Btn
            label="Run maintenance predictions"
            onClick={async () => {
              const r = await apiClient.post(`/addons/crm/garage/vehicles/${vehicleId}/predictions`)
              setResult(JSON.stringify(r.data, null, 2))
            }}
          />
          <Btn
            label="Refresh CLV scores"
            onClick={async () => {
              const r = await apiClient.post(`/addons/crm/garage/customers/${customerId}/scores`)
              setResult(JSON.stringify(r.data, null, 2))
            }}
          />
        </Section>
      )}
      <pre className="col-span-full max-h-64 overflow-auto rounded-lg bg-black/40 p-3 text-xs text-slate-300">
        {result || 'Run an action…'}
      </pre>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
      <h3 className="mb-3 font-semibold text-white">{title}</h3>
      <div className="space-y-2">{children}</div>
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <label className="block text-xs text-slate-400">
      {label}
      <input
        className="mt-1 w-full rounded border border-white/10 bg-black/30 px-2 py-1 text-sm text-white"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  )
}

function Btn({ label, onClick }: { label: string; onClick: () => void | Promise<void> }) {
  return (
    <button
      type="button"
      onClick={() => void onClick()}
      className="w-full rounded-lg border border-brand-teal-500/40 bg-brand-teal-500/10 px-3 py-2 text-left text-sm text-brand-teal-100 hover:bg-brand-teal-500/20"
    >
      {label}
    </button>
  )
}
