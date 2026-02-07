// API Configuration
// Uses environment variable for production, falls back to /api for local development
export const API_BASE = import.meta.env.VITE_API_URL || '/api'

// Helper function to get full API URL
export const getApiUrl = (endpoint) => {
  const base = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${base}${path}`
}


