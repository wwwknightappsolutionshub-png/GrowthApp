const QUEUE_KEY = 'cf:pwa:sync-queue'

export type SyncQueueItem = {
  id: string
  url: string
  method: string
  body?: string
  createdAt: number
}

function readQueue(): SyncQueueItem[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(window.localStorage.getItem(QUEUE_KEY) || '[]') as SyncQueueItem[]
  } catch {
    return []
  }
}

function writeQueue(items: SyncQueueItem[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(QUEUE_KEY, JSON.stringify(items.slice(-50)))
}

export function enqueueBackgroundSync(item: Omit<SyncQueueItem, 'id' | 'createdAt'>) {
  const queue = readQueue()
  queue.push({
    ...item,
    id: crypto.randomUUID(),
    createdAt: Date.now(),
  })
  writeQueue(queue)
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    void navigator.serviceWorker.ready.then((reg) => {
      void reg.sync.register('customerflow-mutation-sync').catch(() => {})
    })
  }
}

export function drainSyncQueue(): SyncQueueItem[] {
  const queue = readQueue()
  writeQueue([])
  return queue
}

export function peekSyncQueue(): SyncQueueItem[] {
  return readQueue()
}
