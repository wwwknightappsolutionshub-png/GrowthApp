'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { Building2, Phone, MapPin, FileText } from 'lucide-react'
import { crm } from '@/lib/api-client'

type Customer = {
  id: string
  client_type?: string
  business_name?: string | null
  first_name: string
  last_name: string | null
  phone: string | null
  address: string | null
  notes: string | null
}

export default function CompanyProfilePage() {
  const { data, isLoading } = useQuery({
    queryKey: ['crm', 'customers', 'companies'],
    queryFn: () => crm.listCustomers({ page: 1, page_size: 100 }).then((r) => r.data),
  })

  const companies = (data?.items ?? []).filter(
    (c: Customer) =>
      c.client_type === 'business' ||
      (c.business_name && c.business_name.trim().length > 0)
  )

  return (
    <div className="space-y-6">
      <div>
        <Link href="/dashboard/crm" className="text-sm text-brand-teal-100/70 hover:text-white">
          ← CRM
        </Link>
        <h1 className="text-2xl font-bold text-white mt-2 flex items-center gap-2">
          <Building2 className="w-7 h-7 text-brand-teal-300" />
          Company profile
        </h1>
        <p className="text-sm text-brand-teal-100/65 mt-1">
          Business clients — contact details and contract notes
        </p>
      </div>

      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-brand-forest-800 bg-brand-forest-900/80 text-left">
                <th className="px-4 py-3 text-xs font-bold uppercase text-brand-teal-100/60">Business</th>
                <th className="px-4 py-3 text-xs font-bold uppercase text-brand-teal-100/60">Phone</th>
                <th className="px-4 py-3 text-xs font-bold uppercase text-brand-teal-100/60">Address</th>
                <th className="px-4 py-3 text-xs font-bold uppercase text-brand-teal-100/60">Contract</th>
                <th className="px-4 py-3 text-xs font-bold uppercase text-brand-teal-100/60" />
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-brand-teal-100/60">
                    Loading…
                  </td>
                </tr>
              ) : companies.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-brand-teal-100/60">
                    No business clients yet. Set client type to &quot;Business&quot; on a customer record.
                  </td>
                </tr>
              ) : (
                companies.map((c: Customer) => (
                  <tr key={c.id} className="border-b border-brand-forest-800 hover:bg-brand-forest-900">
                    <td className="px-4 py-3 font-semibold text-white">
                      {c.business_name || `${c.first_name} ${c.last_name ?? ''}`.trim()}
                    </td>
                    <td className="px-4 py-3 text-brand-teal-100/80">
                      {c.phone ? (
                        <span className="inline-flex items-center gap-1">
                          <Phone className="w-3.5 h-3.5" />
                          {c.phone}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-4 py-3 text-brand-teal-100/80 max-w-xs">
                      {c.address ? (
                        <span className="inline-flex items-start gap-1">
                          <MapPin className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                          {c.address}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-4 py-3 text-brand-teal-100/80 max-w-sm truncate">
                      {c.notes ? (
                        <span className="inline-flex items-center gap-1" title={c.notes}>
                          <FileText className="w-3.5 h-3.5 shrink-0" />
                          {c.notes.slice(0, 80)}
                          {c.notes.length > 80 ? '…' : ''}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/dashboard/crm/customers/${c.id}`}
                        className="text-xs font-semibold text-brand-teal-300 hover:underline"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
