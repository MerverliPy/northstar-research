import { useState, useMemo } from 'react'
import type { ReactNode } from 'react'

interface Column<T> {
  key: string
  header: string
  render?: (item: T) => ReactNode
  className?: string
}

type SortDir = 'asc' | 'desc' | null

interface SortState {
  key: string
  dir: SortDir
}

interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyField: keyof T
  onRowClick?: (item: T) => void
  emptyMessage?: string
  emptyAction?: ReactNode
  loading?: boolean
  loadingRows?: number
  stickyHeader?: boolean
}

const SKELETON_WIDTHS = ['65%', '80%', '55%', '70%', '60%']

function SkeletonRow({ columns }: { columns: number }) {
  return (
    <tr className="border-b border-[#2a2a4a]/50">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-3 py-3">
          <div
            className="skeleton h-4"
            style={{ width: SKELETON_WIDTHS[i % SKELETON_WIDTHS.length] }}
          />
        </td>
      ))}
    </tr>
  )
}

function EmptyState({ message, action }: { message: string; action?: ReactNode }) {
  return (
    <tr>
      <td colSpan={99} className="px-3 py-12 text-center">
        <div className="flex flex-col items-center gap-3">
          <svg
            className="w-10 h-10 text-[#2a2a4a]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m6 4.125l2.25 2.25m0 0l2.25 2.25M12 11.625l2.25-2.25M12 11.625l-2.25 2.25M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"
            />
          </svg>
          <span className="text-sm text-[#8888aa]">{message}</span>
          {action}
        </div>
      </td>
    </tr>
  )
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function Table<T extends Record<string, any>>({
  columns,
  data,
  keyField,
  onRowClick,
  emptyMessage = 'No data',
  emptyAction,
  loading,
  loadingRows = 5,
  stickyHeader,
}: TableProps<T>) {
  const [sort, setSort] = useState<SortState>({ key: '', dir: null })

  const handleSort = (colKey: string) => {
    setSort((prev) => {
      if (prev.key !== colKey) return { key: colKey, dir: 'asc' }
      if (prev.dir === 'asc') return { key: colKey, dir: 'desc' }
      return { key: '', dir: null }
    })
  }

  const sortedData = useMemo(() => {
    if (!sort.key || !sort.dir) return data
    const col = columns.find((c) => c.key === sort.key)
    if (!col) return data

    const collator = new Intl.Collator('en', { numeric: true, sensitivity: 'base' })

    return [...data].sort((a, b) => {
      const aVal = a[sort.key]
      const bVal = b[sort.key]

      // Handle null/undefined
      if (aVal == null && bVal == null) return 0
      if (aVal == null) return 1
      if (bVal == null) return -1

      // Handle dates (ISO strings or Date objects)
      const aDate = aVal instanceof Date ? aVal : typeof aVal === 'string' && /^\d{4}-\d{2}-\d{2}/.test(aVal) ? new Date(aVal) : null
      const bDate = bVal instanceof Date ? bVal : typeof bVal === 'string' && /^\d{4}-\d{2}-\d{2}/.test(bVal) ? new Date(bVal) : null
      if (aDate && bDate && !isNaN(aDate.getTime()) && !isNaN(bDate.getTime())) {
        return sort.dir === 'asc'
          ? aDate.getTime() - bDate.getTime()
          : bDate.getTime() - aDate.getTime()
      }

      // Handle numbers
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sort.dir === 'asc' ? aVal - bVal : bVal - aVal
      }

      // Default: string comparison
      const aStr = String(aVal)
      const bStr = String(bVal)
      const cmp = collator.compare(aStr, bStr)
      return sort.dir === 'asc' ? cmp : -cmp
    })
  }, [data, sort, columns])

  const cellValue = (item: T, col: Column<T>): ReactNode => {
    if (col.render) return col.render(item)
    const val = item[col.key]
    if (val === null || val === undefined) return '-'
    if (typeof val === 'object') return JSON.stringify(val)
    return String(val)
  }

  const sortIndicator = (colKey: string): string => {
    if (sort.key !== colKey || !sort.dir) return ''
    return sort.dir === 'asc' ? ' ▲' : ' ▼'
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse" role="table">
        <thead>
          <tr className={stickyHeader ? 'sticky top-0 z-10' : ''}>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`text-left px-3 py-2 border-b border-[#2a2a4a] text-xs uppercase tracking-wider text-[#8888aa] font-medium bg-[#16213e] select-none ${col.className || ''} ${
                  col.key !== '' ? 'cursor-pointer hover:text-[#e0e0e0] hover:bg-[#2a2a4a]/30 transition-colors' : ''
                } ${sort.key === col.key ? 'text-[#e94560]' : ''}`}
                onClick={() => {
                  if (col.key !== '') handleSort(col.key)
                }}
                onKeyDown={col.key !== '' ? (e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    handleSort(col.key)
                  }
                } : undefined}
                tabIndex={col.key !== '' ? 0 : undefined}
                role="columnheader"
                aria-sort={
                  sort.key === col.key
                    ? sort.dir === 'asc'
                      ? 'ascending'
                      : sort.dir === 'desc'
                        ? 'descending'
                        : 'none'
                    : 'none'
                }
              >
                {col.header}
                <span className={`inline-block text-[#e94560] ${sort.key === col.key ? '' : 'invisible'}`}>
                  {sortIndicator(col.key)}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: loadingRows }).map((_, i) => (
              <SkeletonRow key={i} columns={columns.length} />
            ))
          ) : sortedData.length === 0 ? (
            <EmptyState message={emptyMessage} action={emptyAction} />
          ) : (
            sortedData.map((item) => (
              <tr
                key={String(item[keyField])}
                className={`border-b border-[#2a2a4a]/50 transition-colors ${
                  onRowClick
                    ? 'cursor-pointer hover:bg-[#2a2a4a]/30'
                    : 'hover:bg-[#2a2a4a]/10'
                }`}
                tabIndex={onRowClick ? 0 : undefined}
                role={onRowClick ? 'button' : undefined}
                onKeyDown={onRowClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onRowClick(item); } } : undefined}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-3 py-2.5 text-sm">
                    {cellValue(item, col)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
