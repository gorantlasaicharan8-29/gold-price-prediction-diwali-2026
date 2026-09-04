const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`)
  if (!response.ok) throw new Error(`Request failed: ${response.status}`)
  return response.json()
}

export const getHealth = () => request('/health')
export const getModelInfo = () => request('/api/model-info')
export const getDiwaliPrediction = () => request('/api/diwali-prediction')
export const getForecast = () => request('/api/forecast')
export const getHistoricalData = () => request('/api/historical-data')
export const getModelComparison = () => request('/api/model-comparison')
export const getPredictionDrivers = () => request('/api/prediction-drivers')
export const getWhatIfAnalysis = () => request('/api/what-if')
export const getWeightPrediction = (weight) => request(`/api/weight-prediction?weight=${encodeURIComponent(weight)}`)



