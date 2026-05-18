import { useMemo } from 'react'
import { Button } from './Button'

interface PaginationProps {
  currentPage: number
  totalPages: number
  total: number
  pageSize: number
  pageSizeOptions?: number[]
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}

export function Pagination({
  currentPage,
  totalPages,
  total,
  pageSize,
  pageSizeOptions = [25, 50, 100],
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1
  const endItem = Math.min(currentPage * pageSize, total)

  const pages = useMemo(() => {
    const result: (number | 'ellipsis')[] = []
    const maxVisible = 5

    if (totalPages <= maxVisible + 2) {
      for (let i = 1; i <= totalPages; i++) result.push(i)
      return result
    }

    result.push(1)
    if (currentPage > 3) result.push('ellipsis')

    const start = Math.max(2, currentPage - 1)
    const end = Math.min(totalPages - 1, currentPage + 1)
    for (let i = start; i <= end; i++) result.push(i)

    if (currentPage < totalPages - 2) result.push('ellipsis')
    result.push(totalPages)

    return result
  }, [currentPage, totalPages])

  if (totalPages <= 1 && total <= pageSize) return null

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-[#2a2a4a]">
      {/* Info text */}
      <div className="text-xs text-[#8888aa] whitespace-nowrap">
        {total > 0
          ? `Showing ${startItem}-${endItem} of ${total}`
          : 'No results'}
      </div>

      {/* Page controls */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          disabled={currentPage <= 1}
          onClick={() => onPageChange(currentPage - 1)}
          aria-label="Previous page"
        >
          ‹
        </Button>

        {pages.map((p, i) =>
          p === 'ellipsis' ? (
            <span key={`ellipsis-${i}`} className="px-2 text-xs text-[#8888aa]">
              …
            </span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`min-w-[32px] h-8 rounded-md text-xs font-medium transition-colors ${
                p === currentPage
                  ? 'bg-[#e94560] text-white'
                  : 'text-[#8888aa] hover:text-white hover:bg-[#2a2a4a]'
              }`}
              aria-label={`Page ${p}`}
              aria-current={p === currentPage ? 'page' : undefined}
            >
              {p}
            </button>
          )
        )}

        <Button
          variant="ghost"
          size="sm"
          disabled={currentPage >= totalPages}
          onClick={() => onPageChange(currentPage + 1)}
          aria-label="Next page"
        >
          ›
        </Button>

        {/* Page size selector */}
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="ml-3 bg-[#16213e] border border-[#2a2a4a] rounded-md px-2 py-1 text-xs text-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors"
          aria-label="Page size"
        >
          {pageSizeOptions.map((size) => (
            <option key={size} value={size}>
              {size}/page
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
