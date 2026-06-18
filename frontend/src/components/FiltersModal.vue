<!--
Copyright (c) 2026 Enerlinq.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, computed, watch } from 'vue'
import ComboBox from './ComboBox.vue'

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  },
  dateFilter: {
    type: String,
    default: 'this-week'
  },
  customStartDate: {
    type: String,
    default: ''
  },
  customEndDate: {
    type: String,
    default: ''
  },
  selectedStatuses: {
    type: Array,
    default: () => []
  },
  employeeFilter: {
    type: String,
    default: ''
  },
  projectFilter: {
    type: String,
    default: ''
  },
  currentUserEmployee: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'apply'])

// Local state for filters
const localDateFilter = ref(props.dateFilter)
const localCustomStartDate = ref(props.customStartDate)
const localCustomEndDate = ref(props.customEndDate)
const localSelectedStatuses = ref([...props.selectedStatuses])
const localEmployeeFilter = ref(props.employeeFilter)
const localProjectFilter = ref(props.projectFilter)

// Watch for prop changes to update local state
watch(() => props.show, (newVal) => {
  if (newVal) {
    // Reset local state to props when modal opens
    localDateFilter.value = props.dateFilter
    localCustomStartDate.value = props.customStartDate
    localCustomEndDate.value = props.customEndDate
    localSelectedStatuses.value = [...props.selectedStatuses]
    localEmployeeFilter.value = props.employeeFilter
    localProjectFilter.value = props.projectFilter
  }
})

const availableStatuses = ['Draft', 'Submitted', 'Billed', 'Cancelled']

const isStatusSelected = (status) => {
  return localSelectedStatuses.value.includes(status)
}

const toggleStatus = (status) => {
  const index = localSelectedStatuses.value.indexOf(status)
  if (index > -1) {
    localSelectedStatuses.value.splice(index, 1)
  } else {
    localSelectedStatuses.value.push(status)
  }
}

const clearAllStatuses = () => {
  localSelectedStatuses.value = []
}

const getStatusColor = (status) => {
  const colors = {
    'Draft': 'badge-ghost',
    'Submitted': 'badge-primary',
    'Billed': 'badge-success',
    'Cancelled': 'badge-error'
  }
  return colors[status] || 'badge-ghost'
}

const handleEmployeeSelect = (employee) => {
  localEmployeeFilter.value = employee ? employee.name : ''
}

const clearEmployeeFilter = () => {
  localEmployeeFilter.value = ''
}

const handleProjectSelect = (project) => {
  localProjectFilter.value = project ? project.name : ''
}

const clearProjectFilter = () => {
  localProjectFilter.value = ''
}

const handleClose = () => {
  emit('close')
}

const handleApply = () => {
  emit('apply', {
    dateFilter: localDateFilter.value,
    customStartDate: localCustomStartDate.value,
    customEndDate: localCustomEndDate.value,
    selectedStatuses: [...localSelectedStatuses.value],
    employeeFilter: localEmployeeFilter.value,
    projectFilter: localProjectFilter.value
  })
}

const handleClearAll = () => {
  localDateFilter.value = 'this-week'
  localCustomStartDate.value = ''
  localCustomEndDate.value = new Date().toISOString().split('T')[0]
  localSelectedStatuses.value = []
  localEmployeeFilter.value = '';
  localProjectFilter.value = ''
}

// Computed property to check if any filters are active (different from defaults)
const hasActiveFilters = computed(() => {
  return localDateFilter.value !== 'this-week' ||
    localSelectedStatuses.value.length > 0 ||
    localEmployeeFilter.value !== '' ||
    localProjectFilter.value !== ''
})
</script>

<template>
  <dialog :class="['modal', { 'modal-open': show }]">
    <div class="modal-box w-11/12 max-w-3xl">
      <!-- Modal Header -->
      <div class="flex items-center justify-between mb-6">
        <h3 class="font-bold text-2xl">Filter Timesheets</h3>
        <button class="btn btn-sm btn-circle btn-ghost" @click="handleClose">
          <span class="material-symbols-rounded text-2xl">
            close
          </span>
        </button>
      </div>

      <!-- Filters Content -->
      <div class="flex flex-col gap-6">
        <!-- Date Filter Section -->

        <div class="flex flex-wrap gap-4 items-end">
          <fieldset class="fieldset flex-1 min-w-[200px]">
            <legend class="fieldset-legend">Period</legend>
            <select v-model="localDateFilter" class="select select-bordered w-full">
              <option value="this-week">This Week</option>
              <option value="last-week">Last Week</option>
              <option value="this-month">This Month</option>
              <option value="last-month">Last Month</option>
              <option value="custom">Custom Range</option>
            </select>
          </fieldset>

          <div v-if="localDateFilter === 'custom'" class="flex gap-2 flex-wrap">
            <fieldset class="fieldset">
              <legend class="fieldset-legend">From</legend>
              <input v-model="localCustomStartDate" type="date" class="input input-bordered" />
            </fieldset>
            <fieldset class="fieldset">
              <legend class="fieldset-legend">To</legend>
              <input v-model="localCustomEndDate" type="date" class="input input-bordered" />
            </fieldset>
          </div>
        </div>

        <!-- Employee Filter Section -->

        <fieldset class="fieldset">
          <legend class="fieldset-legend w-full">
            Filter by Employee
            <span class="label float-right text-xs">
              {{ localEmployeeFilter === currentUserEmployee ? 'Current user' : localEmployeeFilter ? 'Custom employee' : 'All employees' }}
            </span>
          </legend>
          <div class="join w-full">
            <div class="flex-1">
              <ComboBox
                name="employee-filter-modal"
                docType="Employee"
                v-model="localEmployeeFilter"
                :displayFields="['employee_name', 'name']"
                placeholder="Search employee..."
                @select="handleEmployeeSelect"
              />
            </div>
            <button
              v-if="localEmployeeFilter"
              class="btn btn-square join-item"
              @click="clearEmployeeFilter"
              title="Clear employee filter">
              <span class="material-symbols-rounded text-xl">
                close
              </span>
            </button>
          </div>
        </fieldset>

        <!-- Project Filter Section -->

        <fieldset class="fieldset">
          <legend class="fieldset-legend w-full">
            Filter by Project
            <span class="label float-right text-xs">
              {{ localProjectFilter ? 'Filtered by project' : 'All projects' }}
            </span>
          </legend>
          <div class="join w-full">
            <div class="flex-1">
              <ComboBox
                name="project-filter-modal"
                docType="Project"
                v-model="localProjectFilter"
                :displayFields="['project_name', 'name']"
                placeholder="Search project..."
                @select="handleProjectSelect"
              />
            </div>
            <button
              v-if="localProjectFilter"
              class="btn btn-square join-item"
              @click="clearProjectFilter"
              title="Clear project filter">
              <span class="material-symbols-rounded text-xl">
                close
              </span>
            </button>
          </div>
        </fieldset>

        <!-- Status Filter Section -->

        <fieldset class="fieldset">
          <legend class="fieldset-legend">Filter by Status</legend>

          <div class="filter">
            <!-- All/Reset button -->
            <input
              class="btn filter-reset"
              type="radio"
              name="status-filter-modal"
              aria-label="All"
              :checked="localSelectedStatuses.length === 0"
              @click="clearAllStatuses"
            />

            <!-- Status filter buttons -->
            <input
              v-for="status in availableStatuses"
              :key="status"
              class="btn"
              :class="isStatusSelected(status) ? getStatusColor(status) : ''"
              type="radio"
              name="status-filter-modal"
              :aria-label="status"
              :checked="isStatusSelected(status)"
              @click="toggleStatus(status)"
            />
          </div>

          <!-- Helper text -->
          <p class="label text-sm">
            {{ localSelectedStatuses.length === 0
              ? 'Click status buttons to filter timesheets'
              : `Filtering by ${localSelectedStatuses.length} status${localSelectedStatuses.length > 1 ? 'es' : ''}: ${localSelectedStatuses.join(', ')}` }}
          </p>
        </fieldset>
      </div>

      <!-- Modal Actions -->
      <div class="modal-action">
        <button
          class="btn btn-ghost"
          @click="handleClearAll"
          :disabled="!hasActiveFilters">
          Clear All
        </button>
        <button class="btn btn-ghost" @click="handleClose">
          Cancel
        </button>
        <button class="btn btn-primary" @click="handleApply">
          <span class="material-symbols-rounded text-xl mr-1">
            filter_alt
          </span>
          Apply Filters
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop" @click="handleClose">
      <button>close</button>
    </form>
  </dialog>
</template>
