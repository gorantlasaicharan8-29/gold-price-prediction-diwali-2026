import React, { useEffect, useState } from 'react'
import { Scale, RefreshCw, AlertCircle, Info } from 'lucide-react'
import { getWeightPrediction } from '../services/api'
import RangeBar from './RangeBar'

const formatMoney = (val) =>
  val == null
    ? '—'
    : `₹${Number(val).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`

const QUICK_WEIGHTS = [1, 2, 5, 8, 10, 12, 15]

export default function GoldWeightCalculator() {
  const [weight, setWeight] = useState(5)
  const [inputVal, setInputVal] = useState('5')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchPrediction = async (w) => {
    const num = parseFloat(w)
    if (isNaN(num) || num < 1 || num > 15) {
      setError('Please select a valid gold weight between 1g and 15g.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const res = await getWeightPrediction(num)
      setData(res)
    } catch (err) {
      setError('Unable to retrieve the weight-based prediction. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPrediction(weight)
  }, [weight])

  const handleSliderChange = (e) => {
    const val = parseFloat(e.target.value)
    setWeight(val)
    setInputVal(val.toString())
  }

  const handleInputChange = (e) => {
    const raw = e.target.value
    setInputVal(raw)
    const num = parseFloat(raw)
    if (!isNaN(num) && num >= 1 && num <= 15) {
      setWeight(num)
    }
  }

  const handleQuickSelect = (w) => {
    setWeight(w)
    setInputVal(w.toString())
  }

  return (
    <div className="fin-panel" style={{ marginTop: 24 }}>
      <div className="panel-header">
        <div className="panel-title-group">
          <Scale className="panel-icon" size={18} style={{ color: 'var(--brand-gold)' }} />
          <span className="panel-title">Gold Weight Price Calculator</span>
        </div>
        <span className="pill-badge pill-amber">1g – 15g WEIGHT CONVERSION</span>
      </div>

      <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20, lineHeight: 1.5 }}>
        Calculate the predicted Diwali 2026 Gold 999 price for any custom weight from 1g to 15g.
        Values are computed proportionally from the official 10g Linear Regression baseline.
      </p>

      {/* Input Controls Container */}
      <div
        style={{
          background: 'var(--bg-card-alt)',
          padding: '20px',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
          marginBottom: '20px',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
            flexWrap: 'wrap',
            marginBottom: '16px',
          }}
        >
          <label htmlFor="weight-input" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-main)' }}>
            Selected Weight (Grams):
          </label>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              id="weight-input"
              type="number"
              min="1"
              max="15"
              step="0.1"
              value={inputVal}
              onChange={handleInputChange}
              aria-label="Gold weight in grams"
              style={{
                width: '90px',
                padding: '8px 12px',
                fontSize: '16px',
                fontWeight: 700,
                fontFamily: 'var(--font-mono)',
                textAlign: 'right',
                borderRadius: '6px',
                border: '1px solid var(--border-medium, #cbd5e1)',
                background: 'var(--bg-card, #ffffff)',
                color: 'var(--text-main, #0f172a)',
                boxShadow: 'var(--shadow-sm)',
              }}
            />
            <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-muted)' }}>g</span>
          </div>
        </div>

        {/* Range Slider */}
        <div style={{ marginBottom: '16px' }}>
          <label htmlFor="weight-slider" className="sr-only" style={{ display: 'none' }}>
            Adjust weight slider
          </label>
          <input
            id="weight-slider"
            type="range"
            min="1"
            max="15"
            step="0.1"
            value={weight}
            onChange={handleSliderChange}
            aria-label="Gold weight range slider from 1 to 15 grams"
            aria-valuemin={1}
            aria-valuemax={15}
            aria-valuenow={weight}
            style={{
              width: '100%',
              height: '6px',
              accentColor: 'var(--brand-gold, #d97706)',
              cursor: 'pointer',
            }}
          />
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '11px',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              marginTop: '4px',
            }}
          >
            <span>1g</span>
            <span>5g</span>
            <span>10g</span>
            <span>15g</span>
          </div>
        </div>

        {/* Quick Selection Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', marginRight: '4px' }}>Quick Select:</span>
          {QUICK_WEIGHTS.map((w) => (
            <button
              key={w}
              type="button"
              onClick={() => handleQuickSelect(w)}
              className={`pill-badge ${weight === w ? 'pill-amber' : 'pill-teal'}`}
              style={{
                cursor: 'pointer',
                border: weight === w ? '1px solid var(--brand-gold)' : '1px solid transparent',
                padding: '4px 10px',
                fontSize: '12px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {w}g
            </button>
          ))}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div
          style={{
            padding: '12px 16px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '6px',
            color: 'var(--brand-red, #ef4444)',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '20px',
          }}
        >
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Output Display */}
      {loading ? (
        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={20} className="spin" style={{ marginBottom: '8px' }} />
          <div>Calculating price for {weight}g...</div>
        </div>
      ) : data ? (
        <div>
          {/* Main Price Box */}
          <div
            style={{
              background: 'var(--bg-card-alt)',
              padding: '20px',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              marginBottom: '20px',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                flexWrap: 'wrap',
                gap: '16px',
              }}
            >
              <div>
                <span className="ticker-label">PREDICTED GOLD 999 PRICE ({data.weight_grams}g)</span>
                <div
                  style={{
                    fontSize: '32px',
                    fontWeight: 800,
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--brand-gold, #d97706)',
                    margin: '6px 0',
                  }}
                >
                  {formatMoney(data.predicted_price)}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Target Weight: <strong style={{ color: 'var(--text-main)' }}>{data.weight_grams} grams</strong>
                </div>
              </div>

              <div
                style={{
                  textAlign: 'right',
                  fontSize: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Reference Date: </span>
                  <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-main)' }}>
                    {data.reference_date} (Diwali)
                  </strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Selected Model: </span>
                  <strong style={{ color: 'var(--text-main)' }}>{data.model}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Base 10g Price: </span>
                  <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-main)' }}>
                    {formatMoney(data.price_per_10g)}
                  </strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Price per Gram: </span>
                  <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-main)' }}>
                    {formatMoney(data.price_per_gram)}
                  </strong>
                </div>
              </div>
            </div>

            {/* Range Bar */}
            {data.lower_estimate && data.upper_estimate && (
              <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
                <RangeBar
                  lower={data.lower_estimate}
                  reference={data.predicted_price}
                  upper={data.upper_estimate}
                  unit={`per ${data.weight_grams}g`}
                />
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
