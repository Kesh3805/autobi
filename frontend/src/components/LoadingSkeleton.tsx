'use client'

import clsx from 'clsx'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={clsx(
        'animate-pulse bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 rounded',
        'bg-[length:200%_100%] animate-shimmer',
        className
      )}
    />
  )
}

export function QueryResultSkeleton() {
  return (
    <div className="space-y-6">
      {/* SQL Panel Skeleton */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <Skeleton className="h-5 w-32" />
          <div className="flex gap-4">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-12" />
            <Skeleton className="h-5 w-20 rounded-full" />
          </div>
        </div>
        <div className="bg-gray-900 rounded-lg p-4 space-y-2">
          <Skeleton className="h-4 w-3/4 bg-gray-700" />
          <Skeleton className="h-4 w-1/2 bg-gray-700" />
          <Skeleton className="h-4 w-2/3 bg-gray-700" />
        </div>
      </div>

      {/* Summary Stats Skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-5 w-5 rounded" />
            </div>
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-3 w-16 mt-2" />
          </div>
        ))}
      </div>

      {/* Chart Skeleton */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-4 w-48" />
        </div>
        <div className="p-4">
          <div className="h-80 flex items-end justify-around gap-4 pt-8">
            {[60, 80, 45, 90, 70, 55, 85].map((h, i) => (
              <Skeleton 
                key={i} 
                className="w-12 rounded-t" 
                style={{ height: `${h}%` }} 
              />
            ))}
          </div>
        </div>
      </div>

      {/* Table Skeleton */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-5 w-16" />
            <Skeleton className="h-4 w-12" />
          </div>
          <Skeleton className="h-8 w-24 rounded-lg" />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {[1, 2, 3, 4, 5].map((i) => (
                  <th key={i} className="px-4 py-3">
                    <Skeleton className="h-4 w-20" />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {[1, 2, 3, 4, 5].map((row) => (
                <tr key={row}>
                  {[1, 2, 3, 4, 5].map((col) => (
                    <td key={col} className="px-4 py-3">
                      <Skeleton className="h-4 w-full" />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export function SchemaSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <Skeleton className="h-5 w-28" />
      </div>
      <div className="p-4 space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-10 w-full rounded-md" />
        ))}
        <div className="pt-4 border-t border-gray-100 space-y-2">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-8 w-full rounded" />
          ))}
        </div>
      </div>
    </div>
  )
}

export function ChartSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-5 w-12 rounded-full" />
        </div>
        <Skeleton className="h-4 w-48" />
      </div>
      <div className="p-4">
        <div className="h-80 flex items-end justify-around gap-4 pt-8">
          {[60, 80, 45, 90, 70, 55, 85].map((h, i) => (
            <Skeleton 
              key={i} 
              className="w-12 rounded-t" 
              style={{ height: `${h}%` }} 
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export function InsightSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-start gap-3">
            <Skeleton className="h-8 w-8 rounded-lg flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-3 w-24 mt-2" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
