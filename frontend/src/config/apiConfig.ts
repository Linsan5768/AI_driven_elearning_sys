// API configuration with environment variable support
const getApiBaseUrl = (): string => {
  // Use Vite environment variable if available, otherwise default to localhost
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  // For production Docker builds, use relative path or backend service name
  if (import.meta.env.PROD) {
    // If backend is in same Docker network, use service name
    // Otherwise use window location for same-origin requests
    return typeof window !== 'undefined' 
      ? `${window.location.protocol}//${window.location.hostname}:8001/api`
      : 'http://backend:8001/api'
  }
  // Development default
  return 'http://127.0.0.1:8001/api'
}

const getBackendUrl = (): string => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL.replace('/api', '')
  }
  if (import.meta.env.PROD) {
    return typeof window !== 'undefined'
      ? `${window.location.protocol}//${window.location.hostname}:8001`
      : 'http://backend:8001'
  }
  return 'http://127.0.0.1:8001'
}

export const API_BASE_URL = getApiBaseUrl()
export const BACKEND_URL = getBackendUrl()
// Ollama URL: use proxy in production, or direct URL in development
const getOllamaUrl = (): string => {
  if (import.meta.env.VITE_OLLAMA_URL) {
    return import.meta.env.VITE_OLLAMA_URL
  }
  // In production (Docker), use Nginx proxy
  if (import.meta.env.PROD) {
    return '/ollama'
  }
  // Development: use localhost
  return 'http://127.0.0.1:11434'
}

export const OLLAMA_URL = getOllamaUrl()

