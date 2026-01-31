'use client'

import { useTheme } from '@/context/ThemeContext'
import { Sun, Moon, Monitor } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

export default function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const themes = [
    { value: 'light', icon: Sun, label: 'Light' },
    { value: 'dark', icon: Moon, label: 'Dark' },
    { value: 'system', icon: Monitor, label: 'System' },
  ] as const

  const CurrentIcon = resolvedTheme === 'dark' ? Moon : Sun

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        aria-label="Toggle theme"
      >
        <CurrentIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-36 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50">
          {themes.map(({ value, icon: Icon, label }) => (
            <button
              key={value}
              onClick={() => {
                setTheme(value)
                setIsOpen(false)
              }}
              className={`
                w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors
                ${theme === value 
                  ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400' 
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }
              `}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
              {theme === value && (
                <span className="ml-auto text-primary-500">✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
