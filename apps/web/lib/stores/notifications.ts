/**
 * Zustand store for in-app notifications.
 *
 * - The bell component renders directly from this store.
 * - `useNotificationSocket` wires the WebSocket stream into the store.
 * - REST mutations (mark read, archive) update the store optimistically and
 *   then reconcile against the server response.
 */
import { create } from 'zustand'

import { notifications as api } from '../api-client'

export interface Notification {
  id: string
  tenant_id: string
  user_id: string | null
  kind: string
  title: string
  body: string | null
  link: string | null
  extra: Record<string, unknown>
  read_at: string | null
  archived_at: string | null
  created_at: string
}

interface NotificationsState {
  items: Notification[]
  unread: number
  isLoading: boolean
  isOpen: boolean
  setOpen: (open: boolean) => void
  hydrate: () => Promise<void>
  ingest: (notif: Notification) => void
  markRead: (id: string) => Promise<void>
  markAllRead: () => Promise<void>
  archive: (id: string) => Promise<void>
  setUnread: (count: number) => void
}

export const useNotificationsStore = create<NotificationsState>((set, get) => ({
  items: [],
  unread: 0,
  isLoading: false,
  isOpen: false,
  setOpen: (open) => set({ isOpen: open }),

  hydrate: async () => {
    set({ isLoading: true })
    try {
      const { data } = await api.list({ page: 1, page_size: 25 })
      set({ items: data.items, unread: data.unread, isLoading: false })
    } catch (err) {
      console.error('Failed to load notifications', err)
      set({ isLoading: false })
    }
  },

  ingest: (notif) =>
    set((state) => {
      // De-duplicate by id (the websocket may echo a row we just polled).
      const exists = state.items.some((n) => n.id === notif.id)
      const items = exists ? state.items : [notif, ...state.items].slice(0, 100)
      const unread = exists
        ? state.unread
        : notif.read_at
        ? state.unread
        : state.unread + 1
      return { items, unread }
    }),

  markRead: async (id) => {
    const current = get().items.find((n) => n.id === id)
    if (!current || current.read_at) return
    // Optimistic update
    set((state) => ({
      items: state.items.map((n) =>
        n.id === id ? { ...n, read_at: new Date().toISOString() } : n,
      ),
      unread: Math.max(0, state.unread - 1),
    }))
    try {
      await api.markRead(id)
    } catch (err) {
      console.error('Failed to mark read', err)
      // Best-effort rollback
      set((state) => ({
        items: state.items.map((n) =>
          n.id === id ? { ...n, read_at: current.read_at } : n,
        ),
        unread: state.unread + 1,
      }))
    }
  },

  markAllRead: async () => {
    const prev = get().items
    set((state) => ({
      items: state.items.map((n) =>
        n.read_at ? n : { ...n, read_at: new Date().toISOString() },
      ),
      unread: 0,
    }))
    try {
      await api.markAllRead()
    } catch (err) {
      console.error('Failed to mark all read', err)
      set({ items: prev })
    }
  },

  archive: async (id) => {
    const prev = get().items
    set((state) => ({
      items: state.items.filter((n) => n.id !== id),
    }))
    try {
      await api.archive(id)
    } catch (err) {
      console.error('Failed to archive', err)
      set({ items: prev })
    }
  },

  setUnread: (count) => set({ unread: count }),
}))
