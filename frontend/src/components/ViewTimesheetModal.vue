<!--
Copyright (c) 2026 Enerlinq.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, watch, computed } from 'vue'
import { updateRecord, checkActivityBillable, getRecord } from '../utils/client/api'
import { updateTimeLogRanges } from '../utils/client/dates'
import { getWorkflowTransitions, applyWorkflow } from '../utils/client/api/generic.api'
import ComboBox from './ComboBox.vue'
import WorkflowActions from './WorkflowActions.vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  },
  timesheet: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'updated', 'toast'])

// Local state
const loading = ref(false)
const isEditMode = ref(false)
const editableTimesheet = ref(null)
const isSubmitting = ref(false)

// Workflow state
const workflowTransitions = ref([])
const loadingWorkflow = ref(false)
const applyingWorkflow = ref(false)
const workflowNotAvailable = ref(false)

// Computed property to check if timesheet can be edited
const canEdit = computed(() => {
  if (!editableTimesheet.value) return false
  const status = editableTimesheet.value.status
  return status !== 'Cancelled' && status !== 'Submitted'
})

// Computed property to check if Submit button should be shown
const canSubmit = computed(() => {
  if (!editableTimesheet.value) return false
  return editableTimesheet.value.status === 'Draft'
})

// Helper function to parse date string as local date (not UTC)
const parseLocalDate = (dateString) => {
  const [year, month, day] = dateString.split('-').map(Number)
  return new Date(year, month - 1, day)
}

// Helper function to format date as YYYY-MM-DD in local timezone
const formatDateLocal = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
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

// Helper function to extract date from from_time (format: "2025-10-20 02:00:00")
const extractDate = (fromTime) => {
  if (!fromTime) return null
  return fromTime.split(' ')[0] // Get "2025-10-20" part
}

// Helper function to normalize numeric fields from Frappe (they come as objects)
const normalizeNumericField = (field) => {
  if (typeof field === 'number') return field
  if (field && typeof field === 'object' && 'parsedValue' in field) {
    return field.parsedValue
  }
  if (field && typeof field === 'object' && 'source' in field) {
    return parseFloat(field.source) || 0
  }
  return parseFloat(field) || 0
}

// Computed property to get dates array from timesheet
const dateRange = computed(() => {
  if (!editableTimesheet.value?.start_date || !editableTimesheet.value?.end_date) return []
  // Extract just the date part (YYYY-MM-DD) from the timestamp with timezone
  const startDateStr = editableTimesheet.value.start_date.split(' ')[0]
  const endDateParts = editableTimesheet.value.end_date.split(' ')
  let endDateStr = endDateParts[0]

  // If end_date time is before 12:00:00, it's a boundary timestamp, so exclude that day
  if (endDateParts[1]) {
    const timeStr = endDateParts[1].replace('+00:00', '')
    const [hours] = timeStr.split(':').map(Number)
    if (hours < 12) {
      // Subtract one day from end date
      const endDate = parseLocalDate(endDateStr)
      endDate.setDate(endDate.getDate() - 1)
      endDateStr = formatDateLocal(endDate)
    }
  }

  return getDatesBetween(startDateStr, endDateStr)
})

// Computed property to organize time logs by date
const timeLogsByDate = computed(() => {
  const logsByDate = {}

  if (!editableTimesheet.value?.time_logs) return logsByDate

  // Initialize each date with an empty array
  dateRange.value.forEach(date => {
    logsByDate[date] = []
  })

  // Group time logs by their date (extracted from from_time)
  editableTimesheet.value.time_logs.forEach(log => {
    const logDate = extractDate(log.from_time)
    if (logDate && logsByDate[logDate] !== undefined) {
      logsByDate[logDate].push(log)
    }
  })

  return logsByDate
})

const closeModal = () => {
  isEditMode.value = false
  emit('close')
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
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

const toggleEditMode = () => {
  if (canEdit.value) {
    isEditMode.value = !isEditMode.value
    if (!isEditMode.value) {
      // Reset to original data if canceling edit
      editableTimesheet.value = JSON.parse(JSON.stringify(props.timesheet))
    }
  }
}

// Update to_time when hours change to maintain consistency
// Also cascade changes to all subsequent time_logs for the same date
const updateTimeRange = (log, date) => {
  // Ensure the log has a from_time set with the correct date
  if (!log.from_time) {
    log.from_time = `${date} 00:00:00`
  }

  // Get all logs for this specific date
  const logsForDate = editableTimesheet.value.time_logs.filter(l => extractDate(l.from_time) === date)

  // Find the index of this log within the date's logs
  const indexInDate = logsForDate.findIndex(l => l === log)

  // Use the utility function to update time ranges and cascade changes
  updateTimeLogRanges(logsForDate, log, indexInDate)
}

const saveTimesheet = async () => {
  try {
    loading.value = true

    // Prepare the update payload with proper child table structure
    // Include the 'name' field for each child row so Frappe knows which row to update
    editableTimesheet.value.time_logs = editableTimesheet.value.time_logs.map(log => ({
      name: log.name,              // Required: unique identifier for the child row
      activity_type: log.activity_type,
      hours: log.hours,
      from_time: log.from_time,
      to_time: log.to_time,        // Updated based on hours
      description: log.description,
      is_billable: log.is_billable,
      project: editableTimesheet.value.parent_project,
      parentfield: 'time_logs',    // Required: links to parent field
      parenttype: 'Timesheet'      // Required: links to parent doctype
    }))

    await updateRecord('Timesheet', editableTimesheet.value.name, editableTimesheet.value)
    isEditMode.value = false
    emit('toast', { message: 'Timesheet updated successfully!', type: 'success' })
    emit('updated')
    emit('close')
  } catch (error) {
    console.error('Error updating timesheet:', error)
    emit('toast', { message: 'Failed to update timesheet. Please try again.', type: 'error' })
  } finally {
    loading.value = false
  }
}

const handleEmployeeSelect = (employee) => {
  editableTimesheet.value.employee = employee.name
}

const handleCompanySelect = (company) => {
  editableTimesheet.value.company = company.name
}

const handleProjectSelect = async (project) => {
  editableTimesheet.value.parent_project = project.name;
  editableTimesheet.value.customer = project.customer || editableTimesheet.value.customer || "";

  // Fetch customer's default currency
  if (project.customer) {
    try {
      const customer = await getRecord('Customer', project.customer, ['default_currency'])
      if (customer && customer.default_currency) {
        editableTimesheet.value.currency = customer.default_currency
      }
    } catch (error) {
      console.error('Error fetching customer currency:', error)
    }
  }
}

const handleActivityTypeSelect = async (activityType, logIndex) => {
  editableTimesheet.value.time_logs[logIndex].activity_type = activityType.name

  // Check if the activity is billable and update the time log
  if (editableTimesheet.value.employee) {
    const isBillable = await checkActivityBillable(activityType.name, editableTimesheet.value.employee)
    editableTimesheet.value.time_logs[logIndex].is_billable = isBillable
  } else {
    // If no employee is selected yet, default to false
    editableTimesheet.value.time_logs[logIndex].is_billable = false
  }
}

const addLog = (date) => {
  editableTimesheet.value.time_logs.push({
    hours: 0,
    activity_type: '',
    description: '',
    is_billable: false,
    project: editableTimesheet.value.parent_project,
    from_time: `${date} 00:00:00`,
    to_time: ''
  })
}

const deleteLog = (index) => {
  editableTimesheet.value.time_logs.splice(index, 1)
}

const submitTimesheet = async () => {
  try {
    isSubmitting.value = true

    // Submit the timesheet by updating status and docstatus
    await updateRecord('Timesheet', editableTimesheet.value.name, {
      status: 'Submitted',
      docstatus: 1
    })

    emit('toast', { message: 'Timesheet submitted successfully!', type: 'success' })
    emit('updated')
    emit('close')
  } catch (error) {
    console.error('Error submitting timesheet:', error)
    emit('toast', { message: 'Failed to submit timesheet. Please try again.', type: 'error' })
  } finally {
    isSubmitting.value = false
  }
}

// Load workflow transitions for the timesheet
const loadWorkflowTransitions = async () => {
  if (!editableTimesheet.value?.id) return

  try {
    loadingWorkflow.value = true
    const transitions = await getWorkflowTransitions({
      name: editableTimesheet.value.id,
      doctype: 'Timesheet'
    })
    workflowTransitions.value = transitions
    workflowNotAvailable.value = false
  } catch (error) {
    console.error('Error loading workflow transitions:', error)

    // Check if it's a 417 or 404 error (workflow not configured)
    if ([417, 404].includes(error?.response.status)) {
      workflowNotAvailable.value = true
    }

    workflowTransitions.value = []
  } finally {
    loadingWorkflow.value = false
  }
}

// Apply workflow action to the timesheet
const handleWorkflowAction = async (action) => {
  try {
    applyingWorkflow.value = true

    await applyWorkflow(
      { name: editableTimesheet.value.id, doctype: 'Timesheet' },
      action
    )

    emit('toast', { message: `Workflow action "${action}" applied successfully`, type: 'success' })
    emit('updated')
    emit('close')
  } catch (error) {
    console.error('Error applying workflow action:', error)

    // Extract error message
    let errorMessage = 'Failed to apply workflow action. Please try again.'
    if (error._server_messages) {
      try {
        const messages = JSON.parse(error._server_messages)
        if (Array.isArray(messages) && messages.length > 0) {
          const firstMessage = JSON.parse(messages[0])
          errorMessage = firstMessage.message || firstMessage.title || errorMessage
        }
      } catch (e) {
        // If parsing fails, use default message
      }
    } else if (error.exception) {
      const match = error.exception.match(/:\s*(.+?)(?:\n|$)/)
      if (match && match[1]) {
        errorMessage = match[1]
      }
    } else if (error.message) {
      errorMessage = error.message
    }

    emit('toast', { message: errorMessage, type: 'error' })
  } finally {
    applyingWorkflow.value = false
  }
}

// Watch for timesheet changes and load workflow transitions
watch(() => props.timesheet, async (newTimesheet) => {
  if (newTimesheet) {
    editableTimesheet.value = JSON.parse(JSON.stringify(newTimesheet)) // Deep clone
    isEditMode.value = false // Reset edit mode when timesheet changes

    // Load workflow transitions
    await loadWorkflowTransitions()
  }
}, { deep: true, immediate: true })

</script>

<template>
  <dialog :class="{ 'modal-open': show }" class="modal">
    <div class="modal-box w-11/12 max-w-4xl">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-bold text-lg">
          {{ isEditMode ? 'Edit' : 'Timesheet Details' }} - {{ editableTimesheet?.id }}
        </h3>
        <div class="badge badge-lg" :class="getStatusColor(editableTimesheet?.workflow_state || editableTimesheet?.status)">
          {{ editableTimesheet?.workflow_state || editableTimesheet?.status }}
        </div>
      </div>

      <div v-if="show && editableTimesheet" class="space-y-6">
        <!-- View Mode -->
        <div v-if="!isEditMode" class="space-y-4">
          <!-- Timesheet Details Fieldset - View Mode -->
          <fieldset class="fieldset bg-base-200 border-base-300 rounded-box border p-4">
            <legend class="fieldset-legend">Timesheet Details</legend>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="label" for="employee">Employee</label>
                <div class="input input-bordered flex items-center bg-base-300">
                  {{ editableTimesheet.employee_name || 'No Name' }}
                  <span v-if="editableTimesheet.employee" class="text-sm text-base-content/60 ml-2">
                    ({{ editableTimesheet.employee }})
                  </span>
                </div>
              </div>

              <div>
                <label class="label" for="company">Company</label>
                <div class="input input-bordered flex items-center bg-base-300">
                  {{ editableTimesheet.company || 'No Company' }}
                </div>
              </div>

              <div>
                <label class="label" for="period">Period</label>
                <div class="input input-bordered flex items-center bg-base-300">
                  {{ formatDate(editableTimesheet.start_date) }} - {{ formatDate(editableTimesheet.end_date) }}
                </div>
              </div>

            <div>
              <label class="label" for="project">Project</label>
              <div class="input input-bordered flex items-center bg-base-300">
                {{ editableTimesheet.project_name || editableTimesheet.project || 'No Project' }}
                <span v-if="editableTimesheet.project" class="text-sm text-base-content/60 ml-2">
                  ({{ editableTimesheet.project }})
                </span>
              </div>
            </div>

            </div>

          </fieldset>

          <!-- Time Logs Section - View Mode -->
          <div v-if="editableTimesheet.time_logs?.length > 0" class="mt-6">
            <h4 class="font-semibold text-lg mb-4">Time Logs</h4>

            <div class="space-y-6">
              <div
                v-for="date in dateRange"
                :key="date"
                class="border border-base-300 rounded-box p-4 bg-base-100"
              >
                <!-- Date Header -->
                <div class="mb-4">
                  <h5 class="font-semibold text-base">
                    {{ formatDateDisplay(date) }}
                  </h5>
                </div>

                <!-- Time Logs for this date -->
                <div v-if="timeLogsByDate[date]?.length === 0" class="text-sm text-base-content/60 italic">
                  No time logs for this day
                </div>

                <div v-else class="space-y-3">
                  <div
                    v-for="(log, logIndex) in timeLogsByDate[date]"
                    :key="`${date}-${logIndex}`"
                    class="fieldset bg-base-200 border-base-300 rounded-box border p-3"
                  >
                    <div class="grid grid-cols-1 md:grid-cols-[2fr_auto_3fr] gap-3">
                      <div>
                        <label class="label label-text text-xs">Activity</label>
                        <div class="input input-bordered input-sm flex items-center bg-base-300">
                          {{ log.activity_type }}
                        </div>
                      </div>

                      <div class="w-24">
                        <label class="label label-text text-xs">Hours</label>
                        <div class="input input-bordered input-sm flex items-center bg-base-300">
                          {{ log.hours }}
                        </div>
                      </div>

                      <div>
                        <label class="label label-text text-xs">Description</label>
                        <div class="input input-bordered input-sm flex items-center bg-base-300 w-full">
                          {{ log.description || 'No description' }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Edit Mode -->
        <div v-else class="space-y-4">
          <!-- Timesheet Details Fieldset -->
          <fieldset class="fieldset bg-base-200 border-base-300 rounded-box border p-4">
            <legend class="fieldset-legend">Timesheet Details</legend>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="label" for="employee">Employee</label>
                <ComboBox
                  name="employee"
                  docType="Employee"
                  v-model="editableTimesheet.employee"
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
                  v-model="editableTimesheet.company"
                  :displayFields="['company_name']"
                  placeholder="Search company..."
                  @select="handleCompanySelect"
                />
                <p class="label">Search and select company</p>
              </div>

              <div>
                <label class="label" for="period">Period</label>
                <div class="input input-bordered flex items-center bg-base-300 cursor-not-allowed">
                  {{ formatDate(editableTimesheet.start_date) }} - {{ formatDate(editableTimesheet.end_date) }}
                </div>
                <p class="label">Period cannot be changed</p>
              </div>

            <div>
              <label class="label" for="project">Project</label>
              <ComboBox
                name="project"
                docType="Project"
                v-model="editableTimesheet.parent_project"
                :displayFields="['project_name', 'name', 'customer']"
                placeholder="Search project..."
                @select="handleProjectSelect"
                :minSearchLength="0"
                :filters="[['is_active', '=', 'Yes']]"
              />
              <p class="label">Search and select project</p>
            </div>

            </div>
          </fieldset>

          <!-- Time Logs Section - Edit Mode -->
          <div class="mt-6">
            <h4 class="font-semibold text-lg mb-4">Time Logs</h4>

            <div class="space-y-6">
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
                <div v-if="timeLogsByDate[date]?.length === 0" class="text-sm text-base-content/60 italic">
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
                            @select="(activityType) => handleActivityTypeSelect(activityType, editableTimesheet.time_logs.indexOf(log))"
                          />
                        </div>

                        <div class="w-24">
                          <label class="label label-text text-xs" :for="`hours-${date}-${logIndex}`">Hours</label>
                          <input
                            :id="`hours-${date}-${logIndex}`"
                            v-model.number="log.hours"
                            type="number"
                            step="0.5"
                            min="0"
                            class="input input-bordered w-full"
                            @input="updateTimeRange(log, date)"
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
                        @click="deleteLog(editableTimesheet.time_logs.indexOf(log))"
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
        </div>
      </div>

      <div class="modal-action">
        <div class="flex items-center gap-4 mr-auto">
          <div class="badge badge-lg badge-neutral">
            <span class="material-symbols-rounded text-base mr-1">
              schedule
            </span>
            <span class="hidden sm:inline">Total: </span>{{ editableTimesheet?.total_hours }} <span class="sm:hidden">h</span><span class="hidden sm:inline">hours</span>
          </div>
        </div>
        <template v-if="!isEditMode">
          <button
            v-if="canEdit"
            @click="toggleEditMode"
            type="button"
            class="btn btn-outline btn-square sm:w-auto sm:h-auto sm:px-4"
          >
            <span class="material-symbols-rounded text-base">
              edit
            </span>
            <span class="hidden sm:inline">Edit</span>
          </button>

          <!-- Workflow Actions Component -->
          <WorkflowActions
            :transitions="workflowTransitions"
            :loading="loadingWorkflow"
            :applying="applyingWorkflow"
            :workflow-available="!workflowNotAvailable"
            direction="top"
            size="md"
            variant="success"
            @action="handleWorkflowAction"
          >
            <template #no-workflow>
              <!-- Legacy Submit Button (shown when workflow is not available) -->
              <button
                v-if="canSubmit"
                @click="submitTimesheet"
                type="button"
                class="btn btn-success"
                :disabled="isSubmitting"
              >
                <span v-if="isSubmitting" class="loading loading-spinner loading-sm"></span>
                <span v-else class="material-symbols-rounded text-base">
                  check_circle
                </span>
                <span class="hidden sm:inline">Submit</span>
              </button>
            </template>
          </WorkflowActions>

          <button type="button" class="btn" @click="closeModal">Close</button>
        </template>
        <template v-else>
          <button type="button" class="btn" @click="toggleEditMode">Cancel</button>
          <button
            type="button"
            class="btn btn-primary"
            @click="saveTimesheet"
            :disabled="loading"
          >
            <span v-if="loading" class="loading loading-spinner loading-sm"></span>
            Save Changes
          </button>
        </template>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop" @click="closeModal">
      <button>close</button>
    </form>
  </dialog>
</template>
