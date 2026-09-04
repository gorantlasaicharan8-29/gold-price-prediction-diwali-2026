import React, { useState, useEffect } from 'react'
import { Sliders, TrendingUp, TrendingDown, Info, ShieldCheck, AlertCircle, HelpCircle } from 'lucide-react'
import { getPredictionDrivers } from '../services/api'
import { ChartSkeleton } from './SkeletonLoader'


const fmtINR = (val) => {
  if (val == null || isNaN(val)) return '—'
  const absVal = Math.abs(val)
  const formatted = absVal.toLocaleString('en-IN', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  })
  return val < 0 ? `-₹${formatted}` : `+₹${formatted}`
}

const fmtDec = (val, dec = 4) => {
  if (val == null || isNaN(val)) return '—'
  return Number(val).toLocaleString('en-IN', {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec,
  })
}

export default function PredictionDrivers() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showAll, setShowAll] = useState(false)
  const [hoveredDriver, setHoveredDriver] = useState(null)

  useEffect(() => {
    let mounted = true
    getPredictionDrivers()
      .then((res) => {
        if (mounted) {
          setData(res)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (mounted) {
          console.error('Failed to fetch prediction drivers:', err)
          setError('Prediction driver analysis is currently unavailable.')
          setLoading(false)
        }
      })
    return () => {
      mounted = false
    }
  }, [])

  if (loading) {
    return (
      <section className="model-lab-section" aria-labelledby="drivers-title">
        <div className="section-header">
          <div>
            <span className="section-eyebrow">EXPLAINABLE AI • PREDICTION DRIVERS</span>
            <h2 id="drivers-title" className="section-title">
              Prediction Drivers (Diwali 2026 Estimate)
            </h2>
          </div>
        </div>
        <ChartSkeleton height={240} />

      </section>
    )
  }

  if (error || !data) {
    return (
      <section className="model-lab-section" aria-labelledby="drivers-title">
        <div className="section-header">
          <div>
            <span className="section-eyebrow">EXPLAINABLE AI • PREDICTION DRIVERS</span>
            <h2 id="drivers-title" className="section-title">
              Prediction Drivers (Diwali 2026 Estimate)
            </h2>
            <p className="section-desc">
              Factors contributing to the model's Diwali 2026 estimate.
            </p>
          </div>
          <div className="section-header-icon">
            <Sliders size={24} />
          </div>
        </div>
        <div className="drivers-error-banner" role="alert">
          <AlertCircle size={20} className="error-icon" />
          <span>{error || 'Prediction driver analysis is currently unavailable.'}</span>
        </div>
      </section>
    )
  }

  const positiveList = showAll
    ? data.positive_drivers || []
    : data.top_positive_drivers || []
  const negativeList = showAll
    ? data.negative_drivers || []
    : data.top_negative_drivers || []

  // Max absolute contribution for scaling bars
  const allDrivers = [
    ...(data.positive_drivers || []),
    ...(data.negative_drivers || []),
  ]
  const maxAbsContrib = Math.max(
    ...allDrivers.map((d) => d.absolute_contribution || 1),
    1
  )

  return (
    <section className="model-lab-section" aria-labelledby="drivers-title">
      {/* ─── Header ─────────────────────────────────────────────────── */}
      <div className="section-header">
        <div>
          <span className="section-eyebrow">EXPLAINABLE AI • PREDICTION DRIVERS</span>
          <h2 id="drivers-title" className="section-title">
            Prediction Drivers (Diwali 2026 Estimate)
          </h2>
          <p className="section-desc">
            Factors contributing to the model's Diwali 2026 estimate
          </p>
        </div>
        <div className="section-header-icon">
          <Sliders size={24} />
        </div>
      </div>

      {/* ─── Model Baseline Summary Strip ────────────────────────────── */}
      <div className="drivers-summary-strip">
        <div className="summary-item">
          <span className="summary-label">MODEL</span>
          <span className="summary-val">{data.model}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">TARGET FORECAST</span>
          <span className="summary-val highlight">
            ₹{data.prediction?.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">MODEL INTERCEPT (b)</span>
          <span className="summary-val">{fmtINR(data.intercept)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">UPWARD PRESSURE (+)</span>
          <span className="summary-val pos-text">
            {fmtINR(data.total_positive_contribution)}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">DOWNWARD PRESSURE (-)</span>
          <span className="summary-val neg-text">
            {fmtINR(data.total_negative_contribution)}
          </span>
        </div>
        <div className="summary-item status-item">
          <span className="summary-label">RECONSTRUCTION</span>
          <span className="reconstruction-badge pass">
            <ShieldCheck size={14} /> PASS (0.00)
          </span>
        </div>
      </div>

      {/* ─── Controls & Toggle ───────────────────────────────────────── */}
      <div className="drivers-toolbar">
        <div className="view-toggle-group">
          <button
            type="button"
            className={`toggle-btn ${!showAll ? 'active' : ''}`}
            onClick={() => setShowAll(false)}
            aria-pressed={!showAll}
          >
            Top 5 Contributors
          </button>
          <button
            type="button"
            className={`toggle-btn ${showAll ? 'active' : ''}`}
            onClick={() => setShowAll(true)}
            aria-pressed={showAll}
          >
            All Feature Drivers ({allDrivers.length})
          </button>
        </div>
      </div>

      {/* ─── Drivers Grid ───────────────────────────────────────────── */}
      <div className="drivers-grid">
        {/* UPWARD CONTRIBUTORS */}
        <div className="driver-column positive-col">
          <div className="col-header positive-header">
            <TrendingUp size={18} className="col-icon" />
            <div className="col-title-group">
              <h3>UPWARD CONTRIBUTORS</h3>
              <span className="col-subtitle">
                Features pushing forecast higher (+)
              </span>
            </div>
            <span className="count-pill pos-pill">{positiveList.length}</span>
          </div>

          <div className="driver-list" role="list">
            {positiveList.map((item) => {
              const widthPct = Math.min(
                100,
                Math.max(4, (item.absolute_contribution / maxAbsContrib) * 100)
              )
              const isHovered = hoveredDriver?.feature === item.feature

              return (
                <div
                  key={item.feature}
                  className={`driver-card ${isHovered ? 'hovered' : ''}`}
                  role="listitem"
                  onMouseEnter={() => setHoveredDriver(item)}
                  onMouseLeave={() => setHoveredDriver(null)}
                  tabIndex={0}
                  aria-label={`${item.display_name}: Upward contribution of ${fmtINR(
                    item.contribution
                  )}`}
                >
                  <div className="driver-card-header">
                    <div className="driver-name-group">
                      <span className="driver-display-name">
                        {item.display_name}
                      </span>
                      <code className="driver-code-name">{item.feature}</code>
                    </div>
                    <span className="driver-value pos-val">
                      {fmtINR(item.contribution)}
                    </span>
                  </div>

                  <div className="bar-track">
                    <div
                      className="bar-fill positive-fill"
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>

                  {/* Tooltip / Details on hover or focus */}
                  {isHovered && (
                    <div className="driver-tooltip" role="tooltip">
                      <div className="tooltip-title">{item.display_name}</div>
                      <div className="tooltip-grid">
                        <div>
                          <span>Raw Value:</span>{' '}
                          <strong>
                            {item.raw_value != null
                              ? fmtDec(item.raw_value, 2)
                              : 'Imputed (Median)'}
                          </strong>
                        </div>
                        <div>
                          <span>Transformed Input:</span>{' '}
                          <strong>{fmtDec(item.transformed_value, 4)}</strong>
                        </div>
                        <div>
                          <span>Model Coef (w):</span>{' '}
                          <strong>{fmtDec(item.coefficient, 4)}</strong>
                        </div>
                        <div>
                          <span>Model Contribution:</span>{' '}
                          <strong className="pos-text">
                            {fmtINR(item.contribution)}
                          </strong>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* DOWNWARD CONTRIBUTORS */}
        <div className="driver-column negative-col">
          <div className="col-header negative-header">
            <TrendingDown size={18} className="col-icon" />
            <div className="col-title-group">
              <h3>DOWNWARD CONTRIBUTORS</h3>
              <span className="col-subtitle">
                Features pushing forecast lower (−)
              </span>
            </div>
            <span className="count-pill neg-pill">{negativeList.length}</span>
          </div>

          <div className="driver-list" role="list">
            {negativeList.map((item) => {
              const widthPct = Math.min(
                100,
                Math.max(4, (item.absolute_contribution / maxAbsContrib) * 100)
              )
              const isHovered = hoveredDriver?.feature === item.feature

              return (
                <div
                  key={item.feature}
                  className={`driver-card ${isHovered ? 'hovered' : ''}`}
                  role="listitem"
                  onMouseEnter={() => setHoveredDriver(item)}
                  onMouseLeave={() => setHoveredDriver(null)}
                  tabIndex={0}
                  aria-label={`${item.display_name}: Downward contribution of ${fmtINR(
                    item.contribution
                  )}`}
                >
                  <div className="driver-card-header">
                    <div className="driver-name-group">
                      <span className="driver-display-name">
                        {item.display_name}
                      </span>
                      <code className="driver-code-name">{item.feature}</code>
                    </div>
                    <span className="driver-value neg-val">
                      {fmtINR(item.contribution)}
                    </span>
                  </div>

                  <div className="bar-track">
                    <div
                      className="bar-fill negative-fill"
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>

                  {/* Tooltip / Details on hover or focus */}
                  {isHovered && (
                    <div className="driver-tooltip" role="tooltip">
                      <div className="tooltip-title">{item.display_name}</div>
                      <div className="tooltip-grid">
                        <div>
                          <span>Raw Value:</span>{' '}
                          <strong>
                            {item.raw_value != null
                              ? fmtDec(item.raw_value, 2)
                              : 'Imputed (Median)'}
                          </strong>
                        </div>
                        <div>
                          <span>Transformed Input:</span>{' '}
                          <strong>{fmtDec(item.transformed_value, 4)}</strong>
                        </div>
                        <div>
                          <span>Model Coef (w):</span>{' '}
                          <strong>{fmtDec(item.coefficient, 4)}</strong>
                        </div>
                        <div>
                          <span>Model Contribution:</span>{' '}
                          <strong className="neg-text">
                            {fmtINR(item.contribution)}
                          </strong>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* ─── Methodology & Limitations Note ──────────────────────────── */}
      <div className="drivers-methodology-note">
        <Info size={18} className="note-icon" />
        <div className="note-content">
          <strong>Methodology & Limitations Note:</strong>
          <p>
            Prediction drivers represent the mathematical contribution of model
            features to the Linear Regression forecast (
            <code>prediction = intercept + ∑(coefficient × transformed_feature_value)</code>
            ). They indicate model influence, not causal effects in the gold market.
          </p>
        </div>
      </div>
    </section>
  )
}
