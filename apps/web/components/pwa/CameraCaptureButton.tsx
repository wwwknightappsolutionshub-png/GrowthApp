'use client'

import { Camera } from 'lucide-react'
import { cn } from '@/lib/utils'

type Props = {
  onCapture: (file: File) => void
  className?: string
  label?: string
  accept?: string
}

/** Native camera capture via `<input capture>` — works in installed PWAs and mobile browsers. */
export function CameraCaptureButton({
  onCapture,
  className,
  label = 'Take photo',
  accept = 'image/*',
}: Props) {
  return (
    <label
      className={cn(
        'inline-flex cursor-pointer items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm font-medium text-foreground hover:bg-muted/50',
        className,
      )}
    >
      <Camera className="h-4 w-4" />
      {label}
      <input
        type="file"
        accept={accept}
        capture="environment"
        className="sr-only"
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) onCapture(file)
          event.target.value = ''
        }}
      />
    </label>
  )
}
