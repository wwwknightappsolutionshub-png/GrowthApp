import { redirect } from 'next/navigation'

export default async function LoyaltyLandingAliasPage({
  params,
}: {
  params: Promise<{ tenant: string }>
}) {
  const { tenant } = await params
  redirect(`/p/${tenant}/memberships`)
}
