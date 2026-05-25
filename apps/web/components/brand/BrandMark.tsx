import Image from 'next/image'

import { cn } from '@/lib/utils'

export const AUTH_HEADLINE = 'Lead + Book + CRM + Booking + Retention'
export const AUTH_JOURNEY_HEADLINE = 'One Platform for your customer journey'

type BrandIconProps = {
  size?: number
  className?: string
}

export function BrandIcon({ size = 32, className }: BrandIconProps) {
  return (
    <Image
      src="/icons/icon.svg"
      alt=""
      width={size}
      height={size}
      className={cn('shrink-0 rounded-md shadow-brand', className)}
      aria-hidden
    />
  )
}

type BrandMarkProps = {
  className?: string
  textClassName?: string
  iconSize?: number
  variant?: 'default' | 'light'
  showText?: boolean
}

export function BrandMark({
  className,
  textClassName,
  iconSize = 32,
  variant = 'default',
  showText = true,
}: BrandMarkProps) {
  const aiColor = variant === 'light' ? 'text-brand-teal-300' : 'text-brand-teal-500'
  const textColor = variant === 'light' ? 'text-white' : 'text-foreground'

  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <BrandIcon size={iconSize} />
      {showText ? (
        <span
          className={cn(
            'font-display text-[17px] font-bold tracking-tight',
            textColor,
            textClassName,
          )}
        >
          CustomerFlow<span className={aiColor}>ai</span>
        </span>
      ) : null}
    </span>
  )
}

export function BrandName({ className, variant = 'default' }: { className?: string; variant?: 'default' | 'light' }) {
  const aiColor = variant === 'light' ? 'text-brand-teal-300' : 'text-brand-teal-500'
  const textColor = variant === 'light' ? 'text-white' : 'text-foreground'

  return (
    <span className={cn('font-display font-bold tracking-tight', textColor, className)}>
      CustomerFlow<span className={aiColor}>ai</span>
    </span>
  )
}
