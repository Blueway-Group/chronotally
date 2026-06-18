// Copyright (c) 2026 Enerlinq.
// Licensed under the LGPL-3.0 License. See LICENSE file for details.

import axios from 'axios'
import { appContext } from '@/stores/appContext'

// Helper function to get CSRF token from appContext
const getCSRFToken = (): string | null => {
  return appContext.csrfToken || null
}

// Create an axios instance with default configuration for Frappe API
const api = axios.create({
  baseURL: window.location.origin,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// Request interceptor to add CSRF token if needed
api.interceptors.request.use(
  (config) => {
    // Only add CSRF token for state-changing methods
    if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
      const csrfToken = getCSRFToken()

      if (csrfToken) {
        config.headers['X-Frappe-CSRF-Token'] = csrfToken
      } else {
        console.warn('CSRF token not found. Request may fail on mobile browsers.')
      }
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle authentication errors
      window.location.href = '/login?redirect-to=' + encodeURIComponent(window.location.pathname)
    } else if (error.response?.status === 403) {
      // CSRF token might be missing or invalid
      console.error('CSRF token error.')
      console.error('Error details:', error.response?.data)
    } else if (error.response?.status === 417) {
      // Mandatory error
      console.error('Request validation failed (417).')
      console.error('Error details:', error.response?.data)
    }
    return Promise.reject(error)
  }
)

export default api
