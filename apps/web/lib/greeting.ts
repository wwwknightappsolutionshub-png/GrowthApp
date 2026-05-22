/** Time-of-day greeting for tenant-facing dashboards. */
export function timeOfDayGreeting(now = new Date()): 'morning' | 'afternoon' | 'evening' {
  const h = now.getHours()
  if (h < 12) return 'morning'
  if (h < 17) return 'afternoon'
  return 'evening'
}

export function greetingPhrase(now = new Date()): string {
  const part = timeOfDayGreeting(now)
  if (part === 'morning') return 'Good morning'
  if (part === 'afternoon') return 'Good afternoon'
  return 'Good evening'
}

export function firstName(fullName?: string | null): string {
  if (!fullName?.trim()) return 'there'
  return fullName.trim().split(/\s+/)[0] ?? 'there'
}
