'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { FileImage, FileText, Film, Upload } from 'lucide-react'
import { social } from '@/lib/api-client'
import { toast } from 'sonner'

type FileType = 'IMAGE' | 'VIDEO' | 'PDF'

interface SampleRow {
  id: string
  file_url: string
  file_type: FileType
  uploaded_at: string
  source_name?: string
  is_local?: boolean
}

const TYPE_ICONS: Record<FileType, typeof FileImage> = {
  IMAGE: FileImage,
  VIDEO: Film,
  PDF: FileText,
}

export default function UploadSamplesPage() {
  const [fileUrl, setFileUrl] = useState('')
  const [fileType, setFileType] = useState<FileType>('IMAGE')
  const [localFileName, setLocalFileName] = useState('')
  const [uploaded, setUploaded] = useState<SampleRow[]>([])

  const uploadMut = useMutation({
    mutationFn: () => social.uploadSample({ file_url: fileUrl, file_type: fileType }),
    onSuccess: (res) => {
      const id = res.data?.id
      setUploaded((prev) => [
        {
          id,
          file_url: fileUrl,
          file_type: fileType,
          uploaded_at: new Date().toISOString(),
          source_name: localFileName || fileUrl,
          is_local: Boolean(localFileName),
        },
        ...prev,
      ])
      setFileUrl('')
      setLocalFileName('')
      toast.success('Sample uploaded — the AI will use it to learn your style')
    },
    onError: () => toast.error('Failed to upload sample'),
  })

  function submit() {
    if (!fileUrl.trim()) {
      toast.error('Add a file URL or choose a file from your device first')
      return
    }
    uploadMut.mutate()
  }

  function handleLocalFile(file: File | undefined) {
    if (!file) return

    const nextType = inferFileType(file)
    if (!nextType) {
      toast.error('Choose an image, video, or PDF file')
      return
    }

    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result !== 'string') {
        toast.error('Could not read this file')
        return
      }
      setFileType(nextType)
      setFileUrl(reader.result)
      setLocalFileName(file.name)
      toast.success('Local file selected')
    }
    reader.onerror = () => toast.error('Could not read this file')
    reader.readAsDataURL(file)
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Upload className="h-6 w-6 text-primary" /> Upload Samples
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Add 5–20 examples of posts, graphics, or guides you love. The AI will study them to
          match your style.
        </p>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 space-y-4 shadow-sm">
        <div>
          <label className="block text-sm font-medium mb-1">Type</label>
          <div className="flex gap-2">
            {(['IMAGE', 'VIDEO', 'PDF'] as FileType[]).map((t) => {
              const Icon = TYPE_ICONS[t]
              return (
                <button
                  key={t}
                  onClick={() => setFileType(t)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold border ${
                    fileType === t
                      ? 'bg-primary/10 text-primary border-primary/40'
                      : 'bg-card text-muted-foreground border-border hover:border-foreground/30'
                  }`}
                >
                  <Icon className="h-4 w-4" /> {t}
                </button>
              )
            })}
          </div>
        </div>

        <div className="rounded-xl border border-dashed border-brand-forest-300 bg-brand-forest-50/40 p-4">
          <label className="block text-sm font-semibold text-brand-forest-800 mb-2">
            Upload from local device
          </label>
          <input
            type="file"
            accept="image/*,video/*,.pdf,application/pdf"
            onChange={(e) => handleLocalFile(e.target.files?.[0])}
            className="block w-full cursor-pointer rounded-lg border border-brand-forest-200 bg-white text-sm text-muted-foreground file:mr-4 file:border-0 file:bg-brand-forest-700 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-brand-forest-foreground hover:file:bg-brand-forest-800"
          />
          <p className="text-xs text-brand-forest-700/80 mt-2">
            Choose an image, video, or PDF from your computer. You can also paste a public URL below.
          </p>
          {localFileName && (
            <p className="mt-2 rounded-lg bg-white px-3 py-2 text-xs font-medium text-brand-forest-800">
              Selected: {localFileName}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">File URL or selected local file</label>
          <input
            value={fileUrl}
            onChange={(e) => {
              setFileUrl(e.target.value)
              setLocalFileName('')
            }}
            placeholder="https://cdn.yoursite.com/sample.png"
            className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Paste a public URL, or use the local device picker above to fill this automatically.
          </p>
        </div>

        <button
          onClick={submit}
          disabled={uploadMut.isPending}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
        >
          <Upload className="h-4 w-4" />
          {uploadMut.isPending ? 'Uploading…' : 'Upload sample'}
        </button>
      </div>

      <div>
        <h2 className="text-sm font-semibold text-foreground mb-3">Recent uploads</h2>
        {uploaded.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-8 text-center text-muted-foreground text-sm">
            No samples uploaded in this session yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {uploaded.map((s) => {
              const Icon = TYPE_ICONS[s.file_type]
              return (
                <div key={s.id} className="bg-card border border-border rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className="h-4 w-4 text-primary" />
                    <span className="text-xs font-semibold text-muted-foreground">
                      {s.file_type}
                    </span>
                  </div>
                  {s.is_local ? (
                    <p className="text-xs text-foreground break-all">{s.source_name}</p>
                  ) : (
                    <a
                      href={s.file_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-primary break-all hover:underline"
                    >
                      {s.file_url}
                    </a>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

function inferFileType(file: File): FileType | null {
  if (file.type.startsWith('image/')) return 'IMAGE'
  if (file.type.startsWith('video/')) return 'VIDEO'
  if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) return 'PDF'
  return null
}
