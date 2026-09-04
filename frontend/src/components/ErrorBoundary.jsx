import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('UI Component Error Boundary caught error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="drivers-error-banner" style={{ margin: '20px 0', padding: 20 }}>
          <AlertCircle size={22} className="error-icon" />
          <div>
            <strong style={{ display: 'block', fontSize: 14 }}>Component Rendering Notice</strong>
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              {this.props.fallbackMessage || 'This section is currently unavailable due to a rendering error.'}
            </span>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
