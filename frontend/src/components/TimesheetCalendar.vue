<!--
Copyright (c) 2026 Blueway Consulting LLC.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<template>
  <div>
    <FullCalendar
    v-if="ready"
    ref="calendarRef"
      :options="calendarOptions"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { getTimesheetSettings } from '../utils/client/api'

// Props
const props = defineProps({
  timesheets: {
    type: Array,
    default: () => []
  },
  viewMode: {
    type: String,
    default: 'dayGridMonth'
  }
})

// Emits
const emit = defineEmits(['timesheet-click', 'timesheet-select', 'date-select', 'date-range-change'])

const calendarRef = ref(null)
const ready = ref(false)
const selectedView = ref('dayGridMonth')

// Calendar options
const calendarOptions = ref({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: selectedView.value,
  headerToolbar: {
    left: 'prev,next,today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay'
  },
  height: 'auto',
  selectable: true,
  selectMirror: true,
  dayMaxEvents: true,
  weekends: true,
  editable: false,
  droppable: false,
  events: [],
  eventClick: handleEventClick,
  dateClick: handleDateClick,
  select: handleDateSelect,
  eventClassNames: ['cursor-pointer'],
  eventDisplay: 'block',
  displayEventTime: false,
  eventMouseEnter: handleEventMouseEnter,
  eventMouseLeave: handleEventMouseLeave,
  datesSet: handleDatesSet,
  viewDidMount: handleViewDidMount,
  // Additional touch-friendly options
  longPressDelay: 800,
  eventLongPressDelay: 800,
  // Handle touch events for better mobile experience
  eventDidMount: handleEventDidMount
})

// Transform timesheets to calendar events
const calendarEvents = computed(() => {
  return props.timesheets.map(timesheet => {
    // Calculate the color based on status
    const statusColors = {
      'Draft': '#64748b',      // slate-500
      'Submitted': '#3b82f6',  // blue-500 (primary)
      'Billed': '#10b981',      // emerald-500
      'Cancelled': '#ef4444'    // red-500
    }

    const color = statusColors[timesheet.status] || '#64748b'

    // Helper function to extract date from datetime string
    const extractDate = (dateTimeStr) => {
      if (!dateTimeStr) return null
      // Extract just the date portion (YYYY-MM-DD) from various formats
      // Handles: "2025-10-03 06:00:00+00:00", "2025-10-03T06:00:00", "2025-10-03"
      const match = dateTimeStr.match(/^(\d{4}-\d{2}-\d{2})/)
      return match ? match[1] : null
    }

    // Always create a single event for the parent timesheet (not individual time logs)
    const startDate = extractDate(timesheet.start_date)
    const endDate = extractDate(timesheet.end_date)

    return {
      id: timesheet.id,
      title: `${timesheet.project_name || timesheet.project || 'No Project'} - ${timesheet.total_hours}h`,
      start: startDate,
      end: endDate,
      allDay: true,
      backgroundColor: color,
      borderColor: color,
      textColor: '#ffffff',
      extendedProps: {
        timesheet: timesheet,
        hours: timesheet.total_hours,
        status: timesheet.status,
        employee: timesheet.employee || '',
        employee_name: timesheet.employee_name || 'Current User',
        company: timesheet.company,
        project: timesheet.project,
        project_name: timesheet.project_name || '',
        time_logs: timesheet.time_logs || []
      }
    }
  })
})

// Event handlers
function handleEventClick(clickInfo) {
  emit('timesheet-click', clickInfo.event.extendedProps.timesheet)
}

// Handle single date clicks (better for mobile touch)
function handleDateClick(dateClickInfo) {
  emit('date-select', {
    start: dateClickInfo.date,
    end: dateClickInfo.date,
    startStr: dateClickInfo.dateStr,
    endStr: dateClickInfo.dateStr,
    allDay: dateClickInfo.allDay
  })
}

// Handle date range selection (drag to select on desktop)
function handleDateSelect(selectInfo) {
  emit('date-select', {
    start: selectInfo.start,
    end: selectInfo.start, // Use start for end to indicate single day selection
    startStr: selectInfo.startStr,
    endStr: selectInfo.startStr,
    allDay: selectInfo.allDay
  })
}

function handleDatesSet(dateInfo) {
  // This event fires when the calendar view changes (navigation, view type change, etc.)
  // It provides the current visible date range
  emit('date-range-change', {
    start: dateInfo.start,
    end: dateInfo.end,
    startStr: dateInfo.startStr,
    endStr: dateInfo.endStr,
    view: dateInfo.view.type
  })
}

function handleViewDidMount(viewInfo) {
  // This fires when a view is initially mounted
  // Emit initial date range
  emit('date-range-change', {
    start: viewInfo.view.activeStart,
    end: viewInfo.view.activeEnd,
    startStr: viewInfo.view.activeStart.toISOString().split('T')[0],
    endStr: viewInfo.view.activeEnd.toISOString().split('T')[0],
    view: viewInfo.view.type
  })
}

function handleEventMouseEnter(mouseEnterInfo) {
  const event = mouseEnterInfo.event
  const props = event.extendedProps

  // Check if we're on a touch device
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0

  // Remove any existing tooltip first
  if (mouseEnterInfo.el._tooltip) {
    document.body.removeChild(mouseEnterInfo.el._tooltip)
    mouseEnterInfo.el._tooltip = null
  }

  // Create tooltip content
  const tooltip = document.createElement('div')
  tooltip.className = 'timesheet-tooltip fixed z-50 bg-base-100 border border-base-300 rounded-lg shadow-lg p-3 text-sm max-w-sm pointer-events-none'
  tooltip.style.pointerEvents = 'none'
  tooltip.style.zIndex = '9999'

  // Add touch-specific classes for better mobile experience
  if (isTouchDevice) {
    tooltip.classList.add('touch-action-none')
    // Add a unique ID for easier cleanup
    tooltip.id = `tooltip-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  // Escape HTML content to prevent XSS
  const escapeHtml = (text) => {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
  }

  // Build time logs summary if available
  let timeLogsHtml = ''
  if (props.time_logs && props.time_logs.length > 0) {
    timeLogsHtml = '<div class="mt-2 pt-2 border-t border-base-300"><div class="font-semibold text-xs uppercase">Time Logs:</div>'
    props.time_logs.forEach(log => {
      timeLogsHtml += `
        <div class="mt-1 text-xs">
          <div>${escapeHtml(log.activity_type || 'No activity')} - ${escapeHtml(String(log.hours))}h</div>
          ${log.description ? `<div class="text-base-content/60">${escapeHtml(log.description)}</div>` : ''}
        </div>
      `
    })
    timeLogsHtml += '</div>'
  }

  tooltip.innerHTML = `
    <div class="font-semibold text-base-content">${escapeHtml(props.project_name || props.project || 'No Project')}</div>
    <div class="text-base-content/70 mt-1">
      <div>Employee: ${escapeHtml(props.employee_name || 'Unknown')}</div>
      <div>Total Hours: ${escapeHtml(String(props.hours || 0))}h</div>
      <div>Status: <span class="badge badge-sm ${getStatusBadgeClass(props.status)}">${escapeHtml(props.status || 'Unknown')}</span></div>
    </div>
    ${timeLogsHtml}
  `

  document.body.appendChild(tooltip)

  // Position tooltip with better positioning logic
  const rect = mouseEnterInfo.el.getBoundingClientRect()
  const tooltipRect = tooltip.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  let left = rect.right + 10
  let top = rect.top

  // Adjust horizontal position if tooltip would go off-screen
  if (left + tooltipRect.width > viewportWidth) {
    left = rect.left - tooltipRect.width - 10
  }

  // Adjust vertical position if tooltip would go off-screen
  if (top + tooltipRect.height > viewportHeight) {
    top = viewportHeight - tooltipRect.height - 10
  }

  // Ensure tooltip doesn't go above the top of the viewport
  if (top < 10) {
    top = 10
  }

  tooltip.style.left = Math.max(10, left) + 'px'
  tooltip.style.top = top + 'px'

  // Store tooltip reference
  mouseEnterInfo.el._tooltip = tooltip

  // On touch devices, set up automatic cleanup after a delay
  if (isTouchDevice) {
    // Clear tooltip after 3 seconds on touch devices
    setTimeout(() => {
      if (tooltip && tooltip.parentNode) {
        try {
          document.body.removeChild(tooltip)
        } catch (error) {
          console.debug('Tooltip already removed:', error)
        }
      }
      if (mouseEnterInfo.el._tooltip === tooltip) {
        mouseEnterInfo.el._tooltip = null
      }
    }, 3000)
  }
}

function handleEventDidMount(mountInfo) {
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0

  if (isTouchDevice) {
    // Add touch event listeners for better mobile handling
    const element = mountInfo.el

    // Store original handlers
    element._originalTouchStart = element.ontouchstart
    element._originalTouchEnd = element.ontouchend

    // Add touch handlers for tooltip cleanup
    element.addEventListener('touchstart', function(e) {
      // Clean up any existing tooltips when starting a new touch
      cleanupTooltips()
    }, { passive: true })

    element.addEventListener('touchend', function(e) {
      // Delay cleanup to allow for tap events to process
      setTimeout(() => {
        if (element._tooltip) {
          try {
            document.body.removeChild(element._tooltip)
          } catch (error) {
            console.debug('Tooltip already removed during touchend:', error)
          }
          element._tooltip = null
        }
      }, 100)
    }, { passive: true })
  }
}

function handleEventMouseLeave(mouseLeaveInfo) {
  if (mouseLeaveInfo.el._tooltip) {
    try {
      document.body.removeChild(mouseLeaveInfo.el._tooltip)
    } catch (error) {
      // Tooltip might have already been removed, ignore error
      console.debug('Tooltip already removed or not found:', error)
    }
    mouseLeaveInfo.el._tooltip = null
  }
}

function getStatusBadgeClass(status) {
  const classes = {
    'Draft': 'badge-ghost',
    'Submitted': 'badge-primary',
    'Billed': 'badge-success',
    'Cancelled': 'badge-error'
  }
  return classes[status] || 'badge-ghost'
}

const timesheetSettings = async() => {
  try {
    let defaultPeriod = ''
    const response = await getTimesheetSettings()
    if(response.default_period === 'Work Week'){
      defaultPeriod = 'timeGridWeek'
      console.log('Default period set to Work Week')
    } else {
      defaultPeriod = 'dayGridMonth'
      console.log('Default period set to Month')
    }

    return defaultPeriod
  } catch (error) {
    console.error('Error fetching timesheet settings:', error)
    return 'dayGridMonth'
  }
}

// Watch for changes in timesheets and update calendar events
watch(() => props.timesheets, (newTimesheets) => {
  console.log('Timesheets prop changed in calendar:', newTimesheets?.length, 'timesheets')
}, { deep: true })

watch(calendarEvents, (newEvents) => {
  console.log('Calendar events updated:', newEvents)
  calendarOptions.value.events = newEvents
}, { deep: true, immediate: true })

// Watch for view mode changes
watch(() => props.viewMode, (newViewMode) => {
  if (newViewMode === 'calendar') {
    // Default to dayGridMonth when switching to calendar
    calendarOptions.value.initialView = 'dayGridMonth'
  }
})

// Watch for page visibility changes to clean up tooltips
watch(() => document.visibilityState, (newState) => {
  if (newState === 'hidden') {
    // Clean up tooltips when page becomes hidden (user switches tabs, etc.)
    cleanupTooltips()
  }
})

// Cleanup function to remove all tooltips
const cleanupTooltips = () => {
  const tooltips = document.querySelectorAll('.timesheet-tooltip')
  tooltips.forEach(tooltip => {
    try {
      if (tooltip.parentNode) {
        tooltip.parentNode.removeChild(tooltip)
      }
    } catch (error) {
      console.debug('Error removing tooltip during cleanup:', error)
    }
  })
}

// Global touch/click handler to close tooltips when tapping outside
const handleGlobalInteraction = (event) => {
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0

  // Only handle touch events on touch devices, mouse events on others
  if ((isTouchDevice && event.type === 'touchstart') || (!isTouchDevice && event.type === 'click')) {
    // Check if the touch/click is outside any calendar event
    const isCalendarEvent = event.target.closest('.fc-event')
    const isTooltip = event.target.closest('.timesheet-tooltip')

    // If we're not touching a calendar event or tooltip, clean up all tooltips
    if (!isCalendarEvent && !isTooltip) {
      cleanupTooltips()
    }
  }
}

// Methods to programmatically change the calendar view
const changeView = (viewName) => {
  // This would need to be called on the calendar instance
  // For now, we'll update the initial view for next time
  calendarOptions.value.initialView = viewName
}

// Expose methods to parent component
defineExpose({
  changeView,
  cleanupTooltips
})

onMounted(async () => {
  // Add global event listeners for touch/click outside to clean up tooltips
  document.addEventListener('touchstart', handleGlobalInteraction, { passive: true })
  document.addEventListener('click', handleGlobalInteraction, { passive: true })

  // Clean up tooltips on scroll (important for mobile)
  document.addEventListener('scroll', cleanupTooltips, { passive: true })
  window.addEventListener('scroll', cleanupTooltips, { passive: true })

  // Clean up tooltips on orientation change (mobile)
  window.addEventListener('orientationchange', cleanupTooltips, { passive: true })

  const view = await timesheetSettings()
  if (view) {
    selectedView.value = view
    calendarOptions.value.initialView = view
  }
  ready.value = true

  // Clean up any existing tooltips on mount
  cleanupTooltips()
})

// Cleanup tooltips when component is unmounted
onUnmounted(() => {
  // Remove global event listeners
  document.removeEventListener('touchstart', handleGlobalInteraction)
  document.removeEventListener('click', handleGlobalInteraction)
  document.removeEventListener('scroll', cleanupTooltips)
  window.removeEventListener('scroll', cleanupTooltips)
  window.removeEventListener('orientationchange', cleanupTooltips)

  // Clean up any remaining tooltips
  cleanupTooltips()
})
</script>

<style>

/* Tooltip improvements */
.timesheet-tooltip {
  animation: fadeIn 0.2s ease-in;
  backdrop-filter: blur(8px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  pointer-events: none !important;
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

/* Touch-specific tooltip styles */
@media (pointer: coarse) {
  .timesheet-tooltip {
    /* Slightly larger on touch devices for better readability */
    font-size: 0.875rem;
    padding: 0.875rem;
    max-width: 20rem;
    /* Position further from touch point to avoid finger obstruction */
    transform: translateY(-10px);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
