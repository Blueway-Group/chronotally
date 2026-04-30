<!--
Copyright (c) 2026 Enerlinq.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  message: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'success', // 'success' or 'error'
    validator: (value) => ['success', 'error', 'info', 'warning'].includes(value)
  },
  duration: {
    type: Number,
    default: 3000 // Auto-dismiss after 3 seconds
  }
})

const emit = defineEmits(['close'])

let timeoutId = null

// Watch for show prop changes to handle auto-dismiss
watch(() => props.show, (newValue) => {
  if (newValue && props.duration > 0) {
    // Clear any existing timeout
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    // Set new timeout to auto-dismiss
    timeoutId = setTimeout(() => {
      emit('close')
    }, props.duration)
  }
})

const handleClose = () => {
  if (timeoutId) {
    clearTimeout(timeoutId)
  }
  emit('close')
}

const getAlertClass = () => {
  const classes = {
    success: 'alert-success',
    error: 'alert-error',
    info: 'alert-info',
    warning: 'alert-warning'
  }
  return classes[props.type] || 'alert-success'
}

const getIcon = () => {
  switch (props.type) {
    case 'success':
      return 'check_circle'
    case 'error':
      return 'error'
    case 'info':
      return 'info'
    case 'warning':
      return 'warning'
    default:
      return 'check_circle'
  }
}
</script>

<template>
  <div v-if="show" class="toast toast-top toast-center z-50">
    <div :class="['alert', getAlertClass()]">
      <span class="material-symbols-rounded text-2xl">
        {{ getIcon() }}
      </span>
      <span>{{ message }}</span>
      <button
        v-if="duration === 0"
        @click="handleClose"
        class="btn btn-sm btn-circle btn-ghost ml-2">
        <span class="material-symbols-rounded text-base">
          close
        </span>
      </button>
    </div>
  </div>
</template>
