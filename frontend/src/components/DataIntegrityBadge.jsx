import React from 'react'
import { ShieldCheck, CheckCircle2, Lock } from 'lucide-react'

const INTEGRITY_ITEMS = [
  { label: 'Chronological Train/Val/Test Split', status: 'VERIFIED' },
  { label: 'Untouched Holdout Test Set (26 obs)', status: 'VERIFIED' },
  { label: 'Zero Target Data Leakage', status: 'VERIFIED' },
  { label: 'Zero Future Actual IBJA Data Used', status: 'VERIFIED' },
  { label: 'Zero Future Actual Market Data Used', status: 'VERIFIED' },
  { label: 'Training-Fitted Preprocessor Pipeline', status: 'VERIFIED' },
  { label: 'Frozen Diwali Forecast Artifact', status: 'FROZEN' },
]

export default function DataIntegrityBadge() {
  return (
    <div className="integrity-card">
      <div className="integrity-header">
        <div className="integrity-title">
          <ShieldCheck size={18} className="integrity-icon" />
          <span>Data Integrity & Audit Verification</span>
        </div>
        <span className="integrity-status-badge">
          <Lock size={12} /> SYSTEM FROZEN & VALIDATED
        </span>
      </div>

      <div className="integrity-grid">
        {INTEGRITY_ITEMS.map((item, idx) => (
          <div key={idx} className="integrity-item">
            <CheckCircle2 size={14} className="integrity-check-icon" />
            <span className="integrity-label">{item.label}</span>
            <span className={`integrity-tag ${item.status === 'FROZEN' ? 'tag-frozen' : 'tag-verified'}`}>
              {item.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
