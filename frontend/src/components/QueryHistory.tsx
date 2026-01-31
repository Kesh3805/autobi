'use client'

import { useState, useEffect } from 'react'
import { History, X, Play, Trash2, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import clsx from 'clsx'

interface QueryHistoryItem {
  id: string
  question: string
  timestamp: number
  rowCount: number
  executionTime: number
  confidence: number
}

interface QueryHistoryProps {
  onReplay: (question: string) => void
  currentQuestion?: string
}

const STORAGE_KEY = 'autobi_query_history'
const MAX_HISTORY = 50

export function useQueryHistory() {
  const [history, setHistory] = useState<QueryHistoryItem[]>([])

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        setHistory(JSON.parse(stored))
      } catch {
        setHistory([])
      }
    }
  }, [])

  const addToHistory = (item: Omit<QueryHistoryItem, 'id' | 'timestamp'>) => {
    const newItem: QueryHistoryItem = {
      ...item,
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      timestamp: Date.now(),
    }
    
    setHistory(prev => {
      // Avoid duplicates
      const filtered = prev.filter(h => h.question.toLowerCase() !== item.question.toLowerCase())
      const updated = [newItem, ...filtered].slice(0, MAX_HISTORY)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      return updated
    })
  }

  const removeFromHistory = (id: string) => {
    setHistory(prev => {
      const updated = prev.filter(h => h.id !== id)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      return updated
    })
  }

  const clearHistory = () => {
    setHistory([])
    localStorage.removeItem(STORAGE_KEY)
  }

  return { history, addToHistory, removeFromHistory, clearHistory }
}

export default function QueryHistory({ onReplay, currentQuestion }: QueryHistoryProps) {
  const { history, removeFromHistory, clearHistory } = useQueryHistory()
  const [isExpanded, setIsExpanded] = useState(false)
  const [showAll, setShowAll] = useState(false)

  if (history.length === 0) return null

  const displayedHistory = showAll ? history : history.slice(0, 5)

  const formatTime = (timestamp: number) => {
    const diff = Date.now() - timestamp
    const mins = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)
    
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-gray-500" />
          <span className="font-medium text-gray-900">Query History</span>
          <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
            {history.length}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {/* History List */}
      {isExpanded && (
        <div className="border-t border-gray-100">
          <div className="max-h-80 overflow-y-auto">
            {displayedHistory.map((item) => (
              <div
                key={item.id}
                className={clsx(
                  'px-4 py-3 border-b border-gray-50 hover:bg-gray-50 group',
                  currentQuestion?.toLowerCase() === item.question.toLowerCase() && 'bg-primary-50'
                )}
              >
                <div className="flex items-start gap-3">
                  <button
                    onClick={() => onReplay(item.question)}
                    className="mt-0.5 p-1 rounded hover:bg-primary-100 text-gray-400 hover:text-primary-600 transition-colors"
                    title="Run this query again"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 truncate">{item.question}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(item.timestamp)}
                      </span>
                      <span>{item.rowCount} rows</span>
                      <span>{item.executionTime.toFixed(0)}ms</span>
                      <span className={clsx(
                        'px-1.5 py-0.5 rounded',
                        item.confidence >= 0.8 ? 'bg-green-100 text-green-700' :
                        item.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      )}>
                        {Math.round(item.confidence * 100)}%
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      removeFromHistory(item.id)
                    }}
                    className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-100 text-gray-400 hover:text-red-600 transition-all"
                    title="Remove from history"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="px-4 py-2 bg-gray-50 flex items-center justify-between">
            {history.length > 5 && (
              <button
                onClick={() => setShowAll(!showAll)}
                className="text-xs text-primary-600 hover:text-primary-700"
              >
                {showAll ? 'Show less' : `Show all ${history.length} queries`}
              </button>
            )}
            {history.length > 5 && <div />}
            <button
              onClick={clearHistory}
              className="flex items-center gap-1 text-xs text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-3 h-3" />
              Clear history
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
