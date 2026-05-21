'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Download, Upload } from 'lucide-react'
import { crm } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function CrmImportPage() {
  const [csv, setCsv] = useState('first_name,last_name,email,phone,source\nJane,Smith,jane@example.com,+447700900123,csv')

  const exportMut = useMutation({
    mutationFn: () => crm.exportLeadsCsv().then((r) => r.data as string),
    onSuccess: (data) => {
      const blob = new Blob([data], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'leads-export.csv'
      a.click()
      URL.revokeObjectURL(url)
    },
    onError: () => toast.error('Export failed'),
  })

  const importMut = useMutation({
    mutationFn: () => crm.importLeadsCsv(csv),
    onSuccess: (r) => {
      toast.success(`Imported ${r.data.row_count ?? 0} leads`)
    },
    onError: () => toast.error('Import failed'),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-foreground">Import / Export</h1>
        <p className="text-sm text-muted-foreground">CSV for leads (customers export via GDPR tools)</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Export leads</CardTitle>
        </CardHeader>
        <CardContent>
          <button
            type="button"
            onClick={() => exportMut.mutate()}
            disabled={exportMut.isPending}
            className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium"
          >
            <Download className="h-4 w-4" />
            Download CSV
          </button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Import leads</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-xs text-muted-foreground">
            Header row required: first_name, last_name, email, phone, source
          </p>
          <textarea
            value={csv}
            onChange={(e) => setCsv(e.target.value)}
            rows={8}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 font-mono text-xs"
          />
          <button
            type="button"
            onClick={() => importMut.mutate()}
            disabled={importMut.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white"
          >
            <Upload className="h-4 w-4" />
            Import CSV
          </button>
        </CardContent>
      </Card>
    </div>
  )
}
