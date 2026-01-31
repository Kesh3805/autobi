'use client'

import { useState, useMemo } from 'react'
import { ChevronUp, ChevronDown, Table as TableIcon, Search, X } from 'lucide-react'
import clsx from 'clsx'
import ExportButton from './ExportButton'

interface Column {
  name: string
  type: string
}

interface DataTableProps {
  data: Record<string, any>[]
  columns: Column[]
  tableName?: string
}

type SortDirection = 'asc' | 'desc' | null

export default function DataTable({ data, columns, tableName = 'results' }: DataTableProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)
  const [page, setPage] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const pageSize = 25

  const handleSort = (colName: string) => {
    if (sortColumn === colName) {
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortColumn(null)
        setSortDirection(null)
      }
    } else {
      setSortColumn(colName)
      setSortDirection('asc')
    }
  }

  const filteredData = useMemo(() => {
    if (!searchTerm.trim()) return data
    const term = searchTerm.toLowerCase()
    return data.filter(row =>
      columns.some(col => {
        const val = row[col.name]
        return val != null && String(val).toLowerCase().includes(term)
      })
    )
  }, [data, columns, searchTerm])

  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return filteredData

    return [...filteredData].sort((a, b) => {
      const aVal = a[sortColumn]
      const bVal = b[sortColumn]

      if (aVal === null || aVal === undefined) return 1
      if (bVal === null || bVal === undefined) return -1

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
      }

      const aStr = String(aVal)
      const bStr = String(bVal)
      return sortDirection === 'asc' 
        ? aStr.localeCompare(bStr) 
        : bStr.localeCompare(aStr)
    })
  }, [filteredData, sortColumn, sortDirection])

  const paginatedData = useMemo(() => {
    const start = page * pageSize
    return sortedData.slice(start, start + pageSize)
  }, [sortedData, page])

  const totalPages = Math.ceil(filteredData.length / pageSize)

  const formatValue = (value: any, type: string): string => {
    if (value === null || value === undefined) return '—'
    
    if (type === 'measure' && typeof value === 'number') {
      return value.toLocaleString(undefined, { 
        maximumFractionDigits: 2 
      })
    }
    
    return String(value)
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <TableIcon className="w-4 h-4 text-gray-500" />
          <h3 className="font-medium text-gray-900">Results</h3>
          <span className="text-sm text-gray-500">
            ({filteredData.length}{filteredData.length !== data.length ? ` of ${data.length}` : ''} rows)
          </span>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                setPage(0) // Reset to first page on search
              }}
              placeholder="Filter results..."
              className="pl-9 pr-8 py-1.5 text-sm border border-gray-200 rounded-lg w-48 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          
          {/* Export */}
          <ExportButton data={filteredData} columns={columns} filename={tableName} />
        </div>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-500">
              Page {page + 1} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.name}
                  onClick={() => handleSort(col.name)}
                  className={clsx(
                    'px-4 py-3 text-left font-medium text-gray-700 cursor-pointer hover:bg-gray-100',
                    col.type === 'measure' && 'text-right'
                  )}
                >
                  <div className={clsx(
                    'flex items-center gap-1',
                    col.type === 'measure' && 'justify-end'
                  )}>
                    <span>{col.name}</span>
                    <div className="w-4 h-4 flex items-center justify-center">
                      {sortColumn === col.name && (
                        sortDirection === 'asc' 
                          ? <ChevronUp className="w-4 h-4" />
                          : <ChevronDown className="w-4 h-4" />
                      )}
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {paginatedData.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-gray-50">
                {columns.map((col) => (
                  <td
                    key={col.name}
                    className={clsx(
                      'px-4 py-3 text-gray-900',
                      col.type === 'measure' && 'text-right font-mono'
                    )}
                  >
                    {formatValue(row[col.name], col.type)}
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
