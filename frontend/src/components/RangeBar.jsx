import React from 'react'

const formatMoney = (val) =>
  val == null
    ? '—'
    : `₹${Number(val).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`

export default function RangeBar({ lower, reference, upper, unit = 'per 10g' }) {
  if (!lower || !reference || !upper) return null

  // Calculate percentage placement along range track
  const minVal = Number(lower)
  const refVal = Number(reference)
  const maxVal = Number(upper)
  const rangeSpan = maxVal - minVal
  const refPosPct = rangeSpan > 0 ? Math.min(100, Math.max(0, ((refVal - minVal) / rangeSpan) * 100)) : 50

  return (
    <div className="range-bar-container">
      <div className="range-bar-header">
        <span className="range-bar-label">MODEL ESTIMATED RANGE</span>
        <span className="range-bar-span">
          Span: {formatMoney(rangeSpan)} {unit}
        </span>
      </div>

      <div className="range-track-wrapper">
        <div className="range-track-bg" />
        <div
          className="range-track-fill"
          style={{ width: '100%' }}
        />
        <div
          className="range-pin"
          style={{ left: `${refPosPct}%` }}
        >
          <div className="range-pin-head" />
          <div className="range-pin-line" />
        </div>
      </div>

      <div className="range-nodes">
        <div className="range-node node-low">
          <span className="node-tag">ESTIMATED LOWER (5th %ile)</span>
          <strong className="node-value">{formatMoney(minVal)}</strong>
        </div>

        <div className="range-node node-ref">
          <span className="node-tag">REFERENCE ESTIMATE</span>
          <strong className="node-value ref-value">{formatMoney(refVal)}</strong>
        </div>

        <div className="range-node node-high">
          <span className="node-tag">ESTIMATED UPPER (95th %ile)</span>
          <strong className="node-value">{formatMoney(maxVal)}</strong>
        </div>
      </div>
    </div>
  )
}
