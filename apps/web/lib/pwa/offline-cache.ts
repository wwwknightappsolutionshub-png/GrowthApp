const DB_NAME = 'customerflow-offline-v1'
const STORE = 'api-cache'

type CacheRow = {
  key: string
  body: string
  updatedAt: number
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'key' })
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export async function cacheApiResponse(path: string, data: unknown) {
  if (typeof indexedDB === 'undefined') return
  const db = await openDb()
  const tx = db.transaction(STORE, 'readwrite')
  tx.objectStore(STORE).put({
    key: path,
    body: JSON.stringify(data),
    updatedAt: Date.now(),
  } satisfies CacheRow)
}

export async function readCachedApiResponse<T>(path: string): Promise<T | null> {
  if (typeof indexedDB === 'undefined') return null
  const db = await openDb()
  return new Promise((resolve) => {
    const req = db.transaction(STORE, 'readonly').objectStore(STORE).get(path)
    req.onsuccess = () => {
      const row = req.result as CacheRow | undefined
      if (!row?.body) {
        resolve(null)
        return
      }
      try {
        resolve(JSON.parse(row.body) as T)
      } catch {
        resolve(null)
      }
    }
    req.onerror = () => resolve(null)
  })
}

export const OFFLINE_API_PREFIXES = [
  '/api/v1/leads',
  '/api/v1/quotes',
  '/api/v1/bookings',
  '/api/v1/crm/customers',
] as const
