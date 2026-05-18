import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './button'

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
  })

  it('applies variant classes', () => {
    render(<Button variant="destructive">Delete</Button>)
    const btn = screen.getByRole('button', { name: 'Delete' })
    expect(btn.className).toMatch(/bg-destructive/)
  })

  it('fires onClick when not disabled', async () => {
    const handle = vi.fn()
    render(<Button onClick={handle}>Save</Button>)
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(handle).toHaveBeenCalledOnce()
  })

  it('does not fire onClick when disabled', async () => {
    const handle = vi.fn()
    render(
      <Button onClick={handle} disabled>
        Save
      </Button>,
    )
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(handle).not.toHaveBeenCalled()
  })

  it('renders as a child element when asChild is set', () => {
    render(
      <Button asChild>
        <a href="/foo">Go</a>
      </Button>,
    )
    const link = screen.getByRole('link', { name: 'Go' })
    expect(link).toHaveAttribute('href', '/foo')
  })
})
