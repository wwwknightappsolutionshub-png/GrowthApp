import { AUTH_HEADLINE } from '@/components/brand/BrandMark'

type Props = {
  eyebrow: string
  title?: string
  description: string
}

export function AuthPageHeader({ eyebrow, title = AUTH_HEADLINE, description }: Props) {
  return (
    <div className="mb-8">
      <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-brand-teal-500">
        {eyebrow}
      </span>
      <h1 className="mt-3 font-display text-2xl font-bold leading-tight tracking-tight text-foreground sm:text-3xl">
        {title}
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
    </div>
  )
}
