import { describe, expect, it } from 'vitest'
import { cn, formatCurrency, formatDate, getInitials, slugify } from './utils'

describe('cn', () => {
  it('merges class names and dedupes Tailwind conflicts', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4')
    expect(cn('text-sm', { 'font-bold': true, 'italic': false })).toBe(
      'text-sm font-bold',
    )
    expect(cn('a', null, undefined, false, 'b')).toBe('a b')
  })
})

describe('formatCurrency', () => {
  it('formats GBP from pence', () => {
    expect(formatCurrency(0)).toBe('£0.00')
    expect(formatCurrency(199)).toBe('£1.99')
    expect(formatCurrency(150000)).toBe('£1,500.00')
  })

  it('handles negative amounts', () => {
    expect(formatCurrency(-2599)).toMatch(/-?£25\.99|£-25\.99/)
  })
})

describe('formatDate', () => {
  it('formats ISO strings as DD MMM YYYY (en-GB)', () => {
    const result = formatDate('2026-05-11T10:00:00Z')
    expect(result).toMatch(/11 May 2026/)
  })

  it('accepts Date objects', () => {
    expect(formatDate(new Date('2025-01-15'))).toMatch(/15 Jan 2025/)
  })
})

describe('getInitials', () => {
  it('returns up to two uppercase letters', () => {
    expect(getInitials('Mike Thompson')).toBe('MT')
    expect(getInitials('alice')).toBe('A')
    expect(getInitials('John James Smith')).toBe('JJ')
  })
})

describe('slugify', () => {
  it('converts text to safe url slugs', () => {
    expect(slugify('Mike’s Plumbing & Heating!')).toBe('mikes-plumbing-heating')
    expect(slugify('  Spaces   everywhere  ')).toBe('spaces-everywhere')
    expect(slugify('Already-A-Slug')).toBe('already-a-slug')
  })
})
