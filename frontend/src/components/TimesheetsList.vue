<!--
Copyright (c) 2026 Enerlinq.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { updateRecord, amendTimesheet } from '@/utils/client/api'
import { getWorkflowTransitions, applyWorkflow } from '@/utils/client/api/generic.api'
import Toast from './Toast.vue'
import WorkflowActions from './WorkflowActions.vue'

const props = defineProps({
  timesheets: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  deletingTimesheet: {
    type: String,
    default: null
  },
  lastRefreshed: {
    type: Date,
    default: null
  },
  currentPage: {
    type: Number,
    default: 1
  },
  itemsPerPage: {
    type: Number,
    default: 5
  },
  totalTimesheets: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits([
  'view-timesheet',
  'submit-timesheet',
  'cancel-timesheet',
  'delete-timesheet',
  'refresh',
  'page-change',
  'items-per-page-change'
])

// Reactive state for multi-select
const selectedTimesheets = ref([])
const isSubmitting = ref(false)

// Workflow actions state
const workflowTransitions = ref({}) // { timesheetId: [transitions] }
const loadingWorkflow = ref({}) // { timesheetId: boolean }
const applyingWorkflow = ref({}) // { timesheetId: boolean }
const workflowNotAvailable = ref({}) // { timesheetId: boolean } - true if 417 error

// Toast notification state
const toast = ref({
  show: false,
  message: '',
  type: 'success' // 'success' or 'error'
})

// Computed properties
const selectedDraftTimesheets = computed(() => {
  return selectedTimesheets.value.filter(id => {
    const timesheet = props.timesheets.find(ts => ts.id === id)
    return timesheet && timesheet.status === 'Draft'
  })
})

const showSubmitButton = computed(() => {
  return selectedDraftTimesheets.value.length > 0
})

// Pagination computed properties
const totalPages = computed(() => {
  return Math.ceil(props.totalTimesheets / props.itemsPerPage)
})

const hasNextPage = computed(() => {
  return props.currentPage < totalPages.value
})

const hasPreviousPage = computed(() => {
  return props.currentPage > 1
})

// Generate visible page numbers with ellipsis
// Shows: 1 ... 5 6 [7] 8 9 ... 20
const visiblePages = computed(() => {
  const current = props.currentPage
  const total = totalPages.value
  const delta = 2 // Number of pages to show on each side of current page
  const pages = []

  if (total <= 7) {
    // Show all pages if total is small
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
    return pages
  }

  // Always show first page
  pages.push(1)

  // Calculate range around current page
  const rangeStart = Math.max(2, current - delta)
  const rangeEnd = Math.min(total - 1, current + delta)

  // Add ellipsis after first page if needed
  if (rangeStart > 2) {
    pages.push('...')
  }

  // Add pages around current page
  for (let i = rangeStart; i <= rangeEnd; i++) {
    pages.push(i)
  }

  // Add ellipsis before last page if needed
  if (rangeEnd < total - 1) {
    pages.push('...')
  }

  // Always show last page
  pages.push(total)

  return pages
})

// Pagination methods
const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    emit('page-change', page)
  }
}

const nextPage = () => {
  if (hasNextPage.value) {
    emit('page-change', props.currentPage + 1)
  }
}

const previousPage = () => {
  if (hasPreviousPage.value) {
    emit('page-change', props.currentPage - 1)
  }
}

const changeItemsPerPage = (perPage) => {
  emit('items-per-page-change', perPage)
}

const getStatusColor = (status) => {
  const colors = {
    'Draft': 'badge-ghost',
    'Submitted': 'badge-primary',
    'Billed': 'badge-success',
    'Canceled': 'badge-error',
    'Rejected': 'badge-warning',
    'Approved': 'badge-info',
    'Pending': 'badge-neutral'
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

// Multi-select methods
const handleCheckboxChange = (timesheetId, isChecked) => {
  if (isChecked) {
    selectedTimesheets.value.push(timesheetId)
  } else {
    const index = selectedTimesheets.value.indexOf(timesheetId)
    if (index > -1) {
      selectedTimesheets.value.splice(index, 1)
    }
  }
}

const isSelected = (timesheetId) => {
  return selectedTimesheets.value.includes(timesheetId)
}

const selectAll = () => {
  selectedTimesheets.value = props.timesheets.map(ts => ts.id)
}

const clearSelection = () => {
  selectedTimesheets.value = []
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
  return error.message || error.exc_type || 'Failed to submit timesheets. Please try again.'
}

const submitSelectedTimesheets = async () => {
  if (selectedDraftTimesheets.value.length === 0) return

  try {
    isSubmitting.value = true

    // Submit all selected draft timesheets
    const promises = selectedDraftTimesheets.value.map(timesheetId =>
      updateRecord('Timesheet', timesheetId, { status: 'Submitted', docstatus: 1 })
    )

    await Promise.all(promises)

    // Clear selection and refresh
    const count = selectedDraftTimesheets.value.length
    selectedTimesheets.value = []

    // Show success toast
    toast.value = {
      show: true,
      message: `Successfully submitted ${count} timesheet${count > 1 ? 's' : ''}`,
      type: 'success'
    }

    emit('refresh')

  } catch (error) {
    console.error('Error submitting timesheets:', error)

    // Show error toast with extracted message
    const errorMessage = getErrorMessage(error)
    toast.value = {
      show: true,
      message: errorMessage,
      type: 'error'
    }
  } finally {
    isSubmitting.value = false
  }
}

// Amend a cancelled timesheet
const amendTimesheetItem = async (id) => {
  if (confirm('This will create a new draft timesheet from the cancelled one. Continue?')) {
    try {
      const newTimesheet = await amendTimesheet(id)

      // Show success toast
      toast.value = {
        show: true,
        message: `Amended timesheet created: ${newTimesheet.name}`,
        type: 'success'
      }

      // Emit events to refresh the list
      emit('refresh')
    } catch (error) {
      console.error('Error amending timesheet:', error)
      const errorMessage = getErrorMessage(error)

      // Show error toast
      toast.value = {
        show: true,
        message: errorMessage,
        type: 'error'
      }
    }
  }
}

const downloadFile = (url, fileName) => {
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const downloadTimesheet = (timesheet) => {
  const url = `/api/method/frappe.utils.print_format.download_pdf?doctype=Timesheet&name=${timesheet.id}&format=Standard&no_letterhead=0&letterhead=Autosolutions&settings=%7B%7D&_lang=es-MX`

  const fileName = `timesheet-${timesheet.id}.pdf`
  downloadFile(url, fileName)
}

// Load workflow transitions for a timesheet
const loadWorkflowTransitions = async (timesheet) => {
  try {
    loadingWorkflow.value[timesheet.id] = true
    const transitions = await getWorkflowTransitions({
      name: timesheet.id,
      doctype: 'Timesheet'
    })
    workflowTransitions.value[timesheet.id] = transitions
    workflowNotAvailable.value[timesheet.id] = false
  } catch (error) {
    console.error('Error loading workflow transitions:', error)

    // Check if it's a 417 or 404 error (workflow not configured)
    if ([417, 404].includes(error?.response.status)) {
      workflowNotAvailable.value[timesheet.id] = true
    }

    workflowTransitions.value[timesheet.id] = []
  } finally {
    loadingWorkflow.value[timesheet.id] = false
  }
}

// Clear workflow cache (call on refresh or navigation)
const clearWorkflowCache = () => {
  workflowTransitions.value = {}
  workflowNotAvailable.value = {}
  loadingWorkflow.value = {}
}

// Apply workflow action to a timesheet
const handleWorkflowAction = async (timesheet, action) => {
  try {
    applyingWorkflow.value[timesheet.id] = true

    await applyWorkflow(
      { name: timesheet.id, doctype: 'Timesheet' },
      action
    )

    // Show success toast
    toast.value = {
      show: true,
      message: `Workflow action "${action}" applied successfully`,
      type: 'success'
    }

    // Refresh the list to show updated status
    // setTimeout(() => {
      emit('refresh')
	// }, 500)
  } catch (error) {
    console.error('Error applying workflow action:', error)
    const errorMessage = getErrorMessage(error)

    // Show error toast
    toast.value = {
      show: true,
      message: errorMessage,
      type: 'error'
    }
  } finally {
    applyingWorkflow.value[timesheet.id] = false
  }
}

// Watch for timesheets or refresh changes and load workflow transitions in parallel
watch([() => props.timesheets, () => props.lastRefreshed], async ([newTimesheets, newLastRefreshed], [oldTimesheets, oldLastRefreshed]) => {

	// Clear cache if lastRefreshed changed (user clicked refresh)
  if (newLastRefreshed && newLastRefreshed !== oldLastRefreshed) {
    clearWorkflowCache()
  }

  if (newTimesheets && newTimesheets.length > 0) {
    // Filter timesheets that need workflow transitions loaded
    const timesheetsToLoad = newTimesheets.filter(timesheet =>
      !workflowTransitions.value[timesheet.id] && !loadingWorkflow.value[timesheet.id]
    )

    // Load all workflow transitions in parallel
    if (timesheetsToLoad.length > 0) {
      await Promise.all(
        timesheetsToLoad.map(timesheet => loadWorkflowTransitions(timesheet))
      )
    }
  }
}, { immediate: true })

// Clear cache when component is unmounted (navigation away)
onUnmounted(() => {
  clearWorkflowCache()
})
</script>

<template>
  <div class="card bg-base-100 shadow">
    <div class="card-body">

      <!-- Header Section - Responsive Layout -->
      <div class="flex flex-col gap-4 mb-4">

        <!-- Title Row -->
        <div class="flex items-center justify-between">
          <h2 class="card-title">Timesheet Records</h2>

          <!-- Refresh Button (always visible) -->
          <div class="flex flex-col items-end">
            <div class="tooltip tooltip-left" :data-tip="lastRefreshed ? `Last updated: ${formatDateTime(lastRefreshed)}` : 'Refresh timesheet data'">
              <button @click="emit('refresh')" class="btn btn-sm btn-ghost btn-circle" :disabled="loading">
                <span v-if="!loading" class="material-symbols-rounded text-xl">
                  refresh
                </span>
                <span v-else class="loading loading-spinner loading-sm"></span>
              </button>
            </div>
            <div v-if="lastRefreshed" class="text-xs text-base-content/60 hidden sm:block">
              {{ formatTimeAgo(lastRefreshed) }}
            </div>
          </div>
        </div>

        <!-- Multi-select Controls Row (responsive) -->
        <div v-if="timesheets.length > 0" class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">

          <!-- Selection Controls -->
          <div class="flex items-center gap-2 flex-wrap">
            <button @click="selectAll" class="btn btn-xs sm:btn-sm btn-outline">
              <span class="hidden sm:inline">Select All</span>
              <span class="sm:hidden">All</span>
            </button>
            <button v-if="selectedTimesheets.length > 0" @click="clearSelection" class="btn btn-xs sm:btn-sm btn-outline btn-error">
              Clear
            </button>
            <span v-if="selectedTimesheets.length > 0" class="text-xs sm:text-sm text-base-content/60 whitespace-nowrap">
              {{ selectedTimesheets.length }} selected
            </span>
          </div>

          <!-- Submit Button -->
          <div v-if="showSubmitButton" class="tooltip tooltip-bottom sm:tooltip-left" data-tip="Submit selected draft timesheets">
            <button @click="submitSelectedTimesheets" class="btn btn-sm btn-success w-full sm:w-auto" :disabled="isSubmitting">
              <span v-if="isSubmitting" class="loading loading-spinner loading-sm"></span>
              <span v-else class="material-symbols-rounded text-base">
                check_circle
              </span>
              <span class="hidden sm:inline">Submit ({{ selectedDraftTimesheets.length }})</span>
              <span class="sm:hidden">Submit {{ selectedDraftTimesheets.length }}</span>
            </button>
          </div>
        </div>

      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-20">
        <span class="loading loading-spinner loading-lg text-primary"></span>
      </div>

      <!-- Empty State -->
      <div v-else-if="timesheets.length === 0" class="flex flex-col items-center justify-center py-20">
        <span class="material-symbols-rounded text-base-content/30 mb-4" style="font-size: 4rem;">
          description
        </span>
        <p class="text-base-content/60 text-lg">No timesheets found</p>
        <p class="text-base-content/40 text-sm">Try adjusting your filters or create a new timesheet</p>
      </div>

      <!-- Timesheet List -->
      <div v-else>
        <ul class="list bg-base-100 rounded-box shadow space-y-2">
          <li v-for="timesheet in timesheets" :key="timesheet.id"
            class="list-row relative p-6 hover:bg-base-50 transition-colors duration-200 border border-base-300 rounded-box"
            :class="{ 'ring-2 ring-primary ring-opacity-50': isSelected(timesheet.id) }">

            <!-- Mobile Checkbox - Absolutely positioned at top left -->
            <div class="absolute -top-6 z-10 xl:hidden">
              <input
                type="checkbox"
                :checked="isSelected(timesheet.id)"
                @change="handleCheckboxChange(timesheet.id, $event.target.checked)"
                class="checkbox checkbox-primary checkbox-lg bg-base-100 border-2"
              />
            </div>

            <!-- Desktop Checkbox Column -->
            <div class="hidden xl:flex items-center justify-center min-w-10 mr-4">
              <input
                type="checkbox"
                :checked="isSelected(timesheet.id)"
                @change="handleCheckboxChange(timesheet.id, $event.target.checked)"
                class="checkbox checkbox-primary"
              />
            </div>

            <div class="flex flex-col gap-4 sm:flex-row flex-wrap pl-2 xl:pl-0 w-full">

              <!-- ID Badge -->
              <div class="flex flex-col items-center justify-center min-w-20">
                <span class="font-mono text-xs text-base-content/60 bg-base-200 px-3 py-1 rounded-full mb-2">
                  {{ timesheet.id }}
                </span>
                <div class="badge badge-lg" :class="getStatusColor(timesheet.workflow_state || timesheet.status)">
                  {{ timesheet.workflow_state || timesheet.status }}
                </div>
              </div>

              <!-- Main Content (growing column) -->
              <div class="grow mx-6">
                <div class="flex flex-row flex-wrap justify-between gap-4">
                  <!-- Period -->
                  <div>
                    <div class="text-base-content/60 text-xs uppercase tracking-wide font-semibold mb-1">Period</div>
                    <div class="font-medium text-sm">
                      {{ formatDate(timesheet.start_date) }}
                    </div>
                    <div class="text-sm text-base-content/60">
                      to {{ formatDate(timesheet.end_date) }}
                    </div>
                  </div>

                  <!-- Employee -->
                  <div>
                    <div class="text-base-content/60 text-xs uppercase tracking-wide font-semibold mb-1">Employee
                    </div>
                    <div class="font-medium">{{ timesheet.employee_name || 'N/A' }}</div>
                    <div class="text-sm text-base-content/70">{{ timesheet.employee }}</div>
                  </div>

                  <!-- Project -->
                  <div>
                    <div class="text-base-content/60 text-xs uppercase tracking-wide font-semibold mb-1">Project</div>
                    <div class="font-semibold">{{ timesheet.project_name }}</div>
                    <div class="text-sm text-base-content/70">{{ timesheet.project }}</div>
                  </div>

                </div>
              </div>

              <!-- Hours Display -->
              <div class="flex flex-col items-center justify-center min-w-20">
                <div class="text-3xl font-bold text-primary">{{ timesheet.total_hours }}</div>
                <div class="text-xs text-base-content/60 uppercase tracking-wide">Hours</div>
              </div>

              <!-- Action Buttons -->
              <div class="flex flex-col gap-2 min-w-[100px]">
                <div class="flex gap-1">
                  <div class="tooltip" data-tip="View Details">
                    <button @click="emit('view-timesheet', timesheet)" class="btn btn-sm btn-outline flex-1">
                      <span class="material-symbols-rounded text-base">
                        visibility
                      </span>
                      <span class="inline xl:hidden">View Details</span>
                    </button>
                  </div>
                </div>

                <!-- Workflow Actions Component -->
                <WorkflowActions
                  :transitions="workflowTransitions[timesheet.id]"
                  :loading="loadingWorkflow[timesheet.id]"
                  :applying="applyingWorkflow[timesheet.id]"
                  :workflow-available="!workflowNotAvailable[timesheet.id]"
                  direction="end"
                  size="sm"
                  variant="primary"
                  @action="(action) => handleWorkflowAction(timesheet, action)"
                >
                  <template #no-workflow>
                    <!-- Legacy Action Buttons (shown when workflow is not available) -->
                    <div class="flex gap-1">
                      <div v-if="timesheet.status === 'Draft'" class="tooltip" data-tip="Submit for Approval">
                        <button @click="emit('submit-timesheet', timesheet.id)" class="btn btn-sm btn-success flex-1">
                          <span class="material-symbols-rounded text-base">
                          check_circle
                          </span>
                          <span class="inline xl:hidden">Submit</span>
                        </button>
                      </div>
                      <div v-if="timesheet.status === 'Submitted'" class="tooltip tooltip-warning"
                        data-tip="Cancel Timesheet">
                        <button @click="emit('cancel-timesheet', timesheet.id)" class="btn btn-sm btn-warning flex-1">
                          <span class="material-symbols-rounded text-base">
                            close
                          </span>
                          <span class="inline xl:hidden">Cancel Timesheet</span>
                        </button>
                      </div>
                    </div>
                  </template>
                </WorkflowActions>

                <div class="flex gap-1">
                  <div class="tooltip" data-tip="Download Timesheet">
                    <button @click="downloadTimesheet(timesheet)" class="btn btn-sm btn-secondary">
                      <span class="material-symbols-rounded text-base">
                        download
                      </span>
                      <span class="inline xl:hidden">Download</span>
                    </button>
                  </div>
                  <div v-if="timesheet.status === 'Cancelled'" class="tooltip tooltip-info"
                    data-tip="Amend Timesheet">
                    <button @click="amendTimesheetItem(timesheet.id)" class="btn btn-sm btn-info flex-1">
                      <span class="material-symbols-rounded text-base">
                        edit
                      </span>
                      <span class="inline xl:hidden">Amend</span>
                    </button>
                  </div>
                  <div v-if="timesheet.status !== 'Submitted'" class="tooltip tooltip-error"
                    data-tip="Delete Timesheet">
                    <button
                      @click="emit('delete-timesheet', timesheet.id)"
                      class="btn btn-sm btn-error btn-outline flex-1"
                      :disabled="deletingTimesheet === timesheet.id"
                    >
                      <span v-if="deletingTimesheet === timesheet.id" class="loading loading-spinner loading-sm"></span>
                      <span v-else class="material-symbols-rounded text-base">
                        delete
                      </span>
                      <span class="inline xl:hidden">Delete Timesheet</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </li>
        </ul>

        <!-- Pagination Controls -->
        <div v-if="totalPages > 1" class="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6">
          <!-- Page Info -->
          <div class="text-sm text-base-content/60">
            Showing {{ (currentPage - 1) * itemsPerPage + 1 }} to {{ Math.min(currentPage * itemsPerPage, totalTimesheets) }} of {{ totalTimesheets }} timesheets
          </div>

          <!-- Pagination Buttons -->
          <div class="join">
            <button
              @click="previousPage"
              class="join-item btn btn-sm"
              :disabled="!hasPreviousPage"
            >
              <span class="material-symbols-rounded text-base">
                chevron_left
              </span>
            </button>

            <template v-for="(page, index) in visiblePages" :key="index">
              <!-- Ellipsis -->
              <button
                v-if="page === '...'"
                class="join-item btn btn-sm btn-disabled"
                disabled
              >
                ...
              </button>
              <!-- Page number -->
              <button
                v-else
                @click="goToPage(page)"
                class="join-item btn btn-sm"
                :class="{ 'btn-active': props.currentPage === page }"
              >
                {{ page }}
              </button>
            </template>

            <button
              @click="nextPage"
              class="join-item btn btn-sm"
              :disabled="!hasNextPage"
            >
              <span class="material-symbols-rounded text-base">
                chevron_right
              </span>
            </button>
          </div>

          <!-- Items per page selector -->
          <div class="flex items-center gap-2">
            <label for="items-per-page" class="text-sm text-base-content/60">Per page:</label>
            <select
              id="items-per-page"
              :value="itemsPerPage"
              class="select select-sm select-bordered"
              @change="changeItemsPerPage(Number($event.target.value))"
            >
              <option :value="5">5</option>
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Toast Notification -->
  <Toast
    :show="toast.show"
    :message="toast.message"
    :type="toast.type"
    @close="toast.show = false"
  />
</template>
