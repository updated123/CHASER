// API Configuration
// Uses environment variable for production, falls back to http://localhost:8000/api for local development
const getApiBase = () => {
  const envUrl = import.meta.env.VITE_API_URL
  
  if (envUrl) {
    // Remove trailing slash if present
    let url = envUrl.endsWith('/') ? envUrl.slice(0, -1) : envUrl
    
    // If URL doesn't end with /api, add it (for production deployments)
    // But only if it's not localhost (localhost already has /api in components)
    if (!url.includes('localhost') && !url.endsWith('/api')) {
      url = `${url}/api`
    }
    
    return url
  }
  
  // For local development, use localhost backend
  return 'http://localhost:8000/api'
}

export const API_BASE = getApiBase()

// Helper function to get full API URL
export const getApiUrl = (endpoint) => {
  const base = API_BASE
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${base}${path}`
}

// Log API base for debugging
console.log('🔗 API Base URL:', API_BASE)
console.log('🌍 Environment:', import.meta.env.MODE)
console.log('📡 VITE_API_URL:', import.meta.env.VITE_API_URL || 'Not set')


