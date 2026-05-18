'use client'

import React from 'react'

export interface BillingTableColumn<T> {
  key: string
  header: string
  align?: 'left' | 'right' | 'center'
  render: (row: T) => React.ReactNode
}

export interface BillingTableProps<T> {
  columns: BillingTableColumn<T>[]
  rows: T[]
  isLoading?: boolean
  isError?: boolean
  emptyLabel?: string
  rowKey: (row: T) => string
}

export function BillingTable<T>({
  columns,
  rows,
  isLoading,
  isError,
  emptyLabel = 'No records.',
  rowKey,
}: BillingTableProps<T>) {
  const colCount = columns.length

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-800 text-sm">
          <thead className="bg-gray-950/60 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              {columns.map((c) => (
                <th
                  key={c.key}
                  className={`px-4 py-3 font-semibold ${
                    c.align === 'right'
                      ? 'text-right'
                      : c.align === 'center'
                      ? 'text-center'
                      : 'text-left'
                  }`}
                >
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-200">
            {isLoading && (
              <tr>
                <td colSpan={colCount} className="px-4 py-10 text-center text-gray-500">
                  Loading…
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={colCount} className="px-4 py-10 text-center text-red-400">
                  Could not load data.
                </td>
              </tr>
            )}
            {!isLoading && !isError && rows.length === 0 && (
              <tr>
                <td colSpan={colCount} className="px-4 py-10 text-center text-gray-500">
                  {emptyLabel}
                </td>
              </tr>
            )}
            {!isLoading &&
              !isError &&
              rows.map((row) => (
                <tr key={rowKey(row)} className="hover:bg-gray-950/40">
                  {columns.map((c) => (
                    <td
                      key={c.key}
                      className={`px-4 py-3 align-top ${
                        c.align === 'right'
                          ? 'text-right tabular-nums'
                          : c.align === 'center'
                          ? 'text-center'
                          : ''
                      }`}
                    >
                      {c.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
