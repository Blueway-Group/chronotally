<script setup>
import { ref, watch, computed } from 'vue'
import { createTimesheet, getNewTimesheetData, checkActivityBillable, getRecord } from '../utils/client/api'
import { validateTimeLogs } from '../utils/client/timeValidation'
import ComboBox from './ComboBox.vue'
import { updateTimeLogRanges } from '@/utils/client/dates'

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  },
  date: {
    type: String,
    default: () => {
      const today = new Date()
      const year = today.getFullYear()
      const month = String(today.getMonth() + 1).padStart(2, '0')
      const day = String(today.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }
  }
})

// Helper function to format date as YYYY-MM-DD in local timezone
const formatDateLocal = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// Helper function to parse date string as local date (not UTC)
const parseLocalDate = (dateString) => {
  const [year, month, day] = dateString.split('-').map(Number)
  return new Date(year, month - 1, day)
}

// Helper function to get Monday of current week
const getMondayOfCurrentWeek = () => {
  const today = new Date()
  const day = today.getDay()
  const diff = today.getDate() - day + (day === 0 ? -6 : 1) // Adjust when day is Sunday
  const monday = new Date(today)
  monday.setDate(diff)
  return formatDateLocal(monday)
}

// Helper function to get Friday of current week
const getFridayOfCurrentWeek = () => {
  const today = new Date()
  const day = today.getDay()
  const diff = today.getDate() - day + (day === 0 ? -2 : 5) // Adjust when day is Sunday
  const friday = new Date(today)
  friday.setDate(diff)
  return formatDateLocal(friday)
}

// Helper function to get all dates between start and end (inclusive)
const getDatesBetween = (startDate, endDate) => {
  const dates = []
  const start = parseLocalDate(startDate)
  const end = parseLocalDate(endDate)

  for (let date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
    dates.push(formatDateLocal(date))
  }

  return dates
}

// Helper function to format date for display
const formatDateDisplay = (dateString) => {
  const date = parseLocalDate(dateString)
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
  return date.toLocaleDateString('en-US', options)
}

const emit = defineEmits(['close', 'created', 'toast'])

// Reactive state
const loading = ref(false)
const newTimesheetData = ref(null)
const startDate = ref('') // Start date for timesheet range
const endDate = ref('') // End date for timesheet range

// New timesheet form
const newTimesheet = ref({
  employee: '',
  company: '',
  project: '',
  customer: '',
  currency: '',
  status: 'Draft', // Always set to Draft
  time_logs: []
})

// Computed property to get dates array
const dateRange = computed(() => {
  if (!startDate.value || !endDate.value) return []
  return getDatesBetween(startDate.value, endDate.value)
})

// Computed property to organize time logs by date
const timeLogsByDate = computed(() => {
  const logsByDate = {}

  // Initialize each date with an empty array
  dateRange.value.forEach(date => {
    logsByDate[date] = newTimesheet.value.time_logs.filter(log => log.log_date === date)
  })

  return logsByDate
})

// Computed property for total hours
const totalHours = computed(() => {
  return newTimesheet.value.time_logs.reduce((sum, log) => {
    const hours = parseFloat(log.hours) || 0
    return sum + hours
  }, 0)
})

// Watch for modal open to initialize data
watch(() => props.show, async (newVal) => {
  if (newVal) {
    await initializeForm()
  }
})

// Watch for date range changes and add empty time logs for days without any
watch([startDate, endDate], ([newStart, newEnd]) => {
  if (!newStart || !newEnd) return

  const dates = getDatesBetween(newStart, newEnd)

  // For each date, check if it has any time logs
  dates.forEach(date => {
    const logsForDate = newTimesheet.value.time_logs.filter(log => log.log_date === date)

    // If no logs exist for this date, add one empty log
    if (logsForDate.length === 0) {
      addLog(date)
    }
  })

  // Remove time logs for dates that are no longer in the range
  newTimesheet.value.time_logs = newTimesheet.value.time_logs.filter(log =>
    dates.includes(log.log_date)
  )
})

// Watch for project changes and update all time logs
watch(() => newTimesheet.value.project, (newProject) => {
  // Update project for all existing time logs
  newTimesheet.value.time_logs.forEach(log => {
    log.project = newProject || ''
  })
})

const initializeForm = async () => {
  // Initialize dates to current week (Monday to Friday)
  startDate.value = getMondayOfCurrentWeek()
  endDate.value = getFridayOfCurrentWeek()
  newTimesheet.value.status = 'Draft'

  await loadNewTimesheetData()
}

const loadNewTimesheetData = async () => {
  try {
    const newTsResponse = await getNewTimesheetData()
    newTimesheetData.value = newTsResponse

    // Auto-populate employee with current user's employee ID
    if (newTsResponse.employee_id) {
      newTimesheet.value.employee = newTsResponse.employee_id
    }

    // Auto-populate company with user's default company
    if (newTsResponse.default_company) {
      newTimesheet.value.company = newTsResponse.default_company
    }

  } catch (error) {
    console.error('Error loading new timesheet data:', error)
  }
}

const handleEmployeeSelect = async (employee) => {
  newTimesheet.value.employee = employee.name

  // Re-check billable status for all existing time logs with activity types
  for (let i = 0; i < newTimesheet.value.time_logs.length; i++) {
    const log = newTimesheet.value.time_logs[i]
    if (log.activity_type) {
      const isBillable = await checkActivityBillable(log.activity_type, employee.name)
      log.is_billable = isBillable
    }
  }
}

const handleCompanySelect = (company) => {
  newTimesheet.value.company = company.name
}

const handleProjectSelect = async (project) => {
  newTimesheet.value.project = project.name
  newTimesheet.value.customer = project.customer || ''

  // Fetch customer's default currency
  if (project.customer) {
    try {
      const customer = await getRecord('Customer', project.customer, ['default_currency'])
      if (customer && customer.default_currency) {
        newTimesheet.value.currency = customer.default_currency
      }
    } catch (error) {
      console.error('Error fetching customer currency:', error)
    }
  }
}

const handleActivityTypeSelect = async (activityType, logIndex) => {
  newTimesheet.value.time_logs[logIndex].activity_type = activityType.name

  // Check if the activity is billable and update the time log
  if (newTimesheet.value.employee) {
    const isBillable = await checkActivityBillable(activityType.name, newTimesheet.value.employee)
    newTimesheet.value.time_logs[logIndex].is_billable = isBillable
  } else {
    // If no employee is selected yet, default to false
    newTimesheet.value.time_logs[logIndex].is_billable = false
  }
}

const addLog = (date) => {
  newTimesheet.value.time_logs.push({
    log_date: date,
    hours: 0,
    activity_type: '',
    description: '',
    is_billable: false,
    project: newTimesheet.value.project || '',
    from_time: '',
    to_time: ''
  })
}

const deleteLog = (index) => {
  newTimesheet.value.time_logs.splice(index, 1)
}

const updateTimes = (log, date) => {
  // Ensure the log has a from_time set with the correct date
  if (!log.from_time) {
    log.from_time = `${date} 00:00:00`
  }

  // Get all logs for this specific date
  const logsForDate = newTimesheet.value.time_logs.filter(l => l.log_date === date)

  // Find the index of this log within the date's logs
  const indexInDate = logsForDate.findIndex(l => l === log)

  // Use the utility function to update time ranges and cascade changes
  updateTimeLogRanges(logsForDate, log, indexInDate)
}

const closeModal = () => {
  // Reset form
  newTimesheet.value = {
    employee: '',
    company: '',
    project: '',
    customer: '',
    currency: '',
    status: 'Draft',
    time_logs: []
  }
  startDate.value = ''
  endDate.value = ''
  emit('close')
}

const showToast = (message, type = 'success') => {
  emit('toast', { message, type })
}

const createNewTimesheet = async () => {
  try {
    loading.value = true

    // Validate and update all time logs for each date
    dateRange.value.forEach(date => {
      const logsForDate = newTimesheet.value.time_logs.filter(log => log.log_date === date)

      if (logsForDate.length > 0) {
        const firstLog = logsForDate[0]

        // Initialize the first log's from_time if not set
        if (!firstLog.from_time) {
          firstLog.from_time = `${date} 00:00:00`
        }

        // Call once on the first log - it will cascade to all subsequent logs automatically
        updateTimeLogRanges(logsForDate, firstLog, 0)
      }
    })

    const errors = validateTimeLogs(newTimesheet.value.time_logs)
    if (errors.length > 0) {
      console.error("Validation errors:", errors)
      showToast("Validation errors: " + errors.join(', '), 'error')
      return
    }

    await createTimesheet(newTimesheet.value)
    showToast('Timesheet created successfully!', 'success')
    emit('created')
    closeModal()
  } catch (error) {
    console.error('Error creating timesheet:', error)
    showToast('Failed to create timesheet. Please try again.', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <dialog :class="{ 'modal-open': show }" class="modal">
    <div class="modal-box w-11/12 max-w-4xl max-h-[90vh] overflow-y-auto">
      <h3 class="font-bold text-lg mb-4">New Timesheet</h3>

      <form @submit.prevent="createNewTimesheet" class="space-y-4">
        <!-- Timesheet Details Fieldset -->
        <fieldset class="fieldset bg-base-200 border-base-300 rounded-box border p-4">
          <legend class="fieldset-legend">Timesheet Details</legend>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="label" for="employee">Employee</label>
              <ComboBox
                name="employee"
                docType="Employee"
                v-model="newTimesheet.employee"
                :displayFields="['employee_name', 'name']"
                placeholder="Search employee by name or ID..."
                @select="handleEmployeeSelect"
              />
              <p class="label">Search and select employee</p>
            </div>

            <div>
              <label class="label" for="company">Company</label>
              <ComboBox
                name="company"
                docType="Company"
                v-model="newTimesheet.company"
                :displayFields="['company_name']"
                placeholder="Search company..."
                @select="handleCompanySelect"
              />
              <p class="label">Search and select company</p>
            </div>

            <div>
              <label class="label">Date Range (Start - End)</label>
              <div class="join w-full">
                <input
                  id="start-date"
                  v-model="startDate"
                  type="date"
                  class="input input-bordered join-item w-1/2"
                  required
                />
                <input
                  id="end-date"
                  v-model="endDate"
                  type="date"
                  class="input input-bordered join-item w-1/2"
                  :min="startDate"
                  required
                />
              </div>
            </div>

          <div>
            <label class="label" for="project">Project</label>
            <ComboBox
              name="project"
              docType="Project"
              v-model="newTimesheet.project"
              :displayFields="['project_name', 'name', 'customer']"
              placeholder="Search project..."
              @select="handleProjectSelect"
              :minSearchLength="0"
              :filters="[['is_active', '=', 'Yes'], ['status', '=', 'Open']]"
            />
            <p class="label">Search and select project</p>
          </div>


          </div>
        </fieldset>

        <!-- Time Logs by Date Section -->
        <div class="mt-6">
          <h4 class="font-semibold text-lg mb-4">Time Logs</h4>

          <div v-if="dateRange.length === 0" class="alert alert-info">
            <span>Please select start and end dates to begin adding time logs.</span>
          </div>

          <div v-else class="space-y-6">
            <div
              v-for="date in dateRange"
              :key="date"
              class="border border-base-300 rounded-box p-4 bg-base-100"
            >
              <!-- Date Header -->
              <div class="flex items-center justify-between mb-4">
                <h5 class="font-semibold text-base">
                  {{ formatDateDisplay(date) }}
                </h5>
                <button
                  class="btn btn-sm btn-outline"
                  type="button"
                  @click="addLog(date)"
                >
                  <span class="material-symbols-rounded text-lg">
                    add
                  </span>
                  Add Time Log
                </button>
              </div>

              <!-- Time Logs for this date -->
              <div v-if="timeLogsByDate[date].length === 0" class="text-sm text-base-content/60 italic">
                No time logs for this day
              </div>

              <div v-else class="space-y-3">
                <div
                  v-for="(log, logIndex) in timeLogsByDate[date]"
                  :key="`${date}-${logIndex}`"
                  class="fieldset bg-base-200 border-base-300 rounded-box border p-3"
                >
                  <div class="flex items-start gap-3">
                    <div class="flex-1 grid grid-cols-1 md:grid-cols-[2fr_auto_3fr] gap-3">
                      <div>
                        <label class="label label-text text-xs" :for="`activity-${date}-${logIndex}`">Activity</label>
                        <ComboBox
                          :name="`activity-${date}-${logIndex}`"
                          docType="Activity Type"
                          v-model="log.activity_type"
                          :displayFields="['activity_type']"
                          placeholder="Search activity..."
                          :filters="[['disabled', '=', 0]]"
                          :minSearchLength="0"
                          @select="(activityType) => handleActivityTypeSelect(activityType, newTimesheet.time_logs.indexOf(log))"
                        />
                      </div>

                      <div class="w-24">
                        <label class="label label-text text-xs" :for="`hours-${date}-${logIndex}`">Hours</label>
                        <input
                          :id="`hours-${date}-${logIndex}`"
                          v-model="log.hours"
                          type="number"
                          step="0.5"
                          min="0"
                          class="input input-bordered w-full"
                          @input="updateTimes(log, date)"
                          required
                        />
                      </div>

                      <div>
                        <label class="label label-text text-xs" :for="`description-${date}-${logIndex}`">Description</label>
                        <input
                          :id="`description-${date}-${logIndex}`"
                          v-model="log.description"
                          type="text"
                          class="input input-bordered w-full"
                          placeholder="Task description..."
                        />
                      </div>
                    </div>

                    <button
                      type="button"
                      class="btn btn-sm btn-square btn-error btn-outline mt-6"
                      @click="deleteLog(newTimesheet.time_logs.indexOf(log))"
                      title="Delete this time log"
                    >
                      <span class="material-symbols-rounded">
                        delete
                      </span>
                    </button>
                  </div>

                  <input v-model="log.from_time" type="hidden"/>
                  <input v-model="log.to_time" type="hidden"/>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Modal Actions inside form -->
        <div class="modal-action">
          <div class="flex items-center gap-4 mr-auto">
            <div class="badge badge-lg badge-neutral">
              <span class="material-symbols-rounded text-base mr-1">
                schedule
              </span>
              <span class="hidden sm:inline">Total: </span>{{ totalHours.toFixed(1) }} <span class="hidden sm:inline">hours</span> <div class="inline sm:hidden">h</div>
            </div>
          </div>
          <button type="button" class="btn" @click="closeModal">Cancel</button>
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="loading"
          >
            <span v-if="loading" class="loading loading-spinner loading-sm"></span>
            Create Timesheet
          </button>
        </div>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop" @click="closeModal">
      <button>close</button>
    </form>
  </dialog>
</template>
