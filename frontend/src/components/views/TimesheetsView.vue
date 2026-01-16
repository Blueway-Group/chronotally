<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getTimesheetStats, getTimesheetStatusStats, getTimesheetList, updateRecord, deleteTimesheet, cancelTimesheet, getCurrentUserEmployee } from '@/utils/client/api'
import { getWeekDates } from '@/utils/client/dates'
import TimesheetCalendar from '../TimesheetCalendar.vue'
import TimesheetsList from '../TimesheetsList.vue'
import NewTimesheetModal from '../NewTimesheetModal.vue'
import ViewTimesheetModal from '../ViewTimesheetModal.vue'
import FiltersModal from '../FiltersModal.vue'
import Toast from '../Toast.vue'

// Reactive state
const loading = ref(false)
const deletingTimesheet = ref(null) // Track which timesheet is being deleted
const timesheets = ref([])
const selectedTimesheet = ref(null)
const showNewTimesheetModal = ref(false)
const showViewDetailsModal = ref(false)
const showFiltersModal = ref(false)
const viewMode = ref('list') // 'list' or 'calendar'
const selectedDate = ref('') // Store the selected date from calendar click

// Toast notification state
const toast = ref({
  show: false,
  message: '',
  type: 'success' // 'success' or 'error'
})

// Date filters
const dateFilter = ref('this-week')
const customStartDate = ref('')
const customEndDate = ref(new Date().toISOString().split('T')[0]) // Default to current date
const statusFilter = ref('') // Keep for backward compatibility
const selectedStatuses = ref([])
const employeeFilter = ref('') // Selected employee filter
const projectFilter = ref('') // Selected project filter
const currentUserEmployee = ref('') // Current user's employee ID

// Pagination state
const currentPage = ref(1)
const itemsPerPage = ref(5)
const totalTimesheets = ref(0)

// URL params helper functions
const updateUrlParams = () => {
  const params = new URLSearchParams()

  // Add date filter
  if (dateFilter.value !== 'this-week') {
    params.set('period', dateFilter.value)
  }

  // Add custom dates if using custom range
  if (dateFilter.value === 'custom') {
    if (customStartDate.value) params.set('start', customStartDate.value)
    if (customEndDate.value) params.set('end', customEndDate.value)
  }

  // Add statuses
  if (selectedStatuses.value.length > 0) {
    params.set('status', selectedStatuses.value.join(','))
  }

  // Add employee filter (only if different from current user)
  if (employeeFilter.value && employeeFilter.value !== currentUserEmployee.value) {
    params.set('employee', employeeFilter.value)
  }

  // Add project filter
  if (projectFilter.value) {
    params.set('project', projectFilter.value)
  }

  // Add view mode if calendar
  if (viewMode.value === 'calendar') {
    params.set('view', 'calendar')
  }

  // Update URL without reloading the page
  const newUrl = params.toString() ? `?${params.toString()}` : window.location.pathname
  window.history.replaceState({}, '', newUrl + window.location.hash)
}

const loadFiltersFromUrl = () => {
  const params = new URLSearchParams(window.location.search)

  // Load date filter
  const period = params.get('period')
  if (period && ['this-week', 'last-week', 'this-month', 'last-month', 'custom'].includes(period)) {
    dateFilter.value = period
  }

  // Load custom dates
  if (period === 'custom') {
    const start = params.get('start')
    const end = params.get('end')
    if (start) customStartDate.value = start
    if (end) customEndDate.value = end
  }

  // Load statuses
  const statuses = params.get('status')
  if (statuses) {
    selectedStatuses.value = statuses.split(',').filter(s =>
      ['Draft', 'Submitted', 'Billed', 'Cancelled'].includes(s)
    )
  }

  // Load employee filter
  const employee = params.get('employee')
  if (employee) {
    employeeFilter.value = employee
  }

  // Load project filter
  const project = params.get('project')
  if (project) {
    projectFilter.value = project
  }

  // Load view mode
  const view = params.get('view')
  if (view === 'calendar') {
    viewMode.value = 'calendar'
  }
}

// Calendar-specific date range (separate from filter dropdown)
const calendarDateRange = ref({
  start: '',
  end: '',
  view: 'dayGridMonth'
})

// Stats data
const weeklyStats = ref({ total_hours: 0 })
const statusStats = ref({
  draft: 0,
  submitted: 0,
  billed: 0,
  cancelled: 0
})

// Last refresh timestamp
const lastRefreshed = ref(null)

// Computed properties
const filteredTimesheets = computed(() => {
  let filtered = timesheets.value
  return filtered
})

const totalHoursThisWeek = computed(() => {
  return weeklyStats.value.total_hours || 0
})

// Helper function to get date range based on filter
const getDateRange = () => {
  // If we're in calendar view and have a calendar date range, use that
  if (viewMode.value === 'calendar' && calendarDateRange.value.start && calendarDateRange.value.end) {
    return {
      start: calendarDateRange.value.start,
      end: calendarDateRange.value.end
    }
  }

  const now = new Date()
  let startDate, endDate

  switch (dateFilter.value) {
    case 'this-week':
      const { start, end } = getWeekDates()
      return { start, end }

    case 'last-week':
      const lastWeekEnd = new Date(now)
      lastWeekEnd.setDate(now.getDate() - now.getDay())
      const lastWeekStart = new Date(lastWeekEnd)
      lastWeekStart.setDate(lastWeekEnd.getDate() - 6)
      return {
        start: lastWeekStart.toISOString().split('T')[0],
        end: lastWeekEnd.toISOString().split('T')[0]
      }

    case 'this-month':
      startDate = new Date(now.getFullYear(), now.getMonth(), 1)
      endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0)
      return {
        start: startDate.toISOString().split('T')[0],
        end: endDate.toISOString().split('T')[0]
      }

    case 'last-month':
      startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      endDate = new Date(now.getFullYear(), now.getMonth(), 0)
      return {
        start: startDate.toISOString().split('T')[0],
        end: endDate.toISOString().split('T')[0]
      }

    case 'custom':
      return {
        start: customStartDate.value,
        end: customEndDate.value
      }

    default:
      const { start: defaultStart, end: defaultEnd } = getWeekDates()
      return { start: defaultStart, end: defaultEnd }
  }
}

// Load timesheet data
const loadTimesheets = async () => {
  try {
    loading.value = true
    const { start, end } = getDateRange()

    if (start && end) {
      // Determine status filter - support multiple statuses
      let statusParam = "all"
      if (selectedStatuses.value.length > 0) {
        statusParam = selectedStatuses.value.join(',')
      } else if (statusFilter.value && statusFilter.value !== "") {
        // Backward compatibility
        statusParam = statusFilter.value
      }

      // Calculate API start parameter for pagination
      const apiStart = (currentPage.value - 1) * itemsPerPage.value

      // Load timesheet list using new params object format
      const listResponse = await getTimesheetList({
        startDate: start,
        endDate: end,
        statusFilter: statusParam,
        limit: itemsPerPage.value,
        start: apiStart,
        employee: employeeFilter.value,
        project: projectFilter.value
      })
      timesheets.value = listResponse.timesheets || []
      totalTimesheets.value = listResponse.total_count || 0
      console.debug('Timesheet list loaded:', timesheets.value)
    }
  } catch (error) {
    console.error('Error loading timesheets:', error)
  } finally {
    loading.value = false
  }
}

// Load statistics
const loadStats = async () => {
  try {
    // Load status stats
    const statusResponse = await getTimesheetStatusStats()
    statusStats.value = statusResponse || statusStats.value

    // Load weekly hours
    const { start, end } = getWeekDates()
    const weeklyResponse = await getTimesheetStats(start, end)
    weeklyStats.value = weeklyResponse || weeklyStats.value

  } catch (error) {
    console.error('Error loading stats:', error)
  }
}

// Load current user's employee
const loadCurrentUserEmployee = async () => {
  try {
    const employee = await getCurrentUserEmployee()
    if (employee) {
      currentUserEmployee.value = employee.name
      // Set default employee filter to current user
      employeeFilter.value = employee.name
      console.log('Current user employee:', employee)
    } else {
      console.warn('No employee found for current user')
    }
  } catch (error) {
    console.error('Error loading current user employee:', error)
  }
}

// Watch for filter changes
const onFilterChange = async () => {
  currentPage.value = 1 // Reset to first page when filters change
  await loadTimesheets()
  updateUrlParams()
}

// Open filters modal
const openFiltersModal = () => {
  showFiltersModal.value = true
}

// Close filters modal
const closeFiltersModal = () => {
  showFiltersModal.value = false
}

// Apply filters from modal
const applyFilters = (filters) => {
  dateFilter.value = filters.dateFilter
  customStartDate.value = filters.customStartDate
  customEndDate.value = filters.customEndDate
  selectedStatuses.value = filters.selectedStatuses
  employeeFilter.value = filters.employeeFilter
  projectFilter.value = filters.projectFilter

  showFiltersModal.value = false
  onFilterChange()
}

// Status filter functions
const toggleStatus = (status) => {
  const index = selectedStatuses.value.indexOf(status)
  if (index > -1) {
    selectedStatuses.value.splice(index, 1)
  } else {
    selectedStatuses.value.push(status)
  }
  onFilterChange()
}

const removeStatus = (status) => {
  const index = selectedStatuses.value.indexOf(status)
  if (index > -1) {
    selectedStatuses.value.splice(index, 1)
    onFilterChange()
  }
}

const clearAllStatuses = () => {
  selectedStatuses.value = []
  onFilterChange()
}

const isStatusSelected = (status) => {
  return selectedStatuses.value.includes(status)
}

const availableStatuses = ['Draft', 'Submitted', 'Billed', 'Cancelled']

// Computed property to check if any filters are active
const hasActiveFilters = computed(() => {
  return dateFilter.value !== 'this-week' ||
    selectedStatuses.value.length > 0 ||
    employeeFilter.value !== currentUserEmployee.value ||
    projectFilter.value !== ''
})

// Watch for view mode changes
const onViewModeChange = async (newMode) => {
  viewMode.value = newMode

  // Update URL hash based on view mode
  if (newMode === 'calendar') {
    window.location.hash = '#calendar'
  } else {
    // Remove hash for list view
    if (window.location.hash === '#calendar') {
      history.replaceState(null, null, window.location.pathname + window.location.search)
    }
  }

  // Update URL params
  updateUrlParams()

  // Clear calendar date range when switching to list view
  if (newMode === 'list') {
    calendarDateRange.value = {
      start: '',
      end: '',
      view: ''
    }
  }

  // Reload timesheets when switching views
  await loadTimesheets()
}

// Methods
const getStatusColor = (status) => {
  const colors = {
    'Draft': 'badge-ghost',
    'Submitted': 'badge-primary',
    'Billed': 'badge-success',
    'Cancelled': 'badge-error'
  }
  return colors[status] || 'badge-ghost'
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatDateTime = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTimeAgo = (date) => {
  if (!date) return ''
  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)

  if (diffInSeconds < 60) return 'Just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const openNewTimesheetModal = () => {
  showNewTimesheetModal.value = true
}

const closeNewTimesheetModal = () => {
  showNewTimesheetModal.value = false
  selectedDate.value = '' // Reset the selected date
}

const handleTimesheetCreated = async () => {
  await loadTimesheets()
  await loadStats()
}

const viewTimesheetModal = (timesheet) => {
  selectedTimesheet.value = timesheet
  showViewDetailsModal.value = true
}

const closeViewModal = () => {
  showViewDetailsModal.value = false
}

const handleTimesheetUpdated = async () => {
  await loadTimesheets()
  await loadStats()
}

const showToast = (messageOrEvent, type = 'success') => {
  // Handle both direct calls and event objects from child components
  if (typeof messageOrEvent === 'object' && messageOrEvent.message) {
    toast.value = { show: true, message: messageOrEvent.message, type: messageOrEvent.type || 'success' }
  } else {
    toast.value = { show: true, message: messageOrEvent, type }
  }
}

const deleteTimesheetItem = async (id) => {
  if (confirm('Are you sure you want to delete this timesheet?')) {
    try {
      deletingTimesheet.value = id
      await deleteTimesheet(id)
      await loadTimesheets() // Refresh the list
      await loadStats() // Refresh stats
      showToast('Timesheet deleted successfully', 'success')
    } catch (error) {
      console.error('Error deleting timesheet:', error)
      showToast('Failed to delete timesheet. Please try again.', 'error')
    } finally {
      deletingTimesheet.value = null
    }
  }
}

const cancelTimesheetItem = async (id) => {
  if (confirm('Are you sure you want to cancel this timesheet?')) {
    try {
      await cancelTimesheet(id)
      await loadTimesheets() // Refresh the list
      await loadStats() // Refresh stats
      showToast('Timesheet cancelled successfully', 'success')
    } catch (error) {
      console.error('Error cancelling timesheet:', error)
      showToast('Failed to cancel timesheet. Please try again.', 'error')
    }
  }
}

// Helper function to extract error message from error response
const getErrorMessage = (error) => {
  // Try to parse _server_messages first (Frappe's message format)
  if (error._server_messages) {
    try {
      const messages = JSON.parse(error._server_messages)
      if (Array.isArray(messages) && messages.length > 0) {
        const firstMessage = JSON.parse(messages[0])
        return firstMessage.message || firstMessage.title || 'An error occurred'
      }
    } catch (e) {
      // If parsing fails, continue to other methods
    }
  }

  // Try exception message
  if (error.exception) {
    // Extract the readable error message from exception
    const match = error.exception.match(/:\s*(.+?)(?:\n|$)/)
    if (match && match[1]) {
      return match[1]
    }
  }

  // Fallback to error message or default
  return error.message || error.exc_type || 'Failed to submit timesheet. Please try again.'
}

const submitTimesheet = async (id) => {
  try {
    await updateRecord('Timesheet', id, { status: 'Submitted', docstatus: 1 })
    await loadTimesheets() // Refresh the list
    await loadStats() // Refresh stats
    showToast('Timesheet submitted successfully', 'success')
  } catch (error) {
    console.error('Error submitting timesheet:', error)
    const errorMessage = getErrorMessage(error)
    showToast(errorMessage, 'error')
  }
}

const handleDateSelect = (selectInfo) => {
  // Format the start date to YYYY-MM-DD
  const clickedDate = selectInfo.startStr || selectInfo.start.toISOString().split('T')[0]
  selectedDate.value = clickedDate
  console.log('Date selected on calendar:', clickedDate)

  // Open the NewTimesheetModal with the selected date
  showNewTimesheetModal.value = true
}

const handleCalendarDateRangeChange = async (dateRangeInfo) => {
  // Update calendar date range
  calendarDateRange.value = {
    start: dateRangeInfo.startStr,
    end: dateRangeInfo.endStr,
    view: dateRangeInfo.view
  }

  // Only reload timesheets if we're in calendar view
  if (viewMode.value === 'calendar') {
    console.log('Calendar date range changed:', dateRangeInfo)
    await loadTimesheets()
  }
}

// Handle timesheet click from calendar
const viewTimesheet = (timesheet) => {
  console.log('Calendar timesheet clicked:', timesheet)
  viewTimesheetModal(timesheet)
}

// Refresh function to reload timesheets and stats
const refreshData = async () => {
  await Promise.all([loadTimesheets(), loadStats()])
  lastRefreshed.value = new Date()
}

// Pagination handlers
const handlePageChange = async (page) => {
  currentPage.value = page
  await loadTimesheets()
}

const handleItemsPerPageChange = async (perPage) => {
  itemsPerPage.value = perPage
  currentPage.value = 1 // Reset to first page when changing items per page
  await loadTimesheets()
}

// Keyboard shortcut handler for refresh (Ctrl+R or F5)
const handleKeydown = (event) => {
  // Prevent default browser refresh and use our custom refresh
  if ((event.ctrlKey && event.key === 'r') || event.key === 'F5') {
    event.preventDefault()
    refreshData()
  }
}

// Initialize view mode based on URL hash
const initializeViewMode = () => {
  const params = new URLSearchParams(window.location.search)
  const viewParam = params.get('view')

  // Check both URL param and hash for backward compatibility
  if (viewParam === 'calendar' || window.location.hash === '#calendar') {
    viewMode.value = 'calendar'
  } else {
    viewMode.value = 'list'
  }
}

// Handle browser back/forward navigation
const handleHashChange = () => {
  const newViewMode = window.location.hash === '#calendar' ? 'calendar' : 'list'
  if (newViewMode !== viewMode.value) {
    viewMode.value = newViewMode

    // Clear calendar date range when switching to list view
    if (newViewMode === 'list') {
      calendarDateRange.value = {
        start: '',
        end: '',
        view: ''
      }
    }

    // Reload timesheets when switching views
    loadTimesheets()
  }
}

// Lifecycle
onMounted(async () => {
  // Initialize view mode based on URL hash
  initializeViewMode()

  // Load filters from URL params
  loadFiltersFromUrl()

  // Load current user employee first, then load timesheets with that filter
  await loadCurrentUserEmployee()

  // If no employee filter in URL, set to current user
  if (!employeeFilter.value && currentUserEmployee.value) {
    employeeFilter.value = currentUserEmployee.value
  }

  await Promise.all([loadTimesheets(), loadStats()])
  lastRefreshed.value = new Date()

  // Update URL params to reflect current state
  updateUrlParams()

  // Add event listeners
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('hashchange', handleHashChange)
})

onUnmounted(() => {
  // Clean up event listeners
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('hashchange', handleHashChange)
})
</script>

<template>
  <div class="min-h-full bg-base-100">
    <!-- Page Header -->
    <div class="mb-8">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold text-base-content">Timesheets</h1>
          <p class="text-base-content/70 mt-1">Manage your time tracking and project hours</p>
        </div>

        <!-- Header Actions -->
        <div class="flex flex-wrap gap-3">
          <div class="join">
            <button class="btn join-item" :class="{ 'btn-active': viewMode === 'list' }"
              @click="onViewModeChange('list')">
              <span class="material-symbols-rounded text-xl">
                list
              </span>
              List
            </button>
            <button class="btn join-item" :class="{ 'btn-active': viewMode === 'calendar' }"
              @click="onViewModeChange('calendar')">
              <span class="material-symbols-rounded text-xl">
                calendar_month
              </span>
              Calendar
            </button>
          </div>

          <button class="btn btn-primary" @click="openNewTimesheetModal">
            <span class="material-symbols-rounded text-xl">
              add
            </span>
            New<span class="hidden sm:inline"> Timesheet</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Statistics Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-8">
      <div class="stats shadow bg-base-200">
        <div class="stat">
          <div class="stat-figure text-primary">
            <span class="material-symbols-rounded text-primary" style="font-size: 2rem;">
              schedule
            </span>
          </div>
          <div class="stat-title">This Week</div>
          <div class="stat-value text-primary">{{ totalHoursThisWeek }}h</div>
          <div class="stat-desc">Total hours logged</div>
        </div>
      </div>

      <div class="stats shadow bg-base-200">
        <div class="stat">
          <div class="stat-figure text-secondary">
            <span class="material-symbols-rounded text-secondary" style="font-size: 2rem;">
              description
            </span>
          </div>
          <div class="stat-title">Draft</div>
          <div class="stat-value text-secondary">{{ statusStats.draft }}</div>
          <div class="stat-desc">Pending submission</div>
        </div>
      </div>

      <div class="stats shadow bg-base-200">
        <div class="stat">
          <div class="stat-figure text-primary">
            <span class="material-symbols-rounded text-primary" style="font-size: 2rem;">
              send
            </span>
          </div>
          <div class="stat-title">Submitted</div>
          <div class="stat-value text-primary">{{ statusStats.submitted }}</div>
          <div class="stat-desc">Awaiting approval</div>
        </div>
      </div>

      <div class="stats shadow bg-base-200">
        <div class="stat">
          <div class="stat-figure text-success">
            <span class="material-symbols-rounded text-success" style="font-size: 2rem;">
              check_circle
            </span>
          </div>
          <div class="stat-title">Billed</div>
          <div class="stat-value text-success">{{ statusStats.billed }}</div>
          <div class="stat-desc">Ready for payroll</div>
        </div>
      </div>

      <div class="stats shadow bg-base-200">
        <div class="stat">
          <div class="stat-figure text-error">
            <span class="material-symbols-rounded text-error" style="font-size: 2rem;">
              close
            </span>
          </div>
          <div class="stat-title">Cancelled</div>
          <div class="stat-value text-error">{{ statusStats.cancelled }}</div>
          <div class="stat-desc">Cancelled timesheets</div>
        </div>
      </div>
    </div>

    <!-- Filters Button -->
    <div class="card bg-base-100 shadow mb-6">
      <div class="card-body py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <button class="btn btn-outline btn-primary gap-2" @click="openFiltersModal">
              <span class="material-symbols-rounded text-xl">
                filter_alt
              </span>
              Filters
              <span v-if="hasActiveFilters" class="badge badge-primary badge-sm">Active</span>
            </button>

            <!-- Active Filters Summary -->
            <div v-if="hasActiveFilters" class="flex flex-wrap gap-2 items-center">
              <span class="text-sm text-base-content/70">Active filters:</span>
              <div class="badge badge-outline gap-1" v-if="dateFilter !== 'this-week'">
                {{ dateFilter === 'custom' ? 'Custom dates' : dateFilter.replace('-', ' ') }}
              </div>
              <div class="badge badge-outline gap-1" v-if="selectedStatuses.length > 0">
                {{ selectedStatuses.length }} status{{ selectedStatuses.length > 1 ? 'es' : '' }}
              </div>
              <div class="badge badge-outline gap-1" v-if="employeeFilter && employeeFilter !== currentUserEmployee">
                Employee
              </div>
              <div class="badge badge-outline gap-1" v-if="projectFilter">
                Project
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Timesheets List -->
    <TimesheetsList
      v-if="viewMode === 'list'"
      :timesheets="filteredTimesheets"
      :loading="loading"
      :deletingTimesheet="deletingTimesheet"
      :lastRefreshed="lastRefreshed"
      :currentPage="currentPage"
      :itemsPerPage="itemsPerPage"
      :totalTimesheets="totalTimesheets"
      @view-timesheet="viewTimesheetModal"
      @submit-timesheet="submitTimesheet"
      @cancel-timesheet="cancelTimesheetItem"
      @delete-timesheet="deleteTimesheetItem"
      @refresh="refreshData"
      @page-change="handlePageChange"
      @items-per-page-change="handleItemsPerPageChange"
    />

    <!-- Calendar View -->
    <div v-else class="card bg-base-100 shadow">
      <div class="card-body">
        <div class="flex items-center justify-between mb-4">
          <h2 class="card-title">Calendar View</h2>
          <div class="flex flex-col items-end gap-1">
            <div class="tooltip tooltip-left" :data-tip="lastRefreshed ? `Last updated: ${formatDateTime(lastRefreshed)}` : 'Refresh timesheet data'">
              <button @click="refreshData" class="btn btn-sm btn-ghost btn-circle" :disabled="loading">
                <span v-if="!loading" class="material-symbols-rounded text-xl">
                  refresh
                </span>
                <span v-else class="loading loading-spinner loading-sm"></span>
              </button>
            </div>
            <div v-if="lastRefreshed" class="text-xs text-base-content/60">
              {{ formatTimeAgo(lastRefreshed) }}
            </div>
          </div>
        </div>
        <TimesheetCalendar :timesheets="filteredTimesheets" :view-mode="viewMode" @timesheet-click="viewTimesheet"
          @date-select="handleDateSelect" @date-range-change="handleCalendarDateRangeChange" />
      </div>
    </div>

    <!-- Modals -->

    <NewTimesheetModal
      :show="showNewTimesheetModal"
      :date="selectedDate || undefined"
      @close="closeNewTimesheetModal"
      @created="handleTimesheetCreated"
      @toast="showToast"
    />

    <ViewTimesheetModal
      :show="showViewDetailsModal"
      :timesheet="selectedTimesheet"
      @close="closeViewModal"
      @updated="handleTimesheetUpdated"
      @toast="showToast"
    />

    <FiltersModal
      :show="showFiltersModal"
      :dateFilter="dateFilter"
      :customStartDate="customStartDate"
      :customEndDate="customEndDate"
      :selectedStatuses="selectedStatuses"
      :employeeFilter="employeeFilter"
      :projectFilter="projectFilter"
      :currentUserEmployee="currentUserEmployee"
      @close="closeFiltersModal"
      @apply="applyFilters"
    />

    <!-- Toast Notification -->
    <Toast
      :show="toast.show"
      :message="toast.message"
      :type="toast.type"
      @close="toast.show = false"
    />
  </div>
</template>
