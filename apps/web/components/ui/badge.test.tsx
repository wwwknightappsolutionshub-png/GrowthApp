import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from './badge'

describe('Badge', () => {
  it('renders default variant', () => {
    render(<Badge>New</Badge>)
    const badge = screen.getByText('New')
    expect(badge.className).toMatch(/bg-primary/)
  })

  it('renders destructive variant', () => {
    render(<Badge variant="destructive">Failed</Badge>)
    expect(screen.getByText('Failed').className).toMatch(/bg-destructive/)
  })

  it('renders success and warning variants', () => {
    const { rerender } = render(<Badge variant="success">OK</Badge>)
    expect(screen.getByText('OK').className).toMatch(/bg-success/)

    rerender(<Badge variant="warning">Warn</Badge>)
    expect(screen.getByText('Warn').className).toMatch(/bg-warning/)
  })
})
