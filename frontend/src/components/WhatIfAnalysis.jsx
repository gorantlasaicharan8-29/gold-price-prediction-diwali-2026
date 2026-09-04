import React, { useState, useEffect } from 'react'
import { Layers, Info, AlertCircle, RefreshCw, CheckCircle2 } from 'lucide-react'
import { getWhatIfAnalysis } from '../services/api'
import { ChartSkeleton } from './SkeletonLoader'

const fmtINR = (val) => {
  if (val == null || isNaN(val)) return '—'
  const formatted = Math.abs(val).toLocaleString('en-IN', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  })
  return val < 0 ? `-₹${formatted}` : `₹${formatted}`
}

const fmtChange = (change, pct) => {
  if (change == null || isNaN(change)) return '—'
  const absFormatted = Math.abs(change).toLocaleString('en-IN', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  })
  const sign = change > 0 ? '+' : change < 0 ? '−' : ''
  const pctStr = pct != null ? ` (${sign}${Math.abs(pct).toFixed(2)}%)` : ''
  return change === 0
    ? 'Baseline Reference'
    : `${sign}₹${absFormatted}${pctStr}`
}

export default function WhatIfAnalysis() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedScenario, setSelectedScenario] = useState(null)

  const fetchData = () => {
    setLoading(true)
    setError(null)
    getWhatIfAnalysis()
      .then((res) => {
        setData(res)
        if (res?.scenarios?.length) {
          const base = res.scenarios.find((s) => s.is_baseline) || res.scenarios[0]
          setSelectedScenario(base)
        }
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to fetch what-if analysis:', err)
        setError('Scenario analysis is currently unavailable.')
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) {
    return (
      <section className="model-lab-section" aria-labelledby="whatif-title">
        <div className="section-header">
          <div>
            <span className="section-eyebrow">SENSITIVITY & SCENARIO STRESS-TESTING</span>
            <h2 id="whatif-title" className="section-title">
              What-If Scenario Analysis
            </h2>
          </div>
        </div>
        <ChartSkeleton height={280} />
      </section>
    )
  }

  if (error || !data || !data.scenarios?.length) {
    return (
      <section className="model-lab-section" aria-labelledby="whatif-title">
        <div className="section-header">
          <div>
            <span className="section-eyebrow">SENSITIVITY & SCENARIO STRESS-TESTING</span>
            <h2 id="whatif-title" className="section-title">
              What-If Scenario Analysis
            </h2>
            <p className="section-desc">
              Explore how the model-derived Diwali 2026 estimate changes under predefined market scenarios.
            </p>
          </div>
          <div className="section-header-icon">
            <Layers size={24} />
          </div>
        </div>
        <div className="drivers-error-banner" role="alert">
          <AlertCircle size={20} className="error-icon" />
          <span>{error || 'Scenario analysis is currently unavailable.'}</span>
          <button type="button" className="retry-btn" onClick={fetchData}>
            <RefreshCw size={14} /> Retry
          </button>
        </div>
      </section>
    )
  }

  const baselinePred = data.baseline_prediction
  const scenarios = data.scenarios

  // Calculate min & max predictions for bar chart scaling
  const minPred = Math.min(...scenarios.map((s) => s.prediction)) * 0.98
  const maxPred = Math.max(...scenarios.map((s) => s.prediction)) * 1.02
  const predRange = maxPred - minPred || 1

  return (
    <section className="model-lab-section" aria-labelledby="whatif-title">
      {/* ─── Section Header ─────────────────────────────────────────── */}
      <div className="section-header">
        <div>
          <span className="section-eyebrow">SENSITIVITY & SCENARIO STRESS-TESTING</span>
          <h2 id="whatif-title" className="section-title">
            What-If Scenario Analysis
          </h2>
          <p className="section-desc">
            Explore how the model-derived Diwali 2026 estimate changes under predefined market scenarios.
          </p>
        </div>
        <div className="section-header-icon">
          <Layers size={24} />
        </div>
      </div>

      {/* ─── Mandatory Disclaimer Banner ────────────────────────────── */}
      <div className="whatif-disclaimer-banner">
        <Info size={18} className="banner-icon" />
        <div className="banner-text">
          <strong>Mandatory Notice:</strong> These scenarios are sensitivity analysis, not additional forecasts or guaranteed future outcomes. They demonstrate model behavior under stress assumptions.
        </div>
      </div>

      {/* ─── Scenario Grid ──────────────────────────────────────────── */}
      <div className="whatif-cards-grid" role="list">
        {scenarios.map((scen) => {
          const isSelected = selectedScenario?.scenario === scen.scenario
          const isHigher = scen.change > 0
          const isLower = scen.change < 0

          let statusClass = 'baseline-card'
          let dirText = 'BASELINE FORECAST'
          if (isHigher) {
            statusClass = 'higher-card'
            dirText = 'Higher than baseline'
          } else if (isLower) {
            statusClass = 'lower-card'
            dirText = 'Lower than baseline'
          }

          return (
            <div
              key={scen.scenario}
              className={`whatif-card ${statusClass} ${isSelected ? 'selected' : ''}`}
              onClick={() => setSelectedScenario(scen)}
              role="listitem"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') setSelectedScenario(scen)
              }}
              aria-label={`${scen.display_name}: Estimate ${fmtINR(scen.prediction)}, ${dirText}`}
            >
              <div className="card-top-row">
                <span className="scen-display-name">{scen.display_name}</span>
                {scen.is_baseline ? (
                  <span className="scen-badge base-badge">
                    <CheckCircle2 size={12} /> BASELINE
                  </span>
                ) : (
                  <span className={`scen-badge ${isHigher ? 'high-badge' : 'low-badge'}`}>
                    {dirText}
                  </span>
                )}
              </div>

              <div className="scen-price-row">
                <span className="scen-price">{fmtINR(scen.prediction)}</span>
              </div>

              <div className="scen-diff-row">
                {scen.is_baseline ? (
                  <span className="diff-text base-diff">Official Model Reference</span>
                ) : (
                  <span className={`diff-text ${isHigher ? 'pos-diff' : 'neg-diff'}`}>
                    {fmtChange(scen.change, scen.change_percentage)}
                  </span>
                )}
              </div>

              <p className="scen-assumption">{scen.market_assumption}</p>
            </div>
          )
        })}
      </div>

      {/* ─── Visual Scenario Comparison Bar Chart ──────────────────── */}
      <div className="whatif-chart-panel">
        <div className="panel-title-row">
          <h3>Predefined Scenario Comparison (INR / 10g)</h3>
          <span className="baseline-indicator">
            Baseline Target: <strong>{fmtINR(baselinePred)}</strong>
          </span>
        </div>

        <div className="scenario-bars-list">
          {scenarios.map((scen) => {
            const widthPct = Math.min(
              100,
              Math.max(10, ((scen.prediction - minPred) / predRange) * 100)
            )
            const isSelected = selectedScenario?.scenario === scen.scenario
            const isHigher = scen.change > 0
            const isLower = scen.change < 0

            let barColorClass = 'base-bar'
            if (isHigher) barColorClass = 'high-bar'
            if (isLower) barColorClass = 'low-bar'

            return (
              <div
                key={scen.scenario}
                className={`scenario-bar-row ${isSelected ? 'row-active' : ''}`}
                onClick={() => setSelectedScenario(scen)}
              >
                <div className="row-label">
                  <span className="row-name">{scen.display_name}</span>
                  {scen.is_baseline && <span className="row-tag">MODEL BASE</span>}
                </div>

                <div className="row-track-container">
                  <div className="row-track">
                    <div
                      className={`row-fill ${barColorClass}`}
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                </div>

                <div className="row-val-group">
                  <span className="row-price">{fmtINR(scen.prediction)}</span>
                  {!scen.is_baseline && (
                    <span className={`row-delta ${isHigher ? 'pos-text' : 'neg-text'}`}>
                      {scen.change > 0 ? '+' : ''}
                      {scen.change_percentage?.toFixed(2)}%
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ─── Focused Detail Card ────────────────────────────────────── */}
      {selectedScenario && (
        <div className="whatif-detail-panel">
          <div className="detail-header">
            <h4>SCENARIO INSIGHT: {selectedScenario.display_name}</h4>
            <span className="detail-tag">
              {selectedScenario.is_baseline
                ? 'Baseline Model Reference'
                : selectedScenario.change > 0
                ? 'Upward Sensitivity Shift'
                : 'Downward Sensitivity Shift'}
            </span>
          </div>
          <div className="detail-body">
            <div className="detail-stat">
              <span className="stat-lbl">MODEL ESTIMATE</span>
              <strong className="stat-val">{fmtINR(selectedScenario.prediction)}</strong>
            </div>
            <div className="detail-stat">
              <span className="stat-lbl">VARIANCE FROM BASELINE</span>
              <strong
                className={`stat-val ${
                  selectedScenario.change > 0
                    ? 'pos-text'
                    : selectedScenario.change < 0
                    ? 'neg-text'
                    : ''
                }`}
              >
                {fmtChange(selectedScenario.change, selectedScenario.change_percentage)}
              </strong>
            </div>
            <div className="detail-stat">
              <span className="stat-lbl">MARKET ASSUMPTION</span>
              <span className="stat-desc">{selectedScenario.market_assumption}</span>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
