import React from 'react'
import { BarChart3, Check, Award, HelpCircle } from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const fmtNum = (value, dec = 2) =>
  value == null
    ? '—'
    : Number(value).toLocaleString('en-IN', {
        minimumFractionDigits: dec,
        maximumFractionDigits: dec,
      })

const fmtPercent = (value) =>
  value == null ? '—' : `${Number(value).toFixed(2)}%`

const fmtR2 = (value) => (value == null ? '—' : Number(value).toFixed(4))

export default function ModelComparison({ models = [] }) {
  if (!models || !models.length) return null

  return (
    <section className="model-lab-section" aria-labelledby="model-lab-title">
      <div className="section-header">
        <div>
          <span className="section-eyebrow">MODEL EVALUATION BENCHMARK</span>
          <h2 id="model-lab-title" className="section-title">
            Chronological Validation Benchmark (4 Models)
          </h2>
          <p className="section-desc">
            Four candidate machine learning algorithms were trained on the initial historical window (117 obs) and evaluated on a subsequent chronological validation window (25 obs). Model selection prioritized minimizing validation RMSE, MAE, and MAPE.
          </p>
        </div>
        <div className="section-header-icon">
          <BarChart3 size={24} />
        </div>
      </div>

      <div className="table-responsive">
        <table className="fin-table" aria-label="Validation metrics comparison for candidate models">
          <thead>
            <tr>
              <th scope="col">CANDIDATE MODEL</th>
              <th scope="col" className="text-right">MAE (INR)</th>
              <th scope="col" className="text-right">RMSE (INR)</th>
              <th scope="col" className="text-right">MAPE (%)</th>
              <th scope="col" className="text-right">VALIDATION R²</th>
              <th scope="col" className="text-center">SELECTION STATUS</th>
            </tr>
          </thead>
          <tbody>
            {models.map((item) => {
              const isSelected = item.selected
              return (
                <tr key={item.model} className={isSelected ? 'row-selected' : ''}>
                  <td className="font-semibold text-slate-900">
                    <div className="model-cell-name">
                      {isSelected && <Award size={16} className="badge-award-icon" />}
                      <span>{item.model}</span>
                    </div>
                  </td>
                  <td className="text-right font-mono">{fmtNum(item.MAE, 2)}</td>
                  <td className="text-right font-mono bold">{fmtNum(item.RMSE, 2)}</td>
                  <td className="text-right font-mono">{fmtPercent(item.MAPE)}</td>
                  <td className={`text-right font-mono ${Number(item.R2) < 0 ? 'text-amber-600' : ''}`}>
                    {fmtR2(item.R2)}
                  </td>
                  <td className="text-center">
                    <span className={`status-pill ${isSelected ? 'pill-selected' : 'pill-evaluated'}`}>
                      {isSelected ? (
                        <>
                          <Check size={12} /> SELECTED FOR FINAL FORECAST
                        </>
                      ) : (
                        'EVALUATED'
                      )}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="r2-note-box">
        <HelpCircle size={18} className="r2-note-icon" />
        <div>
          <strong>Validation R² Interpretation Note:</strong>
          <p>
            A negative validation R² on the chronological validation split reflects that the target mean in that specific window shifted relative to the training distribution. Selection was strictly determined by error metrics (RMSE, MAE, MAPE). The untouched test set provides the true final generalisation assessment.
          </p>
        </div>
      </div>

      <div className="model-chart-box">
        <h4 className="chart-box-title">Validation RMSE Comparison (Lower is Better)</h4>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={models} layout="vertical" margin={{ top: 8, right: 32, left: 40, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
            <XAxis
              type="number"
              tick={{ fill: '#475569', fontSize: 11, fontFamily: 'DM Mono, monospace' }}
              axisLine={{ stroke: '#cbd5e1' }}
              tickLine={false}
              tickFormatter={(v) => (v >= 1000 ? `₹${Math.round(v / 1000)}k` : `₹${v}`)}
            />
            <YAxis
              type="category"
              dataKey="model"
              width={160}
              tick={{ fill: '#0f172a', fontSize: 12, fontWeight: 600 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(value) => [`₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`, 'Validation RMSE']}
              cursor={{ fill: '#f8fafc' }}
            />
            <Bar dataKey="RMSE" radius={[0, 4, 4, 0]}>
              {models.map((entry) => (
                <Cell key={entry.model} fill={entry.selected ? '#0d9488' : '#94a3b8'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
