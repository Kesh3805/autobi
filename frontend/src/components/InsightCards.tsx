'use client'

import { TrendingUp, TrendingDown, AlertTriangle, Target, BarChart2, Percent } from 'lucide-react'
import clsx from 'clsx'

interface Insight {
  type: string
  title: string
  description: string
  magnitude: number
  confidence: number
  priority: 'high' | 'medium' | 'low'
  metric?: string
}

interface InsightCardsProps {
  insights: Insight[]
}

const InsightIcon = ({ type, magnitude }: { type: string; magnitude: number }) => {
  switch (type) {
    case 'trend_change':
      return magnitude > 0 
        ? <TrendingUp className="w-5 h-5 text-green-500" />
        : <TrendingDown className="w-5 h-5 text-red-500" />
    case 'trend_direction':
      return magnitude > 0 
        ? <TrendingUp className="w-5 h-5 text-blue-500" />
        : <TrendingDown className="w-5 h-5 text-orange-500" />
    case 'outlier':
      return <AlertTriangle className="w-5 h-5 text-amber-500" />
    case 'concentration':
      return <Target className="w-5 h-5 text-purple-500" />
    case 'volatility':
      return <BarChart2 className="w-5 h-5 text-gray-500" />
    case 'sample_size':
      return <AlertTriangle className="w-5 h-5 text-gray-400" />
    default:
      return <Percent className="w-5 h-5 text-gray-500" />
  }
}

const priorityColors = {
  high: 'border-l-red-500 bg-red-50',
  medium: 'border-l-amber-500 bg-amber-50',
  low: 'border-l-gray-300 bg-gray-50',
}

export default function InsightCards({ insights }: InsightCardsProps) {
  if (!insights.length) return null

  return (
    <div className="space-y-3">
      <h3 className="font-medium text-gray-900 flex items-center gap-2">
        <span className="text-lg">💡</span>
        Insights Detected
      </h3>
      
      <div className="grid gap-3 md:grid-cols-2">
        {insights.map((insight, i) => (
          <div
            key={i}
            className={clsx(
              'p-4 rounded-lg border-l-4 border border-gray-200',
              priorityColors[insight.priority]
            )}
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5">
                <InsightIcon type={insight.type} magnitude={insight.magnitude} />
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 text-sm mb-1">
                  {insight.title}
                </h4>
                <p className="text-sm text-gray-600">
                  {insight.description}
                </p>
                <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                  <span className={clsx(
                    'px-2 py-0.5 rounded-full',
                    insight.confidence >= 0.8 ? 'bg-green-100 text-green-700' :
                    insight.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-gray-100 text-gray-600'
                  )}>
                    {Math.round(insight.confidence * 100)}% confidence
                  </span>
                  <span className="capitalize">{insight.priority} priority</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
