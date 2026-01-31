'use client'

import { useEffect, useCallback } from 'react'

interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  meta?: boolean
  action: () => void
  description: string
}

interface UseKeyboardShortcutsOptions {
  enabled?: boolean
}

export function useKeyboardShortcuts(
  shortcuts: KeyboardShortcut[],
  options: UseKeyboardShortcutsOptions = {}
) {
  const { enabled = true } = options

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return

      // Ignore if user is typing in an input
      const target = event.target as HTMLElement
      const isTyping = ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || 
                       target.isContentEditable

      for (const shortcut of shortcuts) {
        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase()
        const ctrlMatch = shortcut.ctrl ? (event.ctrlKey || event.metaKey) : true
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey
        const altMatch = shortcut.alt ? event.altKey : !event.altKey

        if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
          // Allow some shortcuts even when typing
          if (isTyping && !shortcut.ctrl && !shortcut.meta) {
            continue
          }

          event.preventDefault()
          shortcut.action()
          return
        }
      }
    },
    [shortcuts, enabled]
  )

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])
}

// Common shortcuts hook
export function useAppShortcuts({
  onSearch,
  onEscape,
  onToggleTheme,
  onToggleHistory,
}: {
  onSearch?: () => void
  onEscape?: () => void
  onToggleTheme?: () => void
  onToggleHistory?: () => void
}) {
  const shortcuts: KeyboardShortcut[] = []

  if (onSearch) {
    shortcuts.push({
      key: 'k',
      ctrl: true,
      action: onSearch,
      description: 'Focus search',
    })
    shortcuts.push({
      key: '/',
      action: onSearch,
      description: 'Focus search',
    })
  }

  if (onEscape) {
    shortcuts.push({
      key: 'Escape',
      action: onEscape,
      description: 'Close/Cancel',
    })
  }

  if (onToggleTheme) {
    shortcuts.push({
      key: 'd',
      ctrl: true,
      shift: true,
      action: onToggleTheme,
      description: 'Toggle dark mode',
    })
  }

  if (onToggleHistory) {
    shortcuts.push({
      key: 'h',
      ctrl: true,
      action: onToggleHistory,
      description: 'Toggle history',
    })
  }

  useKeyboardShortcuts(shortcuts)
}

// Keyboard shortcuts help component
export function KeyboardShortcutsHelp() {
  const shortcuts = [
    { keys: ['Ctrl', 'K'], description: 'Focus query input' },
    { keys: ['/'], description: 'Focus query input' },
    { keys: ['Enter'], description: 'Submit query (in input)' },
    { keys: ['Ctrl', 'Enter'], description: 'Submit query' },
    { keys: ['Esc'], description: 'Close panel / Clear input' },
    { keys: ['Ctrl', 'H'], description: 'Toggle history' },
    { keys: ['Ctrl', 'Shift', 'D'], description: 'Toggle dark mode' },
    { keys: ['↑', '↓'], description: 'Navigate suggestions' },
  ]

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
        Keyboard Shortcuts
      </h3>
      <div className="space-y-2">
        {shortcuts.map(({ keys, description }, i) => (
          <div key={i} className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">{description}</span>
            <div className="flex gap-1">
              {keys.map((key, j) => (
                <kbd
                  key={j}
                  className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs font-mono"
                >
                  {key}
                </kbd>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
