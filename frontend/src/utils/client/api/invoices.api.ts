// Copyright (c) 2026 Enerlinq.
// Licensed under the LGPL-3.0 License. See LICENSE file for details.

import api from './api'

export interface CreateInvoiceParams {
  employee: string
  start_date: string
  end_date: string
  customer: string
  project: string
  item: string
}

export interface CreateInvoiceResponse {
  success: boolean
  invoice_name: string
  total_billable_hours: number
  rate: number
  total_amount: number
  timesheets: string[]
  message: string
}

export interface Invoice {
  name: string
  customer: string
  posting_date: string
  due_date: string
  grand_total: number
  status: string
  project?: string
}

export interface GetInvoicesParams {
  filters?: any
  limit?: number
  start?: number
  order_by?: string
}

export interface GetInvoicesResponse {
  data: Invoice[]
  total_count: number
}

export const createInvoiceFromBillableHours = async (params: CreateInvoiceParams): Promise<CreateInvoiceResponse> => {
  const response = await api.post(
    '/api/method/chronotally.chronotally.api_timesheet.create_invoice_from_billable_hours',
    params
  )
  return response.data.message
}

export const getInvoices = async (params?: GetInvoicesParams): Promise<GetInvoicesResponse> => {
  const {
    filters,
    limit = 10,
    start = 0,
    order_by = 'modified desc'
  } = params || {}

  const response = await api.get('/api/resource/Sales Invoice', {
    params: {
      fields: JSON.stringify(['name', 'customer', 'posting_date', 'due_date', 'grand_total', 'status', 'project']),
      filters: filters ? JSON.stringify(filters) : undefined,
      limit_page_length: limit,
      limit_start: start,
      order_by: order_by
    }
  })

  // Frappe returns total_count in the response when using pagination
  const totalCount = response.data.total_count || response.data.data.length

  return {
    data: response.data.data,
    total_count: totalCount
  }
}
