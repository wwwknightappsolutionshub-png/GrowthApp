'use client'

import { IndustryAddonWorkspace } from '@/components/addons/IndustryAddonWorkspace'

export default function IndustryBookingPage() {
  return (
    <div className="p-6">
      <h1 className="mb-4 text-2xl font-semibold text-white">Industry Booking</h1>
      <IndustryAddonWorkspace tab="booking" />
    </div>
  )
}
