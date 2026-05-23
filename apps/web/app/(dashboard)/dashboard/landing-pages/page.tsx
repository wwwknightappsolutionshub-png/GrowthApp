import { redirect } from 'next/navigation'

/** Legacy route — use Business Page (site builder) instead. */
export default function LandingPagesRedirect() {
  redirect('/dashboard/site-builder')
}
