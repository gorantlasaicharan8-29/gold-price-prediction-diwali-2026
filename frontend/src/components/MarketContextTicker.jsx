import React from 'react'
import { DollarSign, Globe, TrendingUp, Cpu } from 'lucide-react'

const formatNum = (val, maxDec = 2) =>
  val == null
    ? '—'
    : Number(val).toLocaleString('en-IN', {
        minimumFractionDigits: maxDec,
        maximumFractionDigits: maxDec,
      })

export default function MarketContextTicker({ forecast = [], historical = [] }) {
  // Use first forecast row (nearest future step) or fallback
  const firstFc = forecast.length > 0 ? forecast[0] : null
  const lastHist = historical.length > 0 ? historical[historical.length - 1] : null

  return (
    <div className="market-ticker-grid">
      <div className="ticker-card">
        <div className="ticker-icon-box gold-usd">
          <DollarSign size={16} />
        </div>
        <div className="ticker-content">
          <span className="ticker-label">INTL GOLD (USD / t oz)</span>
          <strong className="ticker-val">
            ${formatNum(firstFc?.gold_usd_close_forecast ?? lastHist?.gold_usd_close)}
          </strong>
          <span className="ticker-sub">
            {firstFc ? 'Nearest forecast input' : 'Last observed close'}
          </span>
        </div>
      </div>

      <div className="ticker-card">
        <div className="ticker-icon-box usdinr">
          <Globe size={16} />
        </div>
        <div className="ticker-content">
          <span className="ticker-label">USD / INR EXCHANGE RATE</span>
          <strong className="ticker-val">
            ₹{formatNum(firstFc?.usdinr_close_forecast ?? lastHist?.usdinr_close, 4)}
          </strong>
          <span className="ticker-sub">
            {firstFc ? 'Nearest forecast input' : 'Last observed exchange'}
          </span>
        </div>
      </div>

      <div className="ticker-card">
        <div className="ticker-icon-box proxy">
          <TrendingUp size={16} />
        </div>
        <div className="ticker-content">
          <span className="ticker-label">GOLD INR PROXY (USD × FX)</span>
          <strong className="ticker-val">
            ₹{formatNum(firstFc?.gold_inr_proxy ?? ((lastHist?.gold_usd_close ?? 0) * (lastHist?.usdinr_close ?? 0)))}
          </strong>
          <span className="ticker-sub">Implied international value</span>
        </div>
      </div>

      <div className="ticker-card">
        <div className="ticker-icon-box engine">
          <Cpu size={16} />
        </div>
        <div className="ticker-content">
          <span className="ticker-label">FORECAST METHODOLOGY</span>
          <strong className="ticker-val model-name">Recursive Linear Reg.</strong>
          <span className="ticker-sub">AutoReg exogenous inputs</span>
        </div>
      </div>
    </div>
  )
}
