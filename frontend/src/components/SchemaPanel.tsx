'use client'

import { Database, Table, Hash, Calendar, Type } from 'lucide-react'
import clsx from 'clsx'

interface TableInfo {
  name: string
  columns: { name: string; type: string }[]
  row_count: number
}

interface SchemaColumn {
  name: string
  sql_type: string
  semantic_type: string
  quality_score: number
}

interface Schema {
  table_name: string
  row_count: number
  column_count: number
  columns: SchemaColumn[]
  date_columns: string[]
  measure_columns: string[]
  dimension_columns: string[]
  quality_score: number
  warnings: string[]
}

interface SchemaPanelProps {
  tables: TableInfo[]
  selectedTable: string | null
  schema: Schema | null
  onSelectTable: (name: string) => void
}

const TypeIcon = ({ type }: { type: string }) => {
  switch (type) {
    case 'date':
      return <Calendar className="w-3.5 h-3.5 text-amber-500" />
    case 'measure':
      return <Hash className="w-3.5 h-3.5 text-blue-500" />
    default:
      return <Type className="w-3.5 h-3.5 text-gray-400" />
  }
}

export default function SchemaPanel({
  tables,
  selectedTable,
  schema,
  onSelectTable,
}: SchemaPanelProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-gray-500" />
          <h3 className="font-medium text-gray-900">Data Schema</h3>
        </div>
      </div>

      {/* Table List */}
      <div className="p-2 border-b border-gray-200">
        {tables.map((table) => (
          <button
            key={table.name}
            onClick={() => onSelectTable(table.name)}
            className={clsx(
              'w-full flex items-center gap-2 px-3 py-2 rounded-md text-left transition-colors',
              selectedTable === table.name
                ? 'bg-primary-50 text-primary-700'
                : 'text-gray-700 hover:bg-gray-50'
            )}
          >
            <Table className="w-4 h-4" />
            <span className="flex-1 truncate text-sm font-medium">{table.name}</span>
            <span className="text-xs text-gray-400">{table.row_count} rows</span>
          </button>
        ))}
      </div>

      {/* Schema Details */}
      {schema && (
        <div className="p-4">
          {/* Quality Score */}
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-600">Data Quality</span>
              <span className={clsx(
                'font-medium',
                schema.quality_score >= 80 ? 'text-green-600' :
                schema.quality_score >= 60 ? 'text-yellow-600' : 'text-red-600'
              )}>
                {schema.quality_score}%
              </span>
            </div>
            <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={clsx(
                  'h-full rounded-full transition-all',
                  schema.quality_score >= 80 ? 'bg-green-500' :
                  schema.quality_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                )}
                style={{ width: `${schema.quality_score}%` }}
              />
            </div>
          </div>

          {/* Warnings */}
          {schema.warnings.length > 0 && (
            <div className="mb-4 p-2 bg-amber-50 border border-amber-200 rounded-md">
              <ul className="text-xs text-amber-700 space-y-1">
                {schema.warnings.map((warning, i) => (
                  <li key={i}>⚠️ {warning}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Columns */}
          <div className="space-y-1.5">
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              Columns ({schema.column_count})
            </h4>
            {schema.columns.map((col) => (
              <div
                key={col.name}
                className="flex items-center gap-2 px-2 py-1.5 rounded bg-gray-50 text-sm"
              >
                <TypeIcon type={col.semantic_type} />
                <span className="flex-1 truncate text-gray-700">{col.name}</span>
                <span className="text-xs text-gray-400">{col.semantic_type}</span>
              </div>
            ))}
          </div>

          {/* Column Summary */}
          <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-lg font-semibold text-amber-600">
                {schema.date_columns.length}
              </div>
              <div className="text-xs text-gray-500">Dates</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-blue-600">
                {schema.measure_columns.length}
              </div>
              <div className="text-xs text-gray-500">Measures</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-gray-600">
                {schema.dimension_columns.length}
              </div>
              <div className="text-xs text-gray-500">Dimensions</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
