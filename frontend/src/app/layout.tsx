import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/context/ThemeContext'
import { ToastProvider } from '@/context/ToastContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AutoBI - LLM-Powered Data Explorer',
  description: 'Upload CSV, ask questions in plain English, get smart charts and insights',
  keywords: ['data analytics', 'business intelligence', 'natural language query', 'data visualization'],
  authors: [{ name: 'AutoBI Team' }],
  openGraph: {
    title: 'AutoBI - LLM-Powered Data Explorer',
    description: 'Upload CSV, ask questions in plain English, get smart charts and insights',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors`}>
        <ThemeProvider>
          <ToastProvider>
            <ErrorBoundary>
              {children}
            </ErrorBoundary>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
