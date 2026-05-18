import { beforeEach, describe, expect, it } from 'vitest'
import { useCommandPalette } from './command-palette'

beforeEach(() => {
  useCommandPalette.setState({ isOpen: false })
})

describe('useCommandPalette', () => {
  it('starts closed', () => {
    expect(useCommandPalette.getState().isOpen).toBe(false)
  })

  it('open() sets isOpen to true', () => {
    useCommandPalette.getState().open()
    expect(useCommandPalette.getState().isOpen).toBe(true)
  })

  it('close() sets isOpen to false', () => {
    useCommandPalette.setState({ isOpen: true })
    useCommandPalette.getState().close()
    expect(useCommandPalette.getState().isOpen).toBe(false)
  })

  it('toggle() flips state', () => {
    expect(useCommandPalette.getState().isOpen).toBe(false)
    useCommandPalette.getState().toggle()
    expect(useCommandPalette.getState().isOpen).toBe(true)
    useCommandPalette.getState().toggle()
    expect(useCommandPalette.getState().isOpen).toBe(false)
  })
})
