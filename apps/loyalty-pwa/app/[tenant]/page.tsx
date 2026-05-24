import { redirect } from 'next/navigation'

export default function TenantHome({ params }: { params: { tenant: string } }) {
  redirect(`/${params.tenant}/dashboard`)
}
