'use client'

import { useState, useEffect, useCallback } from 'react'
import FileUpload from '@/components/FileUpload'
import QueryInterface from '@/components/QueryInterface'
import DataTable from '@/components/DataTable'
import ChartPanel from '@/components/ChartPanel'
import InsightCards from '@/components/InsightCards'
import SchemaPanel from '@/components/SchemaPanel'
import QueryHistory, { useQueryHistory } from '@/components/QueryHistory'
import SummaryStats from '@/components/SummaryStats'
import { QueryResultSkeleton, ChartSkeleton, InsightSkeleton } from '@/components/LoadingSkeleton'
import ThemeToggle from '@/components/ThemeToggle'
import { Database, BarChart3, Wifi, WifiOff, RefreshCw, History, X } from 'lucide-react'

interface TableInfo {
  name: string
  columns: { name: string; type: string }[]
  row_count: number
}

interface QueryResult {
  sql: string
  data: Record<string, any>[]
  columns: { name: string; type: string }[]
  chart_recommendation: any
  insights: any[]
  row_count: number
  execution_time_ms: number
  confidence: number
  assumptions: string[]
}

export default function Home() {
  const [tables, setTables] = useState<TableInfo[]>([])
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [schema, setSchema] = useState<any>(null)
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [backendStatus, setBackendStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [showHistory, setShowHistory] = useState(false)
  
  // Query history hook
  const { history, addToHistory, removeFromHistory, clearHistory } = useQueryHistory()

  const API_BASE = 'http://localhost:8000'

  // Check backend health
  const checkBackendHealth = useCallback(async () => {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 5000)
      
      const res = await fetch(`${API_BASE}/health`, { signal: controller.signal })
      clearTimeout(timeout)
      
      if (res.ok) {
        setBackendStatus('connected')
        return true
      }
      setBackendStatus('disconnected')
      return false
    } catch {
      setBackendStatus('disconnected')
      return false
    }
  }, [])

  // Fetch tables on mount
  useEffect(() => {
    const init = async () => {
      const healthy = await checkBackendHealth()
      if (healthy) {
        fetchTables()
      }
    }
    init()
    
    // Periodic health check
    const interval = setInterval(checkBackendHealth, 30000)
    return () => clearInterval(interval)
  }, [checkBackendHealth])

  const fetchTables = async () => {
    try {
      const res = await fetch(`${API_BASE}/tables`)
      const data = await res.json()
      setTables(data.tables || [])
      if (data.tables?.length > 0) {
        setSelectedTable(data.tables[0].name)
        fetchSchema(data.tables[0].name)
      }
    } catch (e) {
      console.error('Failed to fetch tables:', e)
    }
  }

  const fetchSchema = async (tableName: string) => {
    try {
      const res = await fetch(`${API_BASE}/schema/${tableName}`)
      const data = await res.json()
      setSchema(data)
    } catch (e) {
      console.error('Failed to fetch schema:', e)
    }
  }

  const handleUpload = async (file: File) => {
    setIsLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Upload failed')
      }

      const data = await res.json()
      await fetchTables()
      setSelectedTable(data.table_name)
      await fetchSchema(data.table_name)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuery = async (question: string) => {
    if (!selectedTable) {
      setError('Please upload data first')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          table_name: selectedTable,
        }),
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Query failed')
      }

      const data = await res.json()
      setQueryResult(data)
      
      // Save to query history
      addToHistory({
        question,
        sql: data.sql,
        tableName: selectedTable,
        rowCount: data.row_count,
        executionTime: data.execution_time_ms
      })
    } catch (e: any) {
      setError(e.message)
    } finally {
      setIsLoading(false)
    }
  }

  // Backend disconnected state
  if (backendStatus === 'disconnected') {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center p-8 bg-white rounded-lg border border-gray-200 shadow-sm max-w-md">
          <WifiOff className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Backend Not Connected</h2>
          <p className="text-gray-600 mb-4">
            The backend server is not responding. Please start the backend first.
          </p>
          <div className="text-left bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono mb-4">
            <p className="text-gray-400 mb-1"># Start the backend:</p>
            <p>cd backend</p>
            <p>uvicorn app.main:app --reload --port 8000</p>
          </div>
          <button
            onClick={checkBackendHealth}
            className="flex items-center gap-2 mx-auto px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Retry Connection
          </button>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-500 rounded-lg">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">AutoBI</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">LLM-Powered Data Explorer</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            {/* History button */}
            {history.length > 0 && (
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
              >
                <History className="w-4 h-4" />
                <span>History ({history.length})</span>
              </button>
            )}
            
            {/* Backend status indicator */}
            <div className="flex items-center gap-1.5">
              {backendStatus === 'connected' ? (
                <Wifi className="w-4 h-4 text-green-500" />
              ) : (
                <WifiOff className="w-4 h-4 text-red-500" />
              )}
              <span className={backendStatus === 'connected' ? 'text-green-600' : 'text-red-600'}>
                {backendStatus === 'connected' ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            {tables.length > 0 && (
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4" />
                <span>{tables.length} table{tables.length !== 1 ? 's' : ''}</span>
              </div>
            )}
            
            {/* Theme Toggle */}
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Upload Section - Show prominently if no tables */}
        {tables.length === 0 ? (
          <div className="mb-8">
            <FileUpload onUpload={handleUpload} isLoading={isLoading} />
          </div>
        ) : (
          <div className="mb-6">
            <FileUpload onUpload={handleUpload} isLoading={isLoading} compact />
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Main Content - Only show if we have data */}
        {tables.length > 0 && (
          <div className="grid grid-cols-12 gap-6">
            {/* Left Sidebar - Schema */}
            <div className="col-span-3">
              <SchemaPanel
                tables={tables}
                selectedTable={selectedTable}
                schema={schema}
                onSelectTable={(name) => {
                  setSelectedTable(name)
                  fetchSchema(name)
                }}
              />
            </div>

            {/* Main Content Area */}
            <div className="col-span-9 space-y-6">
              {/* Query Interface */}
              <QueryInterface onQuery={handleQuery} isLoading={isLoading} />

              {/* Loading Skeletons */}
              {isLoading && (
                <div className="space-y-6">
                  <InsightSkeleton />
                  <ChartSkeleton />
                  <QueryResultSkeleton />
                </div>
              )}

              {/* Results */}
              {queryResult && !isLoading && (
                <>
                  {/* SQL and Metadata */}
                  <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-medium text-gray-900">Generated SQL</h3>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span>{queryResult.row_count} rows</span>
                        <span>{queryResult.execution_time_ms}ms</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs ${
                          queryResult.confidence >= 0.8 
                            ? 'bg-green-100 text-green-700' 
                            : queryResult.confidence >= 0.6 
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-red-100 text-red-700'
                        }`}>
                          {Math.round(queryResult.confidence * 100)}% confidence
                        </span>
                      </div>
                    </div>
                    <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
                      {queryResult.sql}
                    </pre>
                    {queryResult.assumptions.length > 0 && (
                      <div className="mt-3 text-sm text-amber-600">
                        <strong>Assumptions:</strong> {queryResult.assumptions.join('; ')}
                      </div>
                    )}
                  </div>

                  {/* Summary Stats */}
                  <SummaryStats data={queryResult.data} columns={queryResult.columns} />

                  {/* Insight Cards */}
                  {queryResult.insights.length > 0 && (
                    <InsightCards insights={queryResult.insights} />
                  )}

                  {/* Chart */}
                  {queryResult.chart_recommendation.chart_type !== 'none' && 
                   queryResult.chart_recommendation.chart_type !== 'table' && (
                    <ChartPanel
                      config={queryResult.chart_recommendation.config}
                      reasoning={queryResult.chart_recommendation.reasoning}
                    />
                  )}

                  {/* Data Table */}
                  <DataTable
                    data={queryResult.data}
                    columns={queryResult.columns}
                    tableName={selectedTable || 'results'}
                  />
                </>
              )}
            </div>
          </div>
        )}

        {/* Query History Slide-over Panel */}
        {showHistory && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            <div className="absolute inset-0 bg-black/20" onClick={() => setShowHistory(false)} />
            <div className="absolute right-0 top-0 h-full w-96 bg-white dark:bg-gray-800 shadow-xl border-l border-gray-200 dark:border-gray-700 overflow-y-auto">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between sticky top-0 bg-white dark:bg-gray-800">
                <h2 className="font-semibold text-gray-900 dark:text-white">Query History</h2>
                <button
                  onClick={() => setShowHistory(false)}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  aria-label="Close history panel"
                >
                  <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                </button>
              </div>
              <div className="p-4">
                <QueryHistory
                  history={history}
                  onReplay={(query) => {
                    handleQuery(query.question)
                    setShowHistory(false)
                  }}
                  onRemove={removeFromHistory}
                  onClear={clearHistory}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
