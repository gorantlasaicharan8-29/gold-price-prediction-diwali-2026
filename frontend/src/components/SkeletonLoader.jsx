import React from 'react'

export function MetricSkeleton() {
  return (
    <div className="skeleton-metric-card">
      <div className="skeleton-line skeleton-title" />
      <div className="skeleton-line skeleton-value" />
      <div className="skeleton-line skeleton-sub" />
    </div>
  )
}

export function ChartSkeleton({ height = 320 }) {
  return (
    <div className="skeleton-chart-card" style={{ height }}>
      <div className="skeleton-chart-header">
        <div className="skeleton-line skeleton-title" />
        <div className="skeleton-line skeleton-p" />
      </div>
      <div className="skeleton-chart-body" />
    </div>
  )
}

export function TableSkeleton({ rows = 4 }) {
  return (
    <div className="skeleton-table">
      <div className="skeleton-line skeleton-title" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton-row">
          <div className="skeleton-line" style={{ width: '25%' }} />
          <div className="skeleton-line" style={{ width: '15%' }} />
          <div className="skeleton-line" style={{ width: '15%' }} />
          <div className="skeleton-line" style={{ width: '15%' }} />
          <div className="skeleton-line" style={{ width: '15%' }} />
        </div>
      ))}
    </div>
  )
}
