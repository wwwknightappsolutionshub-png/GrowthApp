import { fetchPublicBookingWidget } from '@/lib/public-booking-server'
import { PublicBookClient } from './PublicBookClient'

type Props = {
  params: Promise<{ tenant_slug: string }>
}

export default async function PublicBookPage({ params }: Props) {
  const { tenant_slug: slug } = await params
  const initialWidget = await fetchPublicBookingWidget(slug)
  return <PublicBookClient slug={slug} initialWidget={initialWidget} />
}
