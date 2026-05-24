/** Server-safe URL helpers for the customer rewards wallet. */

export function rewardsPath(tenant: string, subpath = ''): string {
  const suffix = subpath ? `/${subpath.replace(/^\//, '')}` : ''
  return `/rewards/${encodeURIComponent(tenant)}${suffix}`
}
