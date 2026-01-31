'use client'

import { useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement,
} from 'chart.js'
import { Line, Bar, Scatter, Pie, Doughnut } from 'react-chartjs-2'
import { Info, PieChart, BarChart2, TrendingUp, Circle } from 'lucide-react'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface ChartPanelProps {
  config: any
  reasoning: string
}

const chartIcons: Record<string, any> = {
  line: TrendingUp,
  bar: BarChart2,
  pie: PieChart,
  doughnut: Circle,
  scatter: Circle,
}

export default function ChartPanel({ config, reasoning }: ChartPanelProps) {
  const chartType = config?.type

  const ChartComponent = useMemo(() => {
    switch (chartType) {
      case 'line':
        return Line
      case 'bar':
        return Bar
      case 'scatter':
        return Scatter
      case 'pie':
        return Pie
      case 'doughnut':
        return Doughnut
      default:
        return Bar
    }
  }, [chartType])

  const ChartIcon = chartIcons[chartType] || BarChart2

  if (!config || !config.data) {
    return null
  }

  // Ensure responsive behavior
  const options = {
    ...config.options,
    responsive: true,
    maintainAspectRatio: false,
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ChartIcon className="w-4 h-4 text-primary-500" />
          <h3 className="font-medium text-gray-900">Visualization</h3>
          <span className="text-xs px-2 py-0.5 bg-gray-100 rounded text-gray-600 capitalize">
            {chartType}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <Info className="w-3.5 h-3.5" />
          <span>{reasoning}</span>
        </div>
      </div>

      {/* Chart */}
      <div className="p-4">
        <div className="h-80">
          <ChartComponent data={config.data} options={options} />
        </div>
      </div>
    </div>
  )
}
