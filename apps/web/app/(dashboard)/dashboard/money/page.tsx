import { redirect } from 'next/navigation'

/** Legacy route — Accounts is the canonical module name. */
export default function MoneyRedirectPage() {
  redirect('/dashboard/accounts')
}
