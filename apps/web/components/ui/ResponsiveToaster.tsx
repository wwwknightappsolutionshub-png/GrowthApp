'use client'

import { useEffect, useState } from 'react'
import { Toaster, type ToasterProps } from 'sonner'

const MOBILE_MAX = 639

type Props = Omit<ToasterProps, 'position'>

export function ResponsiveToaster(props: Props) {
  const [position, setPosition] = useState<ToasterProps['position']>('top-right')

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_MAX}px)`)
    const sync = () => setPosition(mq.matches ? 'bottom-center' : 'top-right')
    sync()
    mq.addEventListener('change', sync)
    return () => mq.removeEventListener('change', sync)
  }, [])

  return <Toaster position={position} {...props} />
}
