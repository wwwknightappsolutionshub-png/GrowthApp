/**
 * Cmd-K palette open/close state. Keeping it in Zustand so any component can
 * toggle the palette (e.g. the global search button in the topbar, or a
 * keyboard shortcut).
 */
import { create } from 'zustand'

interface CommandPaletteState {
  isOpen: boolean
  open: () => void
  close: () => void
  toggle: () => void
}

export const useCommandPalette = create<CommandPaletteState>((set, get) => ({
  isOpen: false,
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
  toggle: () => set({ isOpen: !get().isOpen }),
}))
