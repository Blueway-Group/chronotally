<!--
Copyright (c) 2026 Blueway Consulting LLC.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Legend, Tooltip } from 'chart.js'
import { getReportSummary, getReportHoursChart, getUnbilledByCustomer, getBudgetAtRisk } from '@/utils/client/api/reports.api'
import ComboBox from '../ComboBox.vue'
import CreateInvoiceModal from '../CreateInvoiceModal.vue'

ChartJS.register(BarElement, CategoryScale, LinearScale, Legend, Tooltip)

// Categorical series colors, assigned in fixed order; "Other" stays neutral
const SERIES_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']
const OTHER_COLOR = '#898781'

// Customers listed individually in the unbilled table; the rest collapse into "Others"
const UNBILLED_VISIBLE_ROWS = 5

// Share of the project budget used by the selected project amount at which a project is flagged
const BUDGET_WARNING_PCT = 90

const DATE_PRESETS = [
  { value: 'last-4-weeks', label: 'Last 4 weeks' },
  { value: 'last-8-weeks', label: 'Last 8 weeks' },
  { value: 'last-12-weeks', label: 'Last 12 weeks' },
  { value: 'this-month', label: 'This month' },
  { value: 'last-month', label: 'Last month' },
  { value: 'this-quarter', label: 'This quarter' },
  { value: 'year-to-date', label: 'Year to date' },
  { value: 'custom', label: 'Custom range' }
]

const GROUP_BY_OPTIONS = [
  { value: 'project', label: 'Project' },
  { value: 'customer', label: 'Customer' },
  { value: 'employee', label: 'Employee' },
  { value: 'activity', label: 'Activity' },
  { value: 'billable', label: 'Billable' }
]

const MEASURE_OPTIONS = [
  { value: 'hours', label: 'Hours' },
  { value: 'amount', label: 'Amount' },
  { value: 'cost', label: 'Cost' }
]

const PERIOD_OPTIONS = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' }
]

// Local YYYY-MM-DD (the report endpoints filter on calendar dates)
const toDateString = (date) => {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

const getPresetRange = (preset, today = new Date()) => {
  const end = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const start = new Date(end)

  switch (preset) {
    case 'last-4-weeks':
      start.setDate(end.getDate() - 4 * 7 + 1)
      break
    case 'last-12-weeks':
      start.setDate(end.getDate() - 12 * 7 + 1)
      break
    case 'this-month':
      start.setDate(1)
      break
    case 'last-month':
      start.setMonth(end.getMonth() - 1, 1)
      end.setDate(0)
      break
    case 'this-quarter':
      start.setMonth(Math.floor(end.getMonth() / 3) * 3, 1)
      break
    case 'year-to-date':
      start.setMonth(0, 1)
      break
    default: // last-8-weeks
      start.setDate(end.getDate() - 8 * 7 + 1)
  }

  return { start: toDateString(start), end: toDateString(end) }
}

// Global filters (apply to the whole page)
const datePreset = ref('last-8-weeks')
const customStart = ref('')
const customEnd = ref('')
const customer = ref('')
const project = ref('')
const employee = ref('')
const includeDrafts = ref(false)

// Chart options
const groupBy = ref('customer')
const measure = ref('amount')
const period = ref('weekly')

// Data
const summary = ref(null)
const chart = ref(null)
const unbilled = ref([])
const budgetRows = ref([])
const budgetAmountLabel = ref('')
const loadingSummary = ref(false)
const loadingChart = ref(false)
const loadingUnbilled = ref(false)
const loadingBudget = ref(false)

// Invoice modal
const showCreateInvoiceModal = ref(false)
const invoicePrefill = ref({})

// Toast state
const toast = ref({
  show: false,
  message: '',
  type: 'success'
})

const dateRange = computed(() => {
  if (datePreset.value === 'custom') {
    return { start: customStart.value, end: customEnd.value }
  }
  return getPresetRange(datePreset.value)
})

const filters = computed(() => ({
  start_date: dateRange.value.start,
  end_date: dateRange.value.end,
  customer: customer.value,
  project: project.value,
  employee: employee.value,
  include_drafts: includeDrafts.value
}))

const hasValidRange = computed(() =>
  Boolean(filters.value.start_date && filters.value.end_date && filters.value.start_date <= filters.value.end_date)
)

// Ignore responses from requests superseded by a newer filter change
let summaryRequestId = 0
let chartRequestId = 0
let unbilledRequestId = 0
let budgetRequestId = 0

const loadSummary = async () => {
  const requestId = ++summaryRequestId
  try {
    loadingSummary.value = true
    const response = await getReportSummary(filters.value)
    if (requestId === summaryRequestId) summary.value = response
  } catch (error) {
    console.error('Error loading report summary:', error)
    showToast(getErrorMessage(error, 'Failed to load report summary'), 'error')
  } finally {
    if (requestId === summaryRequestId) loadingSummary.value = false
  }
}

const loadChart = async () => {
  const requestId = ++chartRequestId
  try {
    loadingChart.value = true
    const response = await getReportHoursChart(filters.value, {
      group_by: groupBy.value,
      measure: measure.value,
      period: period.value
    })
    if (requestId === chartRequestId) chart.value = response
  } catch (error) {
    console.error('Error loading hours chart:', error)
    showToast(getErrorMessage(error, 'Failed to load hours chart'), 'error')
  } finally {
    if (requestId === chartRequestId) loadingChart.value = false
  }
}

const loadUnbilled = async () => {
  const requestId = ++unbilledRequestId
  try {
    loadingUnbilled.value = true
    const response = await getUnbilledByCustomer(filters.value)
    if (requestId === unbilledRequestId) unbilled.value = response
  } catch (error) {
    console.error('Error loading unbilled customers:', error)
    showToast(getErrorMessage(error, 'Failed to load unbilled customers'), 'error')
  } finally {
    if (requestId === unbilledRequestId) loadingUnbilled.value = false
  }
}

const loadBudget = async () => {
  const requestId = ++budgetRequestId
  try {
    loadingBudget.value = true
    const response = await getBudgetAtRisk({ customer: customer.value, project: project.value })
    if (requestId === budgetRequestId) {
      budgetRows.value = response.rows
      budgetAmountLabel.value = response.amount_label
    }
  } catch (error) {
    console.error('Error loading budget at risk:', error)
    showToast(getErrorMessage(error, 'Failed to load budget at risk'), 'error')
  } finally {
    if (requestId === budgetRequestId) loadingBudget.value = false
  }
}

const loadAll = () => {
  if (!hasValidRange.value) return
  loadSummary()
  loadChart()
  loadUnbilled()
}

onMounted(() => {
  loadAll()
  loadBudget()
})

watch(filters, loadAll, { deep: true })
// Budgets don't depend on dates, employee or status
watch([customer, project], loadBudget)
watch([groupBy, measure, period], () => {
  if (hasValidRange.value) loadChart()
})

const onDatePresetChange = () => {
  // Seed the custom inputs with the range that was showing
  if (datePreset.value === 'custom' && !customStart.value) {
    const range = getPresetRange('last-8-weeks')
    customStart.value = range.start
    customEnd.value = range.end
  }
}

// Formatting
const formatNumber = (value) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value || 0)

const formatHours = (hours) => `${formatNumber(hours)} h`

const formatCurrency = (amount) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount || 0)

const formatCompactCurrency = (amount) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(amount || 0)

const formatPercent = (value) => `${Math.round(value || 0)}%`

const formatBucket = (isoDate) => {
  const [year, month, day] = isoDate.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  return period.value === 'monthly'
    ? date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const formatMeasure = (value) => (measure.value === 'hours' ? formatHours(value) : formatCurrency(value))

// Frappe returns thrown messages JSON-encoded in _server_messages
const getErrorMessage = (error, fallback) => {
  try {
    const serverMessages = JSON.parse(error.response?.data?._server_messages || '[]')
    if (serverMessages.length) return JSON.parse(serverMessages[0]).message
  } catch {
    // Fall through to the generic message
  }
  return error.response?.data?.message || fallback
}

// KPI deltas vs. the prior period of the same length
const hoursDelta = computed(() => {
  if (!summary.value?.prior?.total_hours) return null
  return ((summary.value.total_hours - summary.value.prior.total_hours) / summary.value.prior.total_hours) * 100
})

const utilizationDelta = computed(() => {
  if (!summary.value?.prior?.total_hours) return null
  return summary.value.utilization - summary.value.prior.utilization
})

// Chart
// Colors follow the entity: a label keeps its color as filters change the series list
const seriesColorByLabel = new Map()
const getSeriesColor = (label) => {
  if (label === 'Other') return OTHER_COLOR
  if (!seriesColorByLabel.has(label)) {
    const used = new Set(seriesColorByLabel.values())
    const free = SERIES_COLORS.find((color) => !used.has(color))
    seriesColorByLabel.set(label, free || SERIES_COLORS[seriesColorByLabel.size % SERIES_COLORS.length])
  }
  return seriesColorByLabel.get(label)
}

watch(groupBy, () => seriesColorByLabel.clear())

const chartData = computed(() => ({
  labels: (chart.value?.buckets || []).map(formatBucket),
  datasets: (chart.value?.series || []).map((series) => ({
    label: series.label,
    data: series.values,
    backgroundColor: getSeriesColor(series.label),
    borderColor: '#ffffff',
    borderWidth: { top: 2 },
    borderSkipped: 'bottom',
    borderRadius: 4,
    maxBarThickness: 48
  }))
}))

const chartHasData = computed(() => chart.value?.series?.some((series) => series.values.some((v) => v)))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  scales: {
    x: {
      stacked: true,
      grid: { display: false },
      ticks: { color: '#898781' }
    },
    y: {
      stacked: true,
      beginAtZero: true,
      border: { display: false },
      grid: { color: '#e1e0d9' },
      ticks: {
        color: '#898781',
        maxTicksLimit: 5,
        callback: (value) => (measure.value === 'hours' ? `${value} h` : formatCompactCurrency(value))
      }
    }
  },
  plugins: {
    legend: {
      position: 'top',
      align: 'start',
      labels: { usePointStyle: true, pointStyle: 'rectRounded', boxWidth: 10, boxHeight: 10, color: '#52514e' }
    },
    tooltip: {
      callbacks: {
        label: (context) => `${context.dataset.label}: ${formatMeasure(context.parsed.y)}`,
        footer: (items) => `Total: ${formatMeasure(items.reduce((sum, item) => sum + item.parsed.y, 0))}`
      }
    }
  }
}))

const getBudgetProgressClass = (pct) => {
  if (pct > 100) return 'progress-error'
  if (pct >= BUDGET_WARNING_PCT) return 'progress-warning'
  return 'progress-primary'
}

// Unbilled by customer
const unbilledRows = computed(() => {
  const rows = unbilled.value
  if (rows.length <= UNBILLED_VISIBLE_ROWS) return rows

  const visible = rows.slice(0, UNBILLED_VISIBLE_ROWS - 1)
  const others = rows.slice(UNBILLED_VISIBLE_ROWS - 1)
  return [
    ...visible,
    {
      customer: null,
      customer_name: `Others (${others.length})`,
      hours: others.reduce((sum, row) => sum + row.hours, 0),
      amount: others.reduce((sum, row) => sum + row.amount, 0),
      isOthers: true
    }
  ]
})

const openCreateInvoiceModal = (row) => {
  invoicePrefill.value = {
    customer: row.customer,
    start_date: filters.value.start_date,
    end_date: filters.value.end_date,
    project: filters.value.project,
    employee: filters.value.employee
  }
  showCreateInvoiceModal.value = true
}

const closeCreateInvoiceModal = () => {
  showCreateInvoiceModal.value = false
}

const handleInvoiceCreated = (response) => {
  showToast(response.message, 'success')
  loadSummary()
  loadUnbilled()
}

const showToast = (message, type = 'success') => {
  toast.value = {
    show: true,
    message,
    type
  }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}
</script>

<template>
  <div class="container mx-auto p-6">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold">Reports</h1>
      <p class="text-base-content/70 mt-1">Hours, billing and margin across customers, projects and employees</p>
    </div>

    <!-- Global Filters -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body py-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
          <!-- Date Range -->
          <div>
            <label class="label" for="report-date-range">
              <span class="label-text">Date range</span>
            </label>
            <select
              id="report-date-range"
              v-model="datePreset"
              class="select select-bordered w-full"
              @change="onDatePresetChange"
            >
              <option v-for="preset in DATE_PRESETS" :key="preset.value" :value="preset.value">
                {{ preset.label }}
              </option>
            </select>
          </div>

          <!-- Customer -->
          <div>
            <label class="label" for="customer">
              <span class="label-text">Customer</span>
            </label>
            <div class="flex gap-1">
              <div class="flex-1">
                <ComboBox
                  name="customer"
                  docType="Customer"
                  v-model="customer"
                  :displayFields="['customer_name', 'name']"
                  placeholder="All customers"
                  :minSearchLength="0"
                />
              </div>
              <button v-if="customer" class="btn btn-ghost btn-square" title="Clear customer" @click="customer = ''">
                <span class="material-symbols-rounded text-xl">close</span>
              </button>
            </div>
          </div>

          <!-- Project -->
          <div>
            <label class="label" for="project">
              <span class="label-text">Project</span>
            </label>
            <div class="flex gap-1">
              <div class="flex-1">
                <ComboBox
                  name="project"
                  docType="Project"
                  v-model="project"
                  :displayFields="['project_name', 'name']"
                  placeholder="All projects"
                  :minSearchLength="0"
                />
              </div>
              <button v-if="project" class="btn btn-ghost btn-square" title="Clear project" @click="project = ''">
                <span class="material-symbols-rounded text-xl">close</span>
              </button>
            </div>
          </div>

          <!-- Employee -->
          <div>
            <label class="label" for="employee">
              <span class="label-text">Employee</span>
            </label>
            <div class="flex gap-1">
              <div class="flex-1">
                <ComboBox
                  name="employee"
                  docType="Employee"
                  v-model="employee"
                  :displayFields="['employee_name', 'name']"
                  placeholder="All employees"
                  :minSearchLength="0"
                />
              </div>
              <button v-if="employee" class="btn btn-ghost btn-square" title="Clear employee" @click="employee = ''">
                <span class="material-symbols-rounded text-xl">close</span>
              </button>
            </div>
          </div>

          <!-- Status -->
          <div>
            <label class="label" for="report-status">
              <span class="label-text">Status</span>
            </label>
            <select id="report-status" v-model="includeDrafts" class="select select-bordered w-full">
              <option :value="false">Submitted</option>
              <option :value="true">Draft</option>
              <option :value="true">Billed</option>
              <option :value="true">Cancelled</option>
            </select>
          </div>
        </div>

        <!-- Custom Range -->
        <div v-if="datePreset === 'custom'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-2">
          <div>
            <label class="label" for="report-start-date">
              <span class="label-text">From</span>
            </label>
            <input id="report-start-date" v-model="customStart" type="date" class="input input-bordered w-full" />
          </div>
          <div>
            <label class="label" for="report-end-date">
              <span class="label-text">To</span>
            </label>
            <input id="report-end-date" v-model="customEnd" type="date" class="input input-bordered w-full" />
          </div>
          <p v-if="!hasValidRange" class="text-sm text-error self-end pb-3 lg:col-span-3">
            Choose a start date on or before the end date
          </p>
        </div>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="stats stats-vertical lg:stats-horizontal shadow-xl w-full mb-6 bg-base-100">
      <div class="stat">
        <div class="stat-title">Total hours</div>
        <div class="stat-value">
          <span v-if="loadingSummary && !summary" class="loading loading-spinner"></span>
          <template v-else>{{ formatHours(summary?.total_hours) }}</template>
        </div>
        <div class="stat-desc">
          <template v-if="hoursDelta !== null">
            <span :class="hoursDelta >= 0 ? 'text-success' : 'text-error'">
              {{ hoursDelta >= 0 ? '▲' : '▼' }} {{ Math.abs(Math.round(hoursDelta)) }}%
            </span>
            vs. prior period
          </template>
          <template v-else>No prior period data</template>
        </div>
      </div>

      <div class="stat">
        <div class="stat-title">Billable utilization</div>
        <div class="stat-value">
          <span v-if="loadingSummary && !summary" class="loading loading-spinner"></span>
          <template v-else>{{ formatPercent(summary?.utilization) }}</template>
        </div>
        <div class="stat-desc">
          <template v-if="utilizationDelta !== null">
            <span :class="utilizationDelta >= 0 ? 'text-success' : 'text-error'">
              {{ utilizationDelta >= 0 ? '▲' : '▼' }} {{ Math.abs(Math.round(utilizationDelta)) }} pts
            </span>
            ·
          </template>
          {{ formatNumber(summary?.billable_hours) }} of {{ formatHours(summary?.total_hours) }} billable
        </div>
      </div>

      <div class="stat">
        <div class="stat-title">Unbilled (ready to invoice)</div>
        <div class="stat-value">
          <span v-if="loadingSummary && !summary" class="loading loading-spinner"></span>
          <template v-else>{{ formatCurrency(summary?.unbilled_amount) }}</template>
        </div>
        <div class="stat-desc">
          {{ formatHours(summary?.unbilled_hours) }} across {{ summary?.unbilled_customers || 0 }}
          {{ summary?.unbilled_customers === 1 ? 'customer' : 'customers' }}
        </div>
      </div>

      <div class="stat">
        <div class="stat-title">Margin</div>
        <div class="stat-value">
          <span v-if="loadingSummary && !summary" class="loading loading-spinner"></span>
          <template v-else>{{ formatPercent(summary?.margin) }}</template>
        </div>
        <div class="stat-desc">
          {{ formatCompactCurrency(summary?.revenue) }} revenue · {{ formatCompactCurrency(summary?.cost) }} cost
        </div>
      </div>
    </div>

    <!-- Hours Chart -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
          <h2 class="card-title">Hours</h2>
          <div class="flex flex-wrap items-center gap-4">
            <div class="flex items-center gap-2">
              <span class="text-sm text-base-content/70">Group by</span>
              <div class="join">
                <button
                  v-for="option in GROUP_BY_OPTIONS"
                  :key="option.value"
                  class="join-item btn btn-sm"
                  :class="{ 'btn-active': groupBy === option.value }"
                  @click="groupBy = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-base-content/70">Measure</span>
              <div class="join">
                <button
                  v-for="option in MEASURE_OPTIONS"
                  :key="option.value"
                  class="join-item btn btn-sm"
                  :class="{ 'btn-active': measure === option.value }"
                  @click="measure = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-base-content/70">Period</span>
              <div class="join">
                <button
                  v-for="option in PERIOD_OPTIONS"
                  :key="option.value"
                  class="join-item btn btn-sm"
                  :class="{ 'btn-active': period === option.value }"
                  @click="period = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="relative h-80">
          <div v-if="loadingChart && !chart" class="flex justify-center items-center h-full">
            <span class="loading loading-spinner loading-lg"></span>
          </div>
          <div v-else-if="!chartHasData" class="flex flex-col justify-center items-center h-full">
            <span class="material-symbols-rounded text-6xl text-base-content/30">bar_chart</span>
            <p class="text-base-content/70 mt-4">No time logged for the selected filters</p>
          </div>
          <Bar v-else :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- Budget at Risk -->
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h2 class="card-title">
            Budget at risk
            <span class="text-sm font-normal text-base-content/60">(amber ≥ {{ BUDGET_WARNING_PCT }}%)</span>
          </h2>

          <div v-if="loadingBudget && budgetRows.length === 0" class="flex justify-center py-12">
            <span class="loading loading-spinner loading-lg"></span>
          </div>

          <div v-else-if="budgetRows.length === 0" class="text-center py-12">
            <span class="material-symbols-rounded text-6xl text-base-content/30">savings</span>
            <p class="text-base-content/70 mt-4">No project budgets</p>
            <p class="text-sm text-base-content/50 mt-2">Submit a Budget against an open Project to track it here</p>
          </div>

          <ul v-else class="space-y-4">
            <li v-for="row in budgetRows" :key="row.project">
              <div class="flex justify-between gap-4 text-sm mb-1">
                <span class="font-medium truncate" :title="row.project">
                  {{ row.project_name }} · {{ row.customer_name }}
                </span>
                <span
                  class="whitespace-nowrap"
                  :title="`${budgetAmountLabel} / Budget`"
                  :class="{
                    'text-error font-semibold': row.used_pct > 100,
                    'text-warning font-semibold': row.used_pct >= BUDGET_WARNING_PCT && row.used_pct <= 100
                  }"
                >
                  {{ formatCurrency(row.amount) }} / {{ formatCurrency(row.budget) }}
                  ({{ formatPercent(row.used_pct) }})
                </span>
              </div>
              <progress
                class="progress w-full"
                :class="getBudgetProgressClass(row.used_pct)"
                :value="Math.min(row.used_pct, 100)"
                max="100"
              ></progress>
            </li>
          </ul>
        </div>
      </div>

      <!-- Unbilled by Customer -->
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h2 class="card-title">Unbilled by customer</h2>

          <div v-if="loadingUnbilled && unbilled.length === 0" class="flex justify-center py-12">
            <span class="loading loading-spinner loading-lg"></span>
          </div>

          <div v-else-if="unbilled.length === 0" class="text-center py-12">
            <span class="material-symbols-rounded text-6xl text-base-content/30">task_alt</span>
            <p class="text-base-content/70 mt-4">Nothing waiting to be invoiced</p>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="table table-zebra">
              <thead>
                <tr>
                  <th>Customer</th>
                  <th class="text-right">Hours</th>
                  <th class="text-right">Amount</th>
                  <th class="text-right"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in unbilledRows" :key="row.customer || row.customer_name">
                  <td>{{ row.customer_name }}</td>
                  <td class="text-right tabular-nums">{{ formatNumber(row.hours) }}</td>
                  <td class="text-right tabular-nums font-semibold">{{ formatCurrency(row.amount) }}</td>
                  <td class="text-right">
                    <button
                      v-if="!row.isOthers && row.customer"
                      class="btn btn-sm btn-primary btn-outline"
                      @click="openCreateInvoiceModal(row)"
                    >
                      Invoice
                    </button>
                    <span v-else class="text-base-content/40">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Invoice Modal -->
    <CreateInvoiceModal
      :show="showCreateInvoiceModal"
      :prefill="invoicePrefill"
      @close="closeCreateInvoiceModal"
      @created="handleInvoiceCreated"
      @error="(message) => showToast(message, 'error')"
    />

    <!-- Toast Notification -->
    <div v-if="toast.show" class="toast toast-top toast-end">
      <div :class="['alert', toast.type === 'success' ? 'alert-success' : 'alert-error']">
        <span>{{ toast.message }}</span>
      </div>
    </div>
  </div>
</template>
