// API Configuration
// Uses environment variable for production, falls back to /api for local development
const getApiBase = () => {
  const envUrl = import.meta.env.VITE_API_URL
  if (envUrl) {
    // Remove trailing slash if present
    return envUrl.endsWith('/') ? envUrl.slice(0, -1) : envUrl
  }
  // For local development, use relative path
  return '/api'
}

export const API_BASE = getApiBase()

// Helper function to get full API URL
export const getApiUrl = (endpoint) => {
  const base = API_BASE
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${base}${path}`
}

// Log API base for debugging (only in development)
if (import.meta.env.DEV) {
  console.log('API Base URL:', API_BASE)
}


