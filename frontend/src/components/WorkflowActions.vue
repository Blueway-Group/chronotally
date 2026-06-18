<!--
Copyright (c) 2026 Enerlinq.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  // Workflow transitions array
  transitions: {
    type: Array,
    default: () => []
  },
  // Loading state for fetching transitions
  loading: {
    type: Boolean,
    default: false
  },
  // Applying state for when action is being executed
  applying: {
    type: Boolean,
    default: false
  },
  // Whether workflow is available (false if 417 error)
  workflowAvailable: {
    type: Boolean,
    default: true
  },
  // Dropdown direction: 'bottom' (default), 'top', 'left', 'right', 'end'
  direction: {
    type: String,
    default: 'end',
    validator: (value) => ['bottom', 'top', 'left', 'right', 'end'].includes(value)
  },
  // Button size
  size: {
    type: String,
    default: 'sm',
    validator: (value) => ['xs', 'sm', 'md', 'lg'].includes(value)
  },
  // Button variant
  variant: {
    type: String,
    default: 'primary'
  },
  // Custom button classes
  buttonClass: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['action'])

// Computed dropdown direction class
const dropdownDirectionClass = computed(() => {
  if (props.direction === 'bottom') return 'dropdown-bottom'
  if (props.direction === 'top') return 'dropdown-top'
  if (props.direction === 'left') return 'dropdown-left'
  if (props.direction === 'right') return 'dropdown-right'
  if (props.direction === 'end') return 'dropdown-end'
  return 'dropdown-end' // default
})

// Computed button size class
const buttonSizeClass = computed(() => {
  return `btn-${props.size}`
})

// Computed button variant class
const buttonVariantClass = computed(() => {
  return `btn-${props.variant}`
})

const handleAction = (action) => {
  emit('action', action)
}
</script>

<template>
  <!-- Show dropdown only if workflow is available and has transitions -->
  <div
    v-if="workflowAvailable && transitions && transitions.length > 0"
    class="dropdown"
    :class="dropdownDirectionClass"
  >
    <div
      tabindex="0"
      role="button"
      class="btn flex-1"
      :class="[buttonSizeClass, buttonVariantClass, buttonClass]"
      :disabled="applying || undefined"
    >
      <span v-if="applying" class="loading loading-spinner loading-sm"></span>
      <span v-else class="material-symbols-rounded text-base">
        bolt
      </span>
      <span class="hidden sm:inline">Actions</span>
      <svg
        width="12px"
        height="12px"
        class="inline-block h-2 w-2 fill-current opacity-60"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 2048 2048">
        <path d="M1799 349l242 241-1017 1017L7 590l242-241 775 775 775-775z"></path>
      </svg>
    </div>
    <ul
      tabindex="-1"
      class="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow-lg border border-base-300"
    >
      <li v-for="transition in transitions" :key="transition.name">
        <a @click="handleAction(transition.action)" class="flex items-center gap-2">
          <span class="material-symbols-rounded text-sm">
            arrow_forward
          </span>
          <div class="flex flex-col">
            <span class="font-medium">{{ transition.action }}</span>
            <span class="text-xs text-base-content/60">{{ transition.state }} → {{ transition.next_state }}</span>
          </div>
        </a>
      </li>
    </ul>
  </div>

  <!-- Fallback message if workflow is not available -->
  <div v-else-if="!workflowAvailable" class="text-xs text-base-content/60 italic">
    <slot name="no-workflow">
      <!-- Legacy action buttons can be placed in this slot -->
    </slot>
  </div>

  <!-- Loading state -->
  <div v-else-if="loading" class="flex items-center justify-center">
    <span class="loading loading-spinner loading-sm"></span>
  </div>
</template>
