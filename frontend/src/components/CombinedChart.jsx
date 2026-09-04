import React, { useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from 'recharts'
import { LineChart as LineIcon, Info, SlidersHorizontal } from 'lucide-react'

const formatMoney = (val) =>
  val == null
    ? '—'
    : `₹${Number(val).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`

const formatDate = (val) =>
  val
    ? new Date(`${val}T00:00:00`).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : '—'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null

  return (
    <div className="fin-chart-tooltip">
      <div className="tooltip-date">{formatDate(label)}</div>
      {payload.map((item, idx) => (
        <div key={idx} className="tooltip-row">
          <span className="tooltip-dot" style={{ backgroundColor: item.color }} />
          <span className="tooltip-name">{item.name}:</span>
          <strong className="tooltip-val">{formatMoney(item.value)}</strong>
        </div>
      ))}
    </div>
  )
}

export default function CombinedChart({
  historical = [],
  forecast = [],
  title = 'IBJA Gold 999 Price & Forecast Path',
  subtitle = 'Chronological historical IBJA observations (up to 01 Sep 2026) seamlessly joined with recursive model predictions.',
  height = 360,
}) {
  const [viewMode, setViewMode] = useState('all') // 'all', 'history', 'forecast'

  // Prepare combined series
  // Historical data points have { date, observed: gold_999_avg }
  // Forecast data points have { date, forecast: forecast_gold_999 }
  const histPoints = historical.map((h) => ({
    date: h.date,
    observed: h.gold_999_avg ?? h.gold_999_average,
    forecast: null,
  }))

  const fcPoints = forecast.map((f) => ({
    date: f.date,
    observed: null,
    forecast: f.forecast_gold_999,
  }))

  // Create combined array sorted by date
  let dataPoints = []
  if (viewMode === 'all') {
    // To connect history and forecast smoothly in the chart, add last historical point as start of forecast line if desired, or let ReferenceLine demarcate boundary
    dataPoints = [...histPoints, ...fcPoints]
  } else if (viewMode === 'history') {
    dataPoints = histPoints
  } else {
    dataPoints = fcPoints
  }

  const BOUNDARY_DATE = '2026-09-01'

  return (
    <div className="fin-chart-card">
      <div className="fin-chart-header">
        <div className="fin-chart-title-group">
          <div className="fin-chart-icon-box">
            <LineIcon size={18} />
          </div>
          <div>
            <h3>{title}</h3>
            {subtitle && <p className="fin-chart-sub">{subtitle}</p>}
          </div>
        </div>

        <div className="fin-chart-controls">
          <div className="view-toggle">
            <button
              className={`toggle-btn ${viewMode === 'all' ? 'active' : ''}`}
              onClick={() => setViewMode('all')}
            >
              Full Series
            </button>
            <button
              className={`toggle-btn ${viewMode === 'history' ? 'active' : ''}`}
              onClick={() => setViewMode('history')}
            >
              Observed Only
            </button>
            <button
              className={`toggle-btn ${viewMode === 'forecast' ? 'active' : ''}`}
              onClick={() => setViewMode('forecast')}
            >
              Forecast Only
            </button>
          </div>
        </div>
      </div>

      <div className="fin-chart-legend">
        <div className="legend-item">
          <span className="legend-line legend-observed" />
          <span>Observed IBJA Target (INR/10g)</span>
        </div>
        <div className="legend-item">
          <span className="legend-line legend-forecast" />
          <span>Recursive Linear Regression Forecast</span>
        </div>
        <div className="legend-item">
          <span className="legend-line legend-boundary" />
          <span>Forecast Boundary (01 Sep 2026)</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={dataPoints}
          margin={{ top: 16, right: 24, left: 12, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis
            dataKey="date"
            tickFormatter={(v) => formatDate(v).slice(0, 6)}
            tick={{ fill: '#475569', fontSize: 11, fontFamily: 'DM Mono, monospace' }}
            axisLine={{ stroke: '#cbd5e1' }}
            tickLine={false}
            minTickGap={32}
          />
          <YAxis
            tickFormatter={(v) => `₹${Math.round(v / 1000)}k`}
            tick={{ fill: '#475569', fontSize: 11, fontFamily: 'DM Mono, monospace' }}
            axisLine={false}
            tickLine={false}
            width={52}
            domain={['auto', 'auto']}
          />
          <Tooltip content={<CustomTooltip />} />
          
          {viewMode === 'all' && (
            <ReferenceLine
              x={BOUNDARY_DATE}
              stroke="#64748b"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={{
                value: 'Forecast Start (02 Sep 2026)',
                fill: '#475569',
                fontSize: 10,
                position: 'top',
              }}
            />
          )}

          {(viewMode === 'all' || viewMode === 'history') && (
            <Line
              type="monotone"
              dataKey="observed"
              name="Observed IBJA 999"
              stroke="#0d9488"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#0d9488' }}
              connectNulls={false}
            />
          )}

          {(viewMode === 'all' || viewMode === 'forecast') && (
            <Line
              type="monotone"
              dataKey="forecast"
              name="Recursive Forecast"
              stroke="#d97706"
              strokeWidth={2.5}
              strokeDasharray="5 3"
              dot={false}
              activeDot={{ r: 5, fill: '#d97706' }}
              connectNulls={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      <div className="fin-chart-note">
        <Info size={14} className="note-icon" />
        <span>
          <strong>Methodology Note:</strong> Forecast values represent model-generated recursive Linear Regression estimates based on forecasted market signals and imputed OHLC features. They differ from actual observed market prices.
        </span>
      </div>
    </div>
  )
}
