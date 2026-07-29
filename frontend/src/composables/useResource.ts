// Copyright (c) 2026 Blueway Consulting LLC.
// Licensed under the LGPL-3.0 License. See LICENSE file for details.

import api from '@/utils/client/api'
import { reactive } from 'vue'

interface ResourceOptions {
  url: string
  cache?: string
  initialData?: any
  auto?: boolean
  transform?: (data: any) => any
  onError?: (error: any) => void
  onSuccess?: (data: any) => void
}

interface ResourceState {
  data: any
  loading: boolean
  error: any
}

export function createResource(options: ResourceOptions) {
  const state = reactive<ResourceState>({
    data: options.initialData || null,
    loading: false,
    error: null,
  })

  const fetch = async (params?: any) => {
    state.loading = true
    state.error = null

    try {
      const response = await api.post('/api/method/' + options.url, params)
      let data = response.data

      if (options.transform) {
        data = options.transform(data)
      }

      state.data = data
      state.loading = false

      if (options.onSuccess) {
        options.onSuccess(data)
      }

      return data
    } catch (error: any) {
      state.error = error
      state.loading = false

      if (options.onError) {
        options.onError(error)
      }

      throw error
    }
  }

  const submit = async (params?: any) => {
    return fetch(params)
  }

  const reload = async () => {
    return fetch()
  }

  const reset = () => {
    state.data = options.initialData || null
    state.loading = false
    state.error = null
  }

  // Auto-fetch if enabled
  if (options.auto) {
    fetch()
  }

  return {
    ...state,
    fetch,
    submit,
    reload,
    reset,
  }
}
