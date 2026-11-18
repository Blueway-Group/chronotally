// Copyright (c) 2026 Blueway Consulting LLC.
// Licensed under the LGPL-3.0 License. See LICENSE file for details.

import api from './api'

const REPORTS_API = '/api/method/chronotally.chronotally.api_timesheet'

// Global filters shared by every section of the reports page
export interface ReportFilters {
  start_date: string // YYYY-MM-DD
  end_date: string // YYYY-MM-DD
  customer?: string
  project?: string
  employee?: string
  include_drafts?: boolean
}

export type ReportGroupBy = 'project' | 'customer' | 'employee' | 'activity' | 'billable'
export type ReportMeasure = 'hours' | 'amount' | 'cost'
export type ReportPeriod = 'weekly' | 'monthly'

export interface ReportTotals {
  total_hours: number
  billable_hours: number
  utilization: number
  revenue: number
  cost: number
  margin: number
}

export interface ReportSummary extends ReportTotals {
  prior: ReportTotals & { start_date: string; end_date: string }
  unbilled_hours: number
  unbilled_amount: number
  unbilled_customers: number
}

export interface ReportHoursChart {
  buckets: string[]
  series: { label: string; values: number[] }[]
  group_by: ReportGroupBy
  measure: ReportMeasure
  period: ReportPeriod
}

export interface UnbilledCustomer {
  customer: string | null
  customer_name: string
  hours: number
  amount: number
}

const toParams = (filters: ReportFilters) => ({
  start_date: filters.start_date,
  end_date: filters.end_date,
  customer: filters.customer || undefined,
  project: filters.project || undefined,
  employee: filters.employee || undefined,
  include_drafts: filters.include_drafts ? 1 : 0
})

export const getReportSummary = async (filters: ReportFilters): Promise<ReportSummary> => {
  const response = await api.get(`${REPORTS_API}.get_report_summary`, { params: toParams(filters) })
  return response.data.message
}

export const getReportHoursChart = async (
  filters: ReportFilters,
  options: { group_by: ReportGroupBy; measure: ReportMeasure; period: ReportPeriod }
): Promise<ReportHoursChart> => {
  const response = await api.get(`${REPORTS_API}.get_report_hours_chart`, {
    params: { ...toParams(filters), ...options }
  })
  return response.data.message
}

export const getUnbilledByCustomer = async (filters: ReportFilters): Promise<UnbilledCustomer[]> => {
  const response = await api.get(`${REPORTS_API}.get_unbilled_by_customer`, { params: toParams(filters) })
  return response.data.message
}

export interface BudgetAtRiskRow {
  project: string
  project_name: string
  customer: string | null
  customer_name: string
  // Project amount selected in ChronoTally Settings ("Budget at Risk Amount")
  amount: number
  budget: number
  // amount / budget * 100
  used_pct: number
}

export interface BudgetAtRisk {
  // Label of the selected Project amount, e.g. "Total Costing Amount"
  amount_label: string
  rows: BudgetAtRiskRow[]
}

// Budgets are project-lifetime figures, so only the customer and project filters apply
export const getBudgetAtRisk = async (
  filters: Pick<ReportFilters, 'customer' | 'project'>
): Promise<BudgetAtRisk> => {
  const response = await api.get(`${REPORTS_API}.get_budget_at_risk`, {
    params: { customer: filters.customer || undefined, project: filters.project || undefined }
  })
  return response.data.message
}
