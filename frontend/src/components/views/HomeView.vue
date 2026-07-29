<!--
Copyright (c) 2026 Blueway Consulting LLC.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { createTimesheet, getTimesheets, deleteTimesheet, getTimesheetStats, getTimesheetList } from '../../utils/client/api'
import { getWeekDates, getMonthRangeDates, getDayRangeDates, getMonthBoundaryDates } from '../../utils/client/dates'
import { validateTimeLogs } from '../../utils/client/timeValidation'
import NewTimesheetModal from '../NewTimesheetModal.vue'

// Reactive state
const loading = ref(true)
const timesheets = ref([])
const showNewTimesheetModal = ref(false)
const dashboardStats = ref({
  today: { hours: 0, target: 8 },
  thisWeek: { hours: 0, target: 40 },
  thisMonth: { hours: 0, target: 160 },
  financialYear: { hours: 0, target: 2080 }
})

// Chart data for last 30 days
const chartData = ref([])
const chartLabels = ref([])

// Current date calculations
const currentDate = new Date()
const { start: weekStart, end: weekEnd } = getWeekDates(currentDate)
const { start: monthStart, end: monthEnd } = getMonthRangeDates(currentDate)

// Computed properties
const todayProgress = computed(() => {
  const percentage = Math.min((dashboardStats.value.today.hours / dashboardStats.value.today.target) * 100, 100)
  return Math.round(percentage)
})

const weekProgress = computed(() => {
  const percentage = Math.min((dashboardStats.value.thisWeek.hours / dashboardStats.value.thisWeek.target) * 100, 100)
  return Math.round(percentage)
})

const monthProgress = computed(() => {
  const percentage = Math.min((dashboardStats.value.thisMonth.hours / dashboardStats.value.thisMonth.target) * 100, 100)
  return Math.round(percentage)
})

const yearProgress = computed(() => {
  const percentage = Math.min((dashboardStats.value.financialYear.hours / dashboardStats.value.financialYear.target) * 100, 100)
  return Math.round(percentage)
})

// Utility functions
const formatDate = (date) => {
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const formatDateAsBackend = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
}

const getCurrentMonth = () => {
  return currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}

const getFinancialYear = () => {
  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()
  // Assuming financial year starts in April (month 3)
  if (month >= 3) {
    return `${year}-${year + 1}`
  } else {
    return `${year - 1}-${year}`
  }
}

// Fetch timesheet hours for the last 30 days
const getTimesheetsHours = async () => {
  try {
    const timesheetsData = await getTimesheetList({
      startDate: monthStart,
      endDate: monthEnd
    })

    timesheets.value = timesheetsData.timesheets

    const timesheetMap = timesheets.value.reduce((map, item) => {
      item.time_logs.forEach(log => {
        map[log.from_time] = (map[log.from_time] || 0) + log.hours
      })
      return map
    }, {})

    return JSON.stringify(timesheetMap)

  } catch (error) {
    console.error('Error fetching timesheets:', error)
  }
}

// Generate sample chart data for last 30 days
const generateChartData = async () => {
  const hours = []
  const labels = []

  const data = await getTimesheetsHours()
  const timesheetMap = JSON.parse(data)

  const newMap = {}
  for (const [key, value] of Object.entries(timesheetMap)) {
    const newDate = key.match(/^(\d{4}-\d{2}-\d{2})/)
    if (newDate) {
      newMap[newDate[1]] = value
    }
  }

  for (let i = 29; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    const formattedDate = formatDateAsBackend(date)

    if (formattedDate in newMap) {
      hours.push(newMap[formattedDate])
    } else {
      hours.push(0)
    }

    labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))
  }

  chartData.value = hours
  chartLabels.value = labels
}

// Calculate dashboard statistics
const calculateStats = async () => {
  try {
    const todayStats = await getTimesheetStats(weekStart, weekEnd)
    const weekDay = currentDate.getUTCDay()
    dashboardStats.value.today.hours = todayStats.time_logs[weekDay - 1]?.hours || 0

    // This week's stats
    const weekStats = await getTimesheetStats(weekStart, weekEnd)
    dashboardStats.value.thisWeek.hours = weekStats?.total_hours || 0

    // This month's stats (full month boundaries in UTC-aware ISO)
    const { start: monthStartIso, end: monthEndIso } = getMonthBoundaryDates(currentDate)
    const monthStats = await getTimesheetStats(monthStartIso, monthEndIso)
    dashboardStats.value.thisMonth.hours = monthStats?.total_hours || 0
    // Financial year stats (simplified - last 12 months) using day-range helpers
    const yearStartLocal = new Date(currentDate)
    yearStartLocal.setFullYear(currentDate.getFullYear() - 1)
    const { start: yearStartIso } = getDayRangeDates(yearStartLocal)
    const { end: yearEndIso } = getDayRangeDates(currentDate)
    const yearStats = await getTimesheetStats(yearStartIso, yearEndIso)
    dashboardStats.value.financialYear.hours = yearStats?.total_hours || 0

  } catch (error) {
    console.error('Error calculating dashboard stats:', error)
    // Use mock data if API fails
    dashboardStats.value = {
      today: { hours: 6.5, target: 8 },
      thisWeek: { hours: 32.5, target: 40 },
      thisMonth: { hours: 145.2, target: 160 },
      financialYear: { hours: 1856.7, target: 2080 }
    }
  }
}

// Initialize dashboard
const initializeDashboard = async () => {
  loading.value = true
  try {
    await Promise.all([
      calculateStats(),
      generateChartData()
    ])
  } catch (error) {
    console.error('Error initializing dashboard:', error)
  } finally {
    loading.value = false
  }
}

// Modal handlers
const openNewTimesheetModal = () => {
  showNewTimesheetModal.value = true
}

const closeNewTimesheetModal = () => {
  showNewTimesheetModal.value = false
}

const handleTimesheetCreated = async () => {
  // Refresh dashboard stats after creating a new timesheet
  await initializeDashboard()
}

// Lifecycle
onMounted(() => {
  initializeDashboard()
})
</script>

<template>
  <div class="min-h-full bg-base-100">
    <!-- Dashboard Header -->
    <div class="mb-8">
      <div class="hero bg-gradient-to-r from-primary/10 to-secondary/10 rounded-lg">
        <div class="hero-content text-center py-8">
          <div class="max-w-md">
            <h1 class="text-4xl font-bold text-base-content mb-2">Welcome Back!</h1>
            <p class="text-lg text-base-content/70">{{ formatDate(currentDate) }}</p>
            <p class="text-sm text-base-content/60 mt-2">Track your time and stay productive</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-20">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="space-y-8">
      <!-- Statistics Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <!-- Today Card -->
        <div class="stats bg-base-200 shadow-lg hover:shadow-xl transition-shadow duration-200">
          <div class="stat">
            <div class="stat-figure text-primary">
              <span class="material-symbols-rounded text-primary" style="font-size: 2rem;">
                schedule
              </span>
            </div>
            <div class="stat-title text-base-content/70">Today</div>
            <div class="stat-value text-primary">{{ dashboardStats.today.hours.toFixed(1) }}h</div>
            <div class="stat-desc text-base-content/60">
              <div class="flex items-center gap-2">
                <progress
                  class="progress progress-primary w-16"
                  :value="todayProgress"
                  max="100"
                ></progress>
                <span>{{ todayProgress }}%</span>
              </div>
              <div class="mt-1">Goal: {{ dashboardStats.today.target }}h</div>
            </div>
          </div>
        </div>

        <!-- This Week Card -->
        <div class="stats bg-base-200 shadow-lg hover:shadow-xl transition-shadow duration-200">
          <div class="stat">
            <div class="stat-figure text-secondary">
              <span class="material-symbols-rounded text-secondary" style="font-size: 2rem;">
                calendar_month
              </span>
            </div>
            <div class="stat-title text-base-content/70">This Week</div>
            <div class="stat-value text-secondary">{{ dashboardStats.thisWeek.hours.toFixed(1) }}h</div>
            <div class="stat-desc text-base-content/60">
              <div class="flex items-center gap-2">
                <progress
                  class="progress progress-secondary w-16"
                  :value="weekProgress"
                  max="100"
                ></progress>
                <span>{{ weekProgress }}%</span>
              </div>
              <div class="mt-1">Goal: {{ dashboardStats.thisWeek.target }}h</div>
            </div>
          </div>
        </div>

        <!-- This Month Card -->
        <div class="stats bg-base-200 shadow-lg hover:shadow-xl transition-shadow duration-200">
          <div class="stat">
            <div class="stat-figure text-accent">
              <span class="material-symbols-rounded text-accent" style="font-size: 2rem;">
                bar_chart
              </span>
            </div>
            <div class="stat-title text-base-content/70">{{ getCurrentMonth() }}</div>
            <div class="stat-value text-accent">{{ dashboardStats.thisMonth.hours.toFixed(1) }}h</div>
            <div class="stat-desc text-base-content/60">
              <div class="flex items-center gap-2">
                <progress
                  class="progress progress-accent w-16"
                  :value="monthProgress"
                  max="100"
                ></progress>
                <span>{{ monthProgress }}%</span>
              </div>
              <div class="mt-1">Goal: {{ dashboardStats.thisMonth.target }}h</div>
            </div>
          </div>
        </div>

        <!-- Financial Year Card -->
        <div class="stats bg-base-200 shadow-lg hover:shadow-xl transition-shadow duration-200">
          <div class="stat">
            <div class="stat-figure text-success">
              <span class="material-symbols-rounded text-success" style="font-size: 2rem;">
                payments
              </span>
            </div>
            <div class="stat-title text-base-content/70">FY {{ getFinancialYear() }}</div>
            <div class="stat-value text-success">{{ dashboardStats.financialYear.hours.toFixed(0) }}h</div>
            <div class="stat-desc text-base-content/60">
              <div class="flex items-center gap-2">
                <progress
                  class="progress progress-success w-16"
                  :value="yearProgress"
                  max="100"
                ></progress>
                <span>{{ yearProgress }}%</span>
              </div>
              <div class="mt-1">Goal: {{ dashboardStats.financialYear.target }}h</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Working Hours Chart -->
      <div class="card bg-base-100 shadow-lg">
        <div class="card-body">
          <h2 class="card-title text-xl mb-4 flex items-center gap-2">
            <span class="material-symbols-rounded text-2xl">
              bar_chart
            </span>
            My Working Hours (Last 30 Days)
          </h2>

          <!-- Simple Chart Visualization -->
          <div class="h-64 bg-base-200 rounded-lg flex items-end justify-between p-4 gap-1">
            <div
              v-for="(hours, index) in chartData"
              :key="index"
              class="bg-primary rounded-t flex-1 transition-all duration-200 hover:bg-primary-focus tooltip tooltip-top"
              :data-tip="`${chartLabels[index]}: ${hours.toFixed(1)}h`"
              :style="{ height: `${Math.max((hours / 12) * 40, 5)}%` }"
            ></div>
          </div>

          <!-- Chart Labels -->
          <div class="flex justify-between text-xs text-base-content/60 mt-2">
            <span>{{ chartLabels[0] }}</span>
            <span>{{ chartLabels[Math.floor(chartLabels.length / 2)] }}</span>
            <span>{{ chartLabels[chartLabels.length - 1] }}</span>
          </div>

          <!-- Chart Legend -->
          <div class="mt-4 flex justify-center">
            <div class="stats stats-horizontal bg-base-200">
              <div class="stat">
                <div class="stat-title text-sm">Average Daily</div>
                <div class="stat-value text-lg">{{ (chartData.reduce((a, b) => a + b, 0) / chartData.length).toFixed(1) }}h</div>
              </div>
              <div class="stat">
                <div class="stat-title text-sm">Highest Day</div>
                <div class="stat-value text-lg">{{ Math.max(...chartData).toFixed(1) }}h</div>
              </div>
              <div class="stat">
                <div class="stat-title text-sm">Total Hours</div>
                <div class="stat-value text-lg">{{ chartData.reduce((a, b) => a + b, 0).toFixed(0) }}h</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="card bg-base-100 shadow-lg">
        <div class="card-body">
          <h2 class="card-title text-xl mb-4">Quick Actions</h2>
          <div class="flex flex-wrap gap-4">
            <button class="btn btn-primary" @click="openNewTimesheetModal">
              <span class="material-symbols-rounded text-xl">
                add
              </span>
              New Timesheet
            </button>
            <button class="btn btn-secondary">
              <span class="material-symbols-rounded text-xl">
                assessment
              </span>
              View Reports
            </button>
            <button class="btn btn-accent">
              <span class="material-symbols-rounded text-xl">
                timer
              </span>
              Start Timer
            </button>
            <button class="btn btn-outline">
              <span class="material-symbols-rounded text-xl">
                download
              </span>
              Export Data
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- New Timesheet Modal -->
    <NewTimesheetModal
      :show="showNewTimesheetModal"
      @close="closeNewTimesheetModal"
      @created="handleTimesheetCreated"
    />
  </div>
</template>