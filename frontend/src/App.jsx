import React, { useEffect, useState } from 'react'
import { BrowserRouter, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import {
  Activity,
  BarChart3,
  CalendarDays,
  CircleAlert,
  Database,
  Gauge,
  LineChart as LineIcon,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  WifiOff,
  Menu,
  X,
  TrendingUp,
  Award,
  Layers,
  ArrowRight,
  BookOpen,
  Info,
} from 'lucide-react'

import {
  getDiwaliPrediction,
  getForecast,
  getHealth,
  getHistoricalData,
  getModelComparison,
  getModelInfo,
} from './services/api'

import ModelComparison from './components/ModelComparison'
import DataIntegrityBadge from './components/DataIntegrityBadge'
import RangeBar from './components/RangeBar'
import CombinedChart from './components/CombinedChart'
import MarketContextTicker from './components/MarketContextTicker'
import PredictionDrivers from './components/PredictionDrivers'
import WhatIfAnalysis from './components/WhatIfAnalysis'
import GoldWeightCalculator from './components/GoldWeightCalculator'
import ErrorBoundary from './components/ErrorBoundary'
import { MetricSkeleton, ChartSkeleton, TableSkeleton } from './components/SkeletonLoader'


import './App.css'

// ─── Formatters ──────────────────────────────────────────────────────────────

const money = (val) =>
  val == null
    ? '—'
    : `₹${Number(val).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`

const percent = (val) =>
  val == null ? '—' : `${Number(val).toFixed(2)}%`

const r2Fmt = (val) =>
  val == null ? '—' : Number(val).toFixed(4)

const dateLabel = (val) =>
  val
    ? new Date(`${val}T00:00:00`).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : '—'

const todayLabel = () =>
  new Date().toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })

// ─── Data Hook ───────────────────────────────────────────────────────────────

function useData() {
  const [data, setData] = useState({
    prediction: null,
    forecast: [],
    historical: [],
    model: null,
    comparison: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [apiOnline, setApiOnline] = useState(null)

  const loadAll = async () => {
    setLoading(true)
    setError(false)
    try {
      await getHealth()
      setApiOnline(true)
    } catch {
      setApiOnline(false)
      setError(true)
      setLoading(false)
      return
    }

    try {
      const [prediction, forecast, historical, model, comparison] = await Promise.all([
        getDiwaliPrediction(),
        getForecast(),
        getHistoricalData(),
        getModelInfo(),
        getModelComparison(),
      ])
      setData({ prediction, forecast, historical, model, comparison })
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [])

  return { ...data, loading, error, apiOnline, retry: loadAll }
}

// ─── Shared UI Elements ──────────────────────────────────────────────────────

function Header({ apiOnline }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    setMobileOpen(false)
  }, [location])

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <NavLink to="/" className="brand-link">
          <div className="brand-icon">
            <Sparkles size={20} />
          </div>
          <div className="brand-text">
            <span className="brand-title">Gold Price Intelligence</span>
            <span className="brand-subtitle">Diwali 2026 Financial Analytics</span>
          </div>
        </NavLink>

        <nav className={`nav-menu ${mobileOpen ? 'mobile-open' : ''}`}>
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            <Gauge size={16} /> Dashboard
          </NavLink>
          <NavLink to="/forecast" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            <LineIcon size={16} /> Forecast Desk
          </NavLink>
          <NavLink to="/model" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            <BarChart3 size={16} /> Model Lab
          </NavLink>
          <NavLink to="/about" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            <Database size={16} /> Methodology
          </NavLink>
        </nav>

        <div className="header-status-badge">
          <span
            className={`status-dot-pulse ${
              apiOnline === true ? 'dot-online' : apiOnline === false ? 'dot-offline' : ''
            }`}
          />
          <span>{apiOnline === true ? 'API Connected' : apiOnline === false ? 'API Offline' : 'Connecting...'}</span>
        </div>

        <button className="mobile-menu-btn" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Toggle menu">
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>
    </header>
  )
}

function Footer() {
  return (
    <footer className="app-footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <b>Gold Price Intelligence</b>
          <p>
            An institutional-grade analytics dashboard for IBJA Gold 999 price prediction during Diwali 2026. Built with FastAPI and React.
          </p>
        </div>
        <div className="footer-col">
          <h4>Target Specification</h4>
          <ul>
            <li>Commodity: IBJA Gold 999</li>
            <li>Quote Unit: INR per 10g</li>
            <li>Diwali Date: 08 Nov 2026</li>
          </ul>
        </div>
        <div className="footer-col">
          <h4>ML Architecture</h4>
          <ul>
            <li>Model: Linear Regression</li>
            <li>Split: Chronological</li>
            <li>Feature Count: 46 Predictors</li>
          </ul>
        </div>
        <div className="footer-col">
          <h4>Data Sources</h4>
          <ul>
            <li>IBJA Official Historicals</li>
            <li>Yahoo Finance Int'l Gold</li>
            <li>USD/INR FX Rates</li>
          </ul>
        </div>
      </div>

      <div className="footer-disclaimer">
        <strong>DISCLAIMER:</strong> All forecasts presented are model-derived mathematical estimates generated via recursive time-series forecasting. They should be interpreted as analytical projections for informational and educational evaluation, not guaranteed financial advice or official spot rates.
      </div>
    </footer>
  )
}

function ErrorState({ retry }) {
  return (
    <div className="state-box error-box">
      <CircleAlert size={36} className="state-icon" />
      <p>Unable to connect to the Gold Price Prediction service.</p>
      <button className="btn-retry" onClick={retry}>
        <RefreshCw size={15} /> Retry Connection
      </button>
    </div>
  )
}

// ─── DASHBOARD PAGE (/) ──────────────────────────────────────────────────────

function Dashboard({ api }) {
  if (api.loading && !api.prediction) {
    return (
      <div className="page-wrapper">
        <ChartSkeleton height={220} />
        <div style={{ height: 20 }} />
        <ChartSkeleton height={380} />
      </div>
    )
  }

  if (api.error && !api.prediction) {
    return <ErrorState retry={api.retry} />
  }

  const p = api.prediction
  const lastHist = api.historical.length > 0 ? api.historical[api.historical.length - 1] : null
  const prevHist = api.historical.length > 1 ? api.historical[api.historical.length - 2] : null

  // Calculate daily change in historical data
  const currentPrice = lastHist ? (lastHist.gold_999_avg ?? lastHist.gold_999_average) : null
  const prevPrice = prevHist ? (prevHist.gold_999_avg ?? prevHist.gold_999_average) : null
  const priceChange = currentPrice && prevPrice ? currentPrice - prevPrice : null
  const priceChangePct = priceChange && prevPrice ? (priceChange / prevPrice) * 100 : null

  return (
    <div className="page-wrapper">
      {/* ── Dashboard Hero Header ── */}
      <div className="dashboard-hero">
        <div className="hero-main-title">
          <h1>India Gold 999 Market Intelligence</h1>
          <p>
            Real-time analytics and recursive ML price projections leading up to Diwali 2026.
          </p>
        </div>
        <div className="hero-badges">
          <span className="pill-badge pill-teal">
            <Activity size={13} /> As of {dateLabel(lastHist?.date) || todayLabel()}
          </span>
          <span className="pill-badge pill-amber">
            <ShieldCheck size={13} /> IBJA Target: INR / 10g
          </span>
        </div>
      </div>

      {/* ── Market Context Signals Ticker ── */}
      <MarketContextTicker forecast={api.forecast} historical={api.historical} />

      {/* ── Primary Spotlight Grid ── */}
      <div className="fin-grid-2">
        {/* Left Panel: Latest Observed Market Snapshot */}
        <div className="fin-panel">
          <div className="panel-header">
            <div className="panel-title-group">
              <span className="panel-title">Latest Observed IBJA Target</span>
            </div>
            <span className="pill-badge pill-teal">OBSERVED</span>
          </div>

          <div style={{ padding: '8px 0' }}>
            <span className="ticker-label">IBJA GOLD 999 AVERAGE</span>
            <div style={{ fontSize: 36, fontWeight: 800, fontFamily: 'var(--font-mono)', margin: '8px 0' }}>
              {money(currentPrice)}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 13 }}>
              {priceChange != null && (
                <span
                  style={{
                    color: priceChange >= 0 ? 'var(--brand-emerald)' : 'var(--brand-red)',
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <TrendingUp size={16} style={{ transform: priceChange < 0 ? 'rotate(180deg)' : 'none' }} />
                  {priceChange >= 0 ? '+' : ''}
                  {money(priceChange)} ({priceChangePct >= 0 ? '+' : ''}
                  {percent(priceChangePct)})
                </span>
              )}
              <span style={{ color: 'var(--text-muted)' }}>vs previous business day</span>
            </div>
          </div>

          <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--border-subtle)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <span className="ticker-label">OBSERVATION DATE</span>
              <strong style={{ display: 'block', fontSize: 14, fontFamily: 'var(--font-mono)', marginTop: 4 }}>
                {dateLabel(lastHist?.date)}
              </strong>
            </div>
            <div>
              <span className="ticker-label">HISTORICAL DATA POINTS</span>
              <strong style={{ display: 'block', fontSize: 14, fontFamily: 'var(--font-mono)', marginTop: 4 }}>
                {api.historical.length} Business Days
              </strong>
            </div>
          </div>
        </div>

        {/* Right Panel: Frozen Diwali 2026 Forecast Spotlight */}
        <div className="diwali-spotlight-card">
          <div className="spotlight-head">
            <div>
              <span className="spotlight-eyebrow">DIWALI 2026 FORECAST SPOTLIGHT</span>
              <div className="spotlight-date">08 November 2026</div>
            </div>
            <div className="spotlight-badge">
              <CalendarDays size={14} /> Sunday
            </div>
          </div>

          <div className="spotlight-hero-price">
            <span className="spotlight-price-label">MODEL-DERIVED REFERENCE ESTIMATE</span>
            <div className="spotlight-price-value">{money(p?.diwali_reference_estimate?.forecast)}</div>
            <span className="spotlight-price-unit">INR per 10 grams</span>
          </div>

          <RangeBar
            lower={p?.estimated_range?.lower}
            reference={p?.diwali_reference_estimate?.forecast}
            upper={p?.estimated_range?.upper}
          />

          <div className="spotlight-nav-days">
            <div className="day-box">
              <span>PREVIOUS BUSINESS DAY</span>
              <strong>{money(p?.previous_business_day?.forecast)}</strong>
              <small>{dateLabel(p?.previous_business_day?.date)}</small>
            </div>
            <div className="day-box">
              <span>NEXT BUSINESS DAY</span>
              <strong>{money(p?.next_business_day?.forecast)}</strong>
              <small>{dateLabel(p?.next_business_day?.date)}</small>
            </div>
          </div>
        </div>
      </div>

      {/* ── Combined Historical vs Forecast Chart ── */}
      <CombinedChart historical={api.historical} forecast={api.forecast} />

      {/* ── Data Integrity Checklist ── */}
      <DataIntegrityBadge />
    </div>
  )
}

// ─── FORECAST DESK PAGE (/forecast) ──────────────────────────────────────────

function ForecastDesk({ api }) {
  if (api.loading && !api.prediction) {
    return (
      <div className="page-wrapper">
        <ChartSkeleton height={380} />
      </div>
    )
  }

  if (api.error && !api.prediction) {
    return <ErrorState retry={api.retry} />
  }

  const p = api.prediction

  return (
    <div className="page-wrapper">
      <div className="dashboard-hero">
        <div className="hero-main-title">
          <h1>Forecast Desk</h1>
          <p>
            Recursive business-day price projection series from 02 Sep 2026 through 09 Nov 2026.
          </p>
        </div>
        <div className="hero-badges">
          <span className="pill-badge pill-amber">
            <Layers size={13} /> Horizon: 49 Business Days
          </span>
        </div>
      </div>

      {/* Diwali Spotlight Card */}
      <div className="diwali-spotlight-card" style={{ marginBottom: 28 }}>
        <div className="spotlight-head">
          <div>
            <span className="spotlight-eyebrow">OFFICIAL DIWALI TARGET ESTIMATE</span>
            <div className="spotlight-date">08 November 2026 (Diwali)</div>
          </div>
          <span className="pill-badge pill-amber">FROZEN FORECAST</span>
        </div>

        <div className="spotlight-hero-price">
          <span className="spotlight-price-label">MODEL REFERENCE ESTIMATE (INR/10g)</span>
          <div className="spotlight-price-value">{money(p?.diwali_reference_estimate?.forecast)}</div>
        </div>

        <RangeBar
          lower={p?.estimated_range?.lower}
          reference={p?.diwali_reference_estimate?.forecast}
          upper={p?.estimated_range?.upper}
        />
      </div>

      {/* Gold Weight Price Calculator */}
      <ErrorBoundary fallbackMessage="Gold Weight Price Calculator is currently loading or unavailable.">
        <GoldWeightCalculator />
      </ErrorBoundary>

      {/* Full Combined Chart */}
      <CombinedChart
        historical={api.historical}
        forecast={api.forecast}
        title="Full Price Path Transition — Historical to Forecast"
        height={400}
      />

      {/* Prediction Drivers Section */}
      <ErrorBoundary fallbackMessage="Prediction Drivers analysis is currently loading or unavailable.">
        <PredictionDrivers />
      </ErrorBoundary>

      {/* What-If Scenario Analysis Section */}
      <ErrorBoundary fallbackMessage="What-If Scenario Analysis is currently loading or unavailable.">
        <WhatIfAnalysis />
      </ErrorBoundary>



      {/* Methodology & Evaluation Metrics Grid */}
      <div className="fin-grid-2">
        <div className="fin-panel">
          <div className="panel-header">
            <span className="panel-title">Recursive Forecasting Protocol</span>
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6 }}>
            The Linear Regression model generates target predictions step-by-step. At each step $t$, the predicted gold price is recursively inserted into the target history to calculate lag features for step $t+1$. Exogenous market inputs (International Gold & USD/INR) are forecasted independently using AutoReg models.
          </p>

          <div style={{ marginTop: 20, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div style={{ background: 'var(--bg-card-alt)', padding: 12, borderRadius: 6 }}>
              <span className="ticker-label">PRIMARY ALGORITHM</span>
              <strong style={{ display: 'block', fontSize: 14, color: 'var(--text-main)', marginTop: 4 }}>
                Linear Regression
              </strong>
            </div>
            <div style={{ background: 'var(--bg-card-alt)', padding: 12, borderRadius: 6 }}>
              <span className="ticker-label">HOLDOUT EVALUATION</span>
              <strong style={{ display: 'block', fontSize: 14, color: 'var(--brand-teal-dark)', marginTop: 4 }}>
                Test Set (26 obs)
              </strong>
            </div>
          </div>
        </div>

        <div className="fin-panel">
          <div className="panel-header">
            <span className="panel-title">Model Evaluation Metrics</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div style={{ background: 'var(--bg-card-alt)', padding: 14, borderRadius: 6 }}>
              <span className="ticker-label">TEST MAPE</span>
              <strong style={{ display: 'block', fontSize: 20, fontFamily: 'var(--font-mono)', color: 'var(--brand-teal-dark)', margin: '4px 0' }}>
                {percent(api.model?.test?.MAPE)}
              </strong>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Mean Absolute % Error</span>
            </div>

            <div style={{ background: 'var(--bg-card-alt)', padding: 14, borderRadius: 6 }}>
              <span className="ticker-label">TEST R²</span>
              <strong style={{ display: 'block', fontSize: 20, fontFamily: 'var(--font-mono)', color: 'var(--text-main)', margin: '4px 0' }}>
                {r2Fmt(api.model?.test?.R2)}
              </strong>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Coefficient of Determination</span>
            </div>

            <div style={{ background: 'var(--bg-card-alt)', padding: 14, borderRadius: 6 }}>
              <span className="ticker-label">TEST MAE</span>
              <strong style={{ display: 'block', fontSize: 20, fontFamily: 'var(--font-mono)', color: 'var(--text-main)', margin: '4px 0' }}>
                {money(api.model?.test?.MAE)}
              </strong>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Mean Absolute Error</span>
            </div>

            <div style={{ background: 'var(--bg-card-alt)', padding: 14, borderRadius: 6 }}>
              <span className="ticker-label">TEST RMSE</span>
              <strong style={{ display: 'block', fontSize: 20, fontFamily: 'var(--font-mono)', color: 'var(--text-main)', margin: '4px 0' }}>
                {money(api.model?.test?.RMSE)}
              </strong>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Root Mean Squared Error</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── MODEL LAB PAGE (/model) ──────────────────────────────────────────────────

function ModelLab({ api }) {
  if (api.loading && !api.model) {
    return (
      <div className="page-wrapper">
        <TableSkeleton rows={4} />
      </div>
    )
  }

  if (api.error && !api.model) {
    return <ErrorState retry={api.retry} />
  }

  const m = api.model

  return (
    <div className="page-wrapper">
      <div className="dashboard-hero">
        <div className="hero-main-title">
          <h1>Model Lab & Candidate Evaluation</h1>
          <p>
            Chronological model selection benchmark, holdout test results, and data integrity audits.
          </p>
        </div>
        <div className="hero-badges">
          <span className="pill-badge pill-teal">
            <Award size={13} /> Selected: Linear Regression
          </span>
        </div>
      </div>

      {/* Final Test Performance Banner */}
      <div className="fin-panel" style={{ marginBottom: 28, background: 'linear-gradient(135deg, #0f766e 0%, #0f172a 100%)', color: 'white' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: '#99f6e4', letterSpacing: 1 }}>
              FINAL UNTOUCHED TEST PERFORMANCE (26 OBS)
            </span>
            <h3 style={{ fontSize: 24, fontWeight: 800, color: 'white', marginTop: 4 }}>
              Selected Algorithm: {m?.model}
            </h3>
          </div>
          <ShieldCheck size={32} style={{ color: '#2dd4bf' }} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginTop: 20 }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.08)', padding: 14, borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }}>
            <span style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>TEST MAE</span>
            <strong style={{ display: 'block', fontSize: 22, color: 'white', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
              {money(m?.test?.MAE)}
            </strong>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.08)', padding: 14, borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }}>
            <span style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>TEST RMSE</span>
            <strong style={{ display: 'block', fontSize: 22, color: 'white', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
              {money(m?.test?.RMSE)}
            </strong>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.08)', padding: 14, borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }}>
            <span style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>TEST MAPE</span>
            <strong style={{ display: 'block', fontSize: 22, color: '#facc15', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
              {percent(m?.test?.MAPE)}
            </strong>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.08)', padding: 14, borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }}>
            <span style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>TEST R²</span>
            <strong style={{ display: 'block', fontSize: 22, color: 'white', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
              {r2Fmt(m?.test?.R2)}
            </strong>
          </div>
        </div>
      </div>

      {/* Model Comparison Table Component */}
      <ModelComparison models={api.comparison} />

      {/* Data Integrity Checklist */}
      <DataIntegrityBadge />
    </div>
  )
}

// ─── ABOUT PAGE (/about) ──────────────────────────────────────────────────────

function AboutPage() {
  return (
    <div className="page-wrapper">
      <div className="dashboard-hero">
        <div className="hero-main-title">
          <h1>System Architecture & Technical Methodology</h1>
          <p>
            Comprehensive documentation of data sources, feature engineering, leakage prevention, model evaluation, forecasting protocols, and analytical constraints.
          </p>
        </div>
        <div className="hero-badges">
          <span className="pill-badge pill-teal">
            <BookOpen size={13} /> Technical Documentation
          </span>
          <span className="pill-badge pill-amber">
            <ShieldCheck size={13} /> Audit Status: VERIFIED
          </span>
        </div>
      </div>

      {/* ─── 1. End-to-End Methodology Process Flow ──────────────────── */}
      <div className="fin-panel" style={{ marginBottom: 28 }}>
        <div className="panel-header">
          <span className="panel-title">1. End-to-End System Methodology Pipeline</span>
        </div>
        <div className="pipeline-flow-container">
          <div className="flow-step">
            <span className="step-num">01</span>
            <span className="step-name">Data Collection</span>
            <span className="step-desc">IBJA Gold 999, Spot Gold & USD/INR</span>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <span className="step-num">02</span>
            <span className="step-name">Validation & Audit</span>
            <span className="step-desc">168 trading days, 0 imputed targets</span>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <span className="step-num">03</span>
            <span className="step-name">Feature Taxonomy</span>
            <span className="step-desc">46 features across 9 categories</span>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <span className="step-num">04</span>
            <span className="step-name">Time-Aware Split</span>
            <span className="step-desc">117 Train / 25 Val / 26 Test</span>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <span className="step-num">05</span>
            <span className="step-name">Model Selection</span>
            <span className="step-desc">Linear Regression (Lowest RMSE)</span>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <span className="step-num">06</span>
            <span className="step-name">Test Evaluation</span>
            <span className="step-desc">MAPE ≈ 1.42%, R² ≈ 0.8409</span>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <span className="step-num">07</span>
            <span className="step-name">Recursive Forecast</span>
            <span className="step-desc">49 business days to Diwali 2026</span>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <span className="step-num">08</span>
            <span className="step-name">XAI & What-If</span>
            <span className="step-desc">Prediction drivers & 5 scenarios</span>
          </div>
        </div>
      </div>

      {/* ─── 2. Data Sources & Target Specification ──────────────────── */}
      <div className="fin-grid-2" style={{ marginBottom: 28 }}>
        <div className="fin-panel">
          <div className="panel-header">
            <span className="panel-title">2. Target Variable Specification</span>
          </div>
          <table className="info-mini-table">
            <tbody>
              <tr>
                <th>TARGET NAME</th>
                <td><code>target_gold_999</code></td>
              </tr>
              <tr>
                <th>PRIMARY ASSET</th>
                <td>IBJA Gold 999 (India Bullion & Jewellers Association)</td>
              </tr>
              <tr>
                <th>PURITY / FINENESS</th>
                <td>999 Fine Gold (~24 Karat)</td>
              </tr>
              <tr>
                <th>UNIT OF MEASURE</th>
                <td>INR per 10 grams (₹ / 10g)</td>
              </tr>
              <tr>
                <th>CONSTRUCTION</th>
                <td>Daily arithmetic average of IBJA AM and PM rates</td>
              </tr>
              <tr>
                <th>OBSERVATION COUNT</th>
                <td>168 business-day rows (2025-09-02 to 2026-09-01)</td>
              </tr>
              <tr>
                <th>TARGET IMPUTATION</th>
                <td><strong>None (0%)</strong> — Raw actuals only</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="fin-panel">
          <div className="panel-header">
            <span className="panel-title">3. Primary Data Sources</span>
          </div>
          <ul className="source-list">
            <li>
              <strong>IBJA Bullion Rates:</strong>
              <p>Official published morning (AM) and evening (PM) rates for 999 fine gold in Mumbai benchmark market.</p>
            </li>
            <li>
              <strong>Yahoo Finance International Spot Gold:</strong>
              <p>Global USD spot gold closing price (USD/t oz) and daily OHLC trading volumes.</p>
            </li>
            <li>
              <strong>USD/INR Exchange Rates:</strong>
              <p>Spot exchange rate (INR per 1 USD) tracking currency movements.</p>
            </li>
          </ul>
        </div>
      </div>

      {/* ─── 3. Feature Engineering Taxonomy ────────────────────────── */}
      <div className="fin-panel" style={{ marginBottom: 28 }}>
        <div className="panel-header">
          <span className="panel-title">4. Feature Engineering Taxonomy (46 Predictors)</span>
        </div>
        <div className="taxonomy-grid">
          <div className="taxonomy-card">
            <h4>Calendar Features (10)</h4>
            <p>Day of week, day of month, month, quarter, day of year, week of year, month start/end indicators, days to Diwali, is near Diwali.</p>
          </div>
          <div className="taxonomy-card">
            <h4>Historical Lags (6)</h4>
            <p>Target lags at t-1, t-2, t-3, t-5, t-7, t-14 built strictly via shift(1) to eliminate lookahead bias.</p>
          </div>
          <div className="taxonomy-card">
            <h4>Moving Averages (4)</h4>
            <p>3-day, 7-day, 14-day, and 30-day rolling arithmetic mean gold prices.</p>
          </div>
          <div className="taxonomy-card">
            <h4>Volatility Indicators (3)</h4>
            <p>7-day, 14-day, and 30-day rolling standard deviation of daily return percentages.</p>
          </div>
          <div className="taxonomy-card">
            <h4>Domestic Returns (3)</h4>
            <p>1-day, 3-day, and 7-day domestic price percentage returns.</p>
          </div>
          <div className="taxonomy-card">
            <h4>Spot Gold Features (9)</h4>
            <p>International gold OHLC prices, trading volume, 1d/3d/7d returns, and 7d/14d volatility.</p>
          </div>
          <div className="taxonomy-card">
            <h4>USD/INR Features (9)</h4>
            <p>USD/INR OHLC exchange rates, 1d/3d/7d returns, and 7d/14d volatility.</p>
          </div>
          <div className="taxonomy-card">
            <h4>Derived Market Proxy (1)</h4>
            <p>Implied INR gold proxy computed as (Spot Gold USD × USD/INR rate).</p>
          </div>
          <div className="taxonomy-card">
            <h4>Diwali Proximity (1)</h4>
            <p>Countdown scalar (days to Diwali 2026) and 30-day seasonal window flag.</p>
          </div>
        </div>
      </div>

      {/* ─── 4. Data Leakage Prevention Checklist ───────────────────── */}
      <div className="fin-panel" style={{ marginBottom: 28 }}>
        <div className="panel-header">
          <span className="panel-title">5. Data Leakage Prevention Audit Checklist</span>
        </div>
        <div className="leakage-audit-grid">
          <div className="audit-item pass">
            <ShieldCheck size={18} className="audit-icon" />
            <div>
              <strong>Same-Day Target Exclusions</strong>
              <p>Raw target components (AM/PM rates) on day t excluded from predictor inputs.</p>
            </div>
          </div>
          <div className="audit-item pass">
            <ShieldCheck size={18} className="audit-icon" />
            <div>
              <strong>Strict Shift(1) Lags</strong>
              <p>All target lags and rolling windows computed using observations ≤ t-1 only.</p>
            </div>
          </div>
          <div className="audit-item pass">
            <ShieldCheck size={18} className="audit-icon" />
            <div>
              <strong>Train-Only Preprocessor Fit</strong>
              <p>Median imputer parameters fitted strictly on X_train and reused on validation/test.</p>
            </div>
          </div>
          <div className="audit-item pass">
            <ShieldCheck size={18} className="audit-icon" />
            <div>
              <strong>Chronological Split Isolation</strong>
              <p>No random shuffling. Future observations never used in past training.</p>
            </div>
          </div>
          <div className="audit-item pass">
            <ShieldCheck size={18} className="audit-icon" />
            <div>
              <strong>Untouched Holdout Test Set</strong>
              <p>Test set (26 obs) completely isolated prior to model evaluation.</p>
            </div>
          </div>
          <div className="audit-item pass">
            <ShieldCheck size={18} className="audit-icon" />
            <div>
              <strong>No Future Actual Data</strong>
              <p>Future actual IBJA rates and market data were never accessed or leaked.</p>
            </div>
          </div>
        </div>
      </div>

      {/* ─── 5. Categorized Limitations ─────────────────────────────── */}
      <div className="fin-panel">
        <div className="panel-header">
          <span className="panel-title">6. Categorized System Limitations & Analytical Constraints</span>
        </div>
        <div className="limitations-grid">
          <div className="limit-box">
            <h4 style={{ color: 'var(--brand-amber)' }}>DATA LIMITATIONS</h4>
            <ul>
              <li>IBJA quotes are published only on active trading business days; weekends and holidays are non-contiguous.</li>
              <li>Historical window is limited to 168 observations (Sept 2025 – Sept 2026).</li>
              <li>Unobserved future OHLC inputs use train-fitted median imputation during recursive forecasting.</li>
            </ul>
          </div>

          <div className="limit-box">
            <h4 style={{ color: 'var(--brand-teal-dark)' }}>MODEL LIMITATIONS</h4>
            <ul>
              <li>Recursive multi-step forecasting accumulates predictor uncertainty over longer horizons.</li>
              <li>Linear Regression models assume constant linear slope coefficients ($w_i$) across all market regimes.</li>
              <li>Discontinuity gap (-8.25%) between latest actual (01 Sep) and first recursive step (02 Sep) reflects transition from actual lag memory to recursive state.</li>
            </ul>
          </div>

          <div className="limit-box">
            <h4 style={{ color: '#dc2626' }}>MARKET LIMITATIONS</h4>
            <ul>
              <li>Future exogenous market signals (Spot Gold USD & USD/INR) are projected via AutoReg models.</li>
              <li>Black swan geopolitical events, central bank gold purchases, or emergency tariff shifts cannot be foreseen by statistical lag models.</li>
              <li>Diwali 2026 (08 Nov) falls on a Sunday; its estimate is a model-derived interpolation, not a trading quote.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}


// ─── MAIN APP ROOT ────────────────────────────────────────────────────────────

export default function App() {
  const api = useData()

  return (
    <BrowserRouter>
      <div className="app-shell">
        <Header apiOnline={api.apiOnline} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard api={api} />} />
            <Route path="/forecast" element={<ForecastDesk api={api} />} />
            <Route path="/model" element={<ModelLab api={api} />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  )
}
