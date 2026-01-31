'use client'

import { useMemo } from 'react'
import { TrendingUp, TrendingDown, Hash, Activity, Percent, Target } from 'lucide-react'
import clsx from 'clsx'

interface Column {
  name: string
  type: string
}

interface SummaryStatsProps {
  data: Record<string, any>[]
  columns: Column[]
}

interface StatCard {
  label: string
  value: string
  subValue?: string
  icon: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  color: string
}

export default function SummaryStats({ data, columns }: SummaryStatsProps) {
  const stats = useMemo(() => {
    if (!data.length || !columns.length) return []

    const measureCols = columns.filter(c => c.type === 'measure')
    const cards: StatCard[] = []

    // Row count
    cards.push({
      label: 'Total Rows',
      value: data.length.toLocaleString(),
      icon: <Hash className="w-5 h-5" />,
      color: 'blue'
    })

    // First measure: Sum
    if (measureCols[0]) {
      const col = measureCols[0]
      const values = data.map(r => r[col.name]).filter(v => typeof v === 'number') as number[]
      if (values.length > 0) {
        const sum = values.reduce((a, b) => a + b, 0)
        const avg = sum / values.length
        
        cards.push({
          label: `Total ${formatLabel(col.name)}`,
          value: formatNumber(sum),
          subValue: `Avg: ${formatNumber(avg)}`,
          icon: <Activity className="w-5 h-5" />,
          color: 'green'
        })
      }
    }

    // Second measure: Average with range
    if (measureCols[1]) {
      const col = measureCols[1]
      const values = data.map(r => r[col.name]).filter(v => typeof v === 'number') as number[]
      if (values.length > 0) {
        const avg = values.reduce((a, b) => a + b, 0) / values.length
        const min = Math.min(...values)
        const max = Math.max(...values)
        
        cards.push({
          label: `Avg ${formatLabel(col.name)}`,
          value: formatNumber(avg),
          subValue: `${formatNumber(min)} - ${formatNumber(max)}`,
          icon: <Target className="w-5 h-5" />,
          color: 'purple'
        })
      }
    }

    // Calculate growth if we have ordered data with at least 2 rows
    if (measureCols[0] && data.length >= 2) {
      const col = measureCols[0]
      const first = data[0][col.name]
      const last = data[data.length - 1][col.name]
      
      if (typeof first === 'number' && typeof last === 'number' && first !== 0) {
        const change = ((last - first) / Math.abs(first)) * 100
        
        cards.push({
          label: 'Change',
          value: `${change >= 0 ? '+' : ''}${change.toFixed(1)}%`,
          subValue: `${formatNumber(first)} → ${formatNumber(last)}`,
          icon: change >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />,
          trend: change >= 0 ? 'up' : 'down',
          color: change >= 0 ? 'green' : 'red'
        })
      }
    }

    return cards.slice(0, 4)
  }, [data, columns])

  if (stats.length === 0) return null

  const colorClasses: Record<string, { bg: string; text: string; icon: string }> = {
    blue: { bg: 'bg-blue-50', text: 'text-blue-700', icon: 'text-blue-500' },
    green: { bg: 'bg-green-50', text: 'text-green-700', icon: 'text-green-500' },
    purple: { bg: 'bg-purple-50', text: 'text-purple-700', icon: 'text-purple-500' },
    red: { bg: 'bg-red-50', text: 'text-red-700', icon: 'text-red-500' },
    amber: { bg: 'bg-amber-50', text: 'text-amber-700', icon: 'text-amber-500' },
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((stat, i) => {
        const colors = colorClasses[stat.color] || colorClasses.blue
        return (
          <div
            key={i}
            className={clsx('rounded-lg p-4 border border-gray-100', colors.bg)}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                {stat.label}
              </span>
              <div className={colors.icon}>{stat.icon}</div>
            </div>
            <div className={clsx('text-2xl font-bold', colors.text)}>
              {stat.value}
            </div>
            {stat.subValue && (
              <div className="text-xs text-gray-500 mt-1">{stat.subValue}</div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function formatNumber(value: number): string {
  if (Math.abs(value) >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`
  }
  if (Math.abs(value) >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`
  }
  if (Math.abs(value) < 1 && value !== 0) {
    return value.toFixed(3)
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 })
}

function formatLabel(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}
