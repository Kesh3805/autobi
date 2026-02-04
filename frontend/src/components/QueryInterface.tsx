'use client'

import { useState, useRef, useEffect, useMemo, KeyboardEvent } from 'react'
import { Search, Loader2, Sparkles, Mic, MicOff, Clock, ChevronDown } from 'lucide-react'
import clsx from 'clsx'

interface QueryInterfaceProps {
  onQuery: (question: string) => void
  isLoading: boolean
  recentQueries?: string[]
}

const EXAMPLE_QUERIES = [
  'Show total sales by category',
  'What is the trend over time?',
  'Top 10 customers by revenue',
  'Average order value by month',
  'Distribution of prices',
  'Compare regions by profit',
  'Show me the bottom 5 products',
  'Monthly growth rate',
]

const SMART_SUGGESTIONS = [
  { pattern: /^show\s*$/i, suggestions: ['Show total', 'Show all', 'Show top 10', 'Show trend'] },
  { pattern: /^total\s*$/i, suggestions: ['Total sales by category', 'Total revenue by month', 'Total orders'] },
  { pattern: /^top\s*$/i, suggestions: ['Top 10 products', 'Top 5 customers', 'Top performing regions'] },
  { pattern: /^by\s*$/i, suggestions: ['by category', 'by month', 'by region', 'by customer'] },
  { pattern: /^compare\s*$/i, suggestions: ['Compare regions', 'Compare products', 'Compare months'] },
]

export default function QueryInterface({ onQuery, isLoading, recentQueries = [] }: QueryInterfaceProps) {
  const [question, setQuestion] = useState('')
  const [showSuggestionsState, setShowSuggestionsState] = useState(false)
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // Compute suggestions inline without storing in state to avoid infinite loops
  const suggestions = useMemo(() => {
    if (!question.trim()) {
      return []
    }

    // Check smart suggestions
    for (const { pattern, suggestions: sugg } of SMART_SUGGESTIONS) {
      if (pattern.test(question)) {
        return sugg
      }
    }

    // Filter example queries and recent queries
    const q = question.toLowerCase()
    const allQueries = [...new Set([...recentQueries, ...EXAMPLE_QUERIES])]
    const filtered = allQueries
      .filter(ex => ex.toLowerCase().includes(q) && ex.toLowerCase() !== q)
      .slice(0, 5)
    
    return filtered
  }, [question, recentQueries])

  // Compute whether to show suggestions without state updates
  const showSuggestions = showSuggestionsState && suggestions.length > 0 && question.trim().length > 0

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node)) {
        setShowSuggestionsState(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSubmit = () => {
    if (question.trim() && !isLoading) {
      onQuery(question.trim())
      setShowSuggestionsState(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (selectedSuggestion >= 0 && suggestions[selectedSuggestion]) {
        setQuestion(suggestions[selectedSuggestion])
        setShowSuggestionsState(false)
        setSelectedSuggestion(-1)
      } else {
        handleSubmit()
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedSuggestion(prev => Math.min(prev + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedSuggestion(prev => Math.max(prev - 1, -1))
    } else if (e.key === 'Escape') {
      setShowSuggestionsState(false)
      setSelectedSuggestion(-1)
    }
  }

  const selectSuggestion = (suggestion: string) => {
    setQuestion(suggestion)
    setShowSuggestionsState(false)
    setSelectedSuggestion(-1)
    inputRef.current?.focus()
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-3 mb-3">
        <Sparkles className="w-5 h-5 text-primary-500" />
        <h3 className="font-medium text-gray-900">Ask a question about your data</h3>
      </div>

      <div className="flex gap-3">
        <div className="flex-1 relative" ref={suggestionsRef}>
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
          <input
            ref={inputRef}
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => suggestions.length > 0 && setShowSuggestionsState(true)}
            placeholder="e.g., Show me total revenue by product category..."
            className={clsx(
              'w-full pl-12 pr-12 py-3 border border-gray-300 rounded-lg text-gray-900',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
              'placeholder:text-gray-400'
            )}
            disabled={isLoading}
            autoComplete="off"
          />
          
          {/* Mic button placeholder */}
          <button
            className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
            title="Voice input (coming soon)"
            disabled
          >
            <Mic className="w-5 h-5" />
          </button>

          {/* Suggestions dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden">
              {suggestions.map((suggestion, i) => (
                <button
                  key={suggestion}
                  onClick={() => selectSuggestion(suggestion)}
                  className={clsx(
                    'w-full px-4 py-2.5 text-left text-sm flex items-center gap-2 transition-colors',
                    selectedSuggestion === i 
                      ? 'bg-primary-50 text-primary-700' 
                      : 'text-gray-700 hover:bg-gray-50'
                  )}
                >
                  {recentQueries.includes(suggestion) ? (
                    <Clock className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  ) : (
                    <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  )}
                  <span className="truncate">{suggestion}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={handleSubmit}
          disabled={!question.trim() || isLoading}
          className={clsx(
            'px-6 py-3 rounded-lg font-medium transition-colors',
            'bg-primary-500 text-white hover:bg-primary-600',
            'disabled:bg-gray-300 disabled:cursor-not-allowed'
          )}
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            'Analyze'
          )}
        </button>
      </div>

      {/* Example queries */}
      <div className="mt-4 flex flex-wrap gap-2">
        {EXAMPLE_QUERIES.slice(0, 5).map((example) => (
          <button
            key={example}
            onClick={() => {
              setQuestion(example)
              onQuery(example)
            }}
            disabled={isLoading}
            className={clsx(
              'px-3 py-1.5 text-sm rounded-full border border-gray-200',
              'text-gray-600 hover:bg-gray-50 hover:border-gray-300 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  )
}
