'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { ArrowLeft, Receipt, RefreshCw } from 'lucide-react'
import { billingInspectorApi } from '@/lib/api-client'
import { InvoiceViewer, type InvoiceData } from '../../components/InvoiceViewer'

export default function BillingInspectorInvoicePage() {
  const { id } = useParams<{ id: string }>()
  const q = useQuery({
    queryKey: ['billing-inspector', 'invoice', id],
    queryFn: () => billingInspectorApi.invoice(id).then((r) => r.data as InvoiceData),
    enabled: Boolean(id),
  })

  return (
    <div className="text-white">
      <div className="mb-4">
        <Link
          href="/admin/billing-inspector"
          className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to overview
        </Link>
      </div>

      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Receipt className="h-6 w-6 text-amber-400" /> Invoice
          </h1>
          <p className="text-sm text-gray-400 mt-1">Read-only invoice detail with payment-attempt history.</p>
        </div>
        <button
          onClick={() => q.refetch()}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${q.isFetching ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {q.isLoading ? (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-10 text-center text-gray-500">
          Loading invoice…
        </div>
      ) : q.isError ? (
        <div className="rounded-lg border border-red-900 bg-red-950/40 p-10 text-center text-red-300">
          Could not load invoice.
        </div>
      ) : q.data ? (
        <InvoiceViewer data={q.data} />
      ) : null}
    </div>
  )
}
