import { cn } from '@/lib/utils'

type Props = {
  className?: string
  lineClassName?: string
  variant?: 'light' | 'dark'
}

export function AuthJourneyHeadline({ className, lineClassName, variant = 'light' }: Props) {
  const accent = variant === 'light' ? 'text-brand-teal-300' : 'text-brand-teal-500'
  const base = variant === 'light' ? 'text-white' : 'text-foreground'

  return (
    <span className={cn('block', className)}>
      <span className={cn('block font-display font-bold tracking-tight', base, lineClassName)}>
        One Platform
      </span>
      <span className={cn('block font-display font-bold tracking-tight', accent, lineClassName)}>
        for your customer journey
      </span>
    </span>
  )
}

export function authPageTitle(label: string) {
  return `${label} | CustomerFlowai`
}
