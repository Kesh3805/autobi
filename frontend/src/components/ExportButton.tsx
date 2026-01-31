'use client'

import { useState, useRef, useEffect } from 'react'
import { Download, FileJson, FileSpreadsheet, Copy, Check, ChevronDown } from 'lucide-react'
import clsx from 'clsx'

interface ExportButtonProps {
  data: Record<string, any>[]
  columns: { name: string; type: string }[]
  filename?: string
}

export default function ExportButton({ data, columns, filename = 'export' }: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const exportCSV = () => {
    const headers = columns.map(c => c.name)
    const csvContent = [
      headers.join(','),
      ...data.map(row => 
        headers.map(h => {
          const val = row[h]
          if (val === null || val === undefined) return ''
          if (typeof val === 'string' && (val.includes(',') || val.includes('"') || val.includes('\n'))) {
            return `"${val.replace(/"/g, '""')}"`
          }
          return String(val)
        }).join(',')
      )
    ].join('\n')

    downloadFile(csvContent, `${filename}.csv`, 'text/csv')
    setIsOpen(false)
  }

  const exportJSON = () => {
    const jsonContent = JSON.stringify(data, null, 2)
    downloadFile(jsonContent, `${filename}.json`, 'application/json')
    setIsOpen(false)
  }

  const copyToClipboard = async () => {
    const headers = columns.map(c => c.name)
    const tsvContent = [
      headers.join('\t'),
      ...data.map(row => headers.map(h => row[h] ?? '').join('\t'))
    ].join('\n')

    try {
      await navigator.clipboard.writeText(tsvContent)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
    setIsOpen(false)
  }

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type: `${type};charset=utf-8;` })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  if (!data.length) return null

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border transition-colors',
          'text-gray-600 border-gray-200 hover:bg-gray-50 hover:border-gray-300'
        )}
      >
        <Download className="w-4 h-4" />
        Export
        <ChevronDown className={clsx('w-3 h-3 transition-transform', isOpen && 'rotate-180')} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg border border-gray-200 shadow-lg z-50 py-1">
          <button
            onClick={exportCSV}
            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            <FileSpreadsheet className="w-4 h-4 text-green-600" />
            Download CSV
          </button>
          <button
            onClick={exportJSON}
            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            <FileJson className="w-4 h-4 text-blue-600" />
            Download JSON
          </button>
          <div className="border-t border-gray-100 my-1" />
          <button
            onClick={copyToClipboard}
            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-green-600" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 text-gray-500" />
                Copy to clipboard
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}
