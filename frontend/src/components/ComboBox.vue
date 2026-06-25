<!--
Copyright (c) 2026 Blueway Consulting LLC.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { listRecords, getRecord } from '@/utils/client/api'

const props = defineProps({
  name: {
    type: String,
    required: true
  },
  docType: {
    type: String,
    required: true
  },
  filters: {
    type: Array,
    default: () => []
  },
  minSearchLength: {
    type: Number,
    default: 2
  },
  debounce: {
    type: Number,
    default: 600
  },
  defaultValue: {
    type: String,
    default: ''
  },
  displayFields: {
    type: Array,
    default: () => ['name']
  },
  placeholder: {
    type: String,
    default: 'Type to search...'
  },
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'select'])

// Reactive state
const searchTerm = ref('')
const displayValue = ref('')
const results = ref([])
const loading = ref(false)
const isOpen = ref(false)
const selectedIndex = ref(-1)
const dropdownRef = ref(null)
const inputRef = ref(null)

// Debounce timer
let debounceTimer = null

// Initialize display value from default value
onMounted(async () => {
  if (props.defaultValue) {
    displayValue.value = props.defaultValue
  }
  if (props.modelValue) {
    // If modelValue is provided, fetch the display value
    await fetchInitialDisplayValue()
  }
  
  // If minSearchLength is 0, load initial results on mount
  if (props.minSearchLength === 0) {
    await loadInitialResults()
  }
})

// Watch for external modelValue changes
watch(() => props.modelValue, (newValue) => {
  if (newValue && newValue !== searchTerm.value) {
    fetchInitialDisplayValue()
  } else if (!newValue) {
    // Clear the display value when modelValue is cleared
    displayValue.value = ''
    searchTerm.value = ''
    results.value = []
    isOpen.value = false
  }
})

const fetchInitialDisplayValue = async () => {
  if (!props.modelValue) return
  
  try {
    const doc = await getRecord(
      props.docType,
      props.modelValue,
      ['name', ...props.displayFields]
    )
    
    if (doc) {
      displayValue.value = formatDisplayValue(doc)
      searchTerm.value = props.modelValue
    }
  } catch (error) {
    console.error('Error fetching initial display value:', error)
    displayValue.value = props.modelValue
  }
}

const formatDisplayValue = (doc) => {
  if (!doc) return ''
  
  return props.displayFields
    .map(field => doc[field])
    .filter(val => val)
    .join(' - ')
}

const loadInitialResults = async () => {
  // Only load if minSearchLength is 0
  if (props.minSearchLength !== 0) return
  
  loading.value = true
  
  try {
    // Build filters array
    const combinedFilters = [...props.filters]
    
    // Load initial results without search term
    results.value = await listRecords({
      docType: props.docType,
      fields: ['name', ...props.displayFields],
      filters: combinedFilters.length > 0 ? combinedFilters : undefined,
      limit: 20
    })
    
    // Don't open dropdown yet, just load the results
    // Dropdown will open on focus
  } catch (error) {
    console.error('Error loading initial results:', error)
    results.value = []
  } finally {
    loading.value = false
  }
}

const performSearch = async (term) => {
  // If minSearchLength is 0 and no term, use the pre-loaded results
  if (props.minSearchLength === 0 && (!term || term.length === 0)) {
    // Just open the dropdown with existing results
    if (results.value.length > 0) {
      isOpen.value = true
      selectedIndex.value = -1
    }
    return
  }
  
  // Otherwise, perform regular search with minimum length check
  if (!term || term.length < props.minSearchLength) {
    results.value = []
    isOpen.value = false
    return
  }

  loading.value = true
  
  try {
    // Build filters array - combine additional filters with search filters
    const combinedFilters = [...props.filters]
    
    // Use generic listRecords function
    results.value = await listRecords({
      docType: props.docType,
      fields: ['name', ...props.displayFields],
      filters: combinedFilters.length > 0 ? combinedFilters : undefined,
      searchTerm: term,
      searchFields: props.displayFields,
      limit: 20
    })
    
    selectedIndex.value = -1
  } catch (error) {
    console.error('Error searching:', error)
    results.value = []
    isOpen.value = false
  } finally {
    loading.value = false
  }
}

const onInput = (event) => {
  const value = event.target.value
  displayValue.value = value
  
  // Clear the debounce timer
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  
  // Set a new debounce timer
  debounceTimer = setTimeout(() => {
    performSearch(value)
  }, props.debounce)
}

const selectItem = (item) => {
  searchTerm.value = item.name
  displayValue.value = formatDisplayValue(item)
  results.value = []
  isOpen.value = false
  selectedIndex.value = -1
  
  emit('update:modelValue', item.name)
  emit('select', item)
  
  // Blur the input to close keyboard on mobile
  if (inputRef.value) {
    inputRef.value.blur()
  }
}

const onKeyDown = (event) => {
  if (!isOpen.value) return
  
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      selectedIndex.value = Math.min(selectedIndex.value + 1, results.value.length - 1)
      scrollToSelected()
      break
    case 'ArrowUp':
      event.preventDefault()
      selectedIndex.value = Math.max(selectedIndex.value - 1, -1)
      scrollToSelected()
      break
    case 'Enter':
      event.preventDefault()
      if (selectedIndex.value >= 0 && results.value[selectedIndex.value]) {
        selectItem(results.value[selectedIndex.value])
      }
      break
    case 'Escape':
      event.preventDefault()
      isOpen.value = false
      selectedIndex.value = -1
      break
  }
}

const scrollToSelected = () => {
  if (!dropdownRef.value || selectedIndex.value < 0) return
  
  const selectedElement = dropdownRef.value.children[selectedIndex.value]
  if (selectedElement) {
    selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }
}

const onFocus = () => {
  isOpen.value = true
}

const onBlur = () => {
  // Delay closing to allow click events on dropdown items
  setTimeout(() => {
    isOpen.value = false
    selectedIndex.value = -1
  }, 200)
}

// Click outside handler
const handleClickOutside = (event) => {
  if (inputRef.value && !inputRef.value.contains(event.target) && 
      dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    isOpen.value = false
    selectedIndex.value = -1
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
})
</script>

<template>
  <div class="relative">
    <!-- Input Field -->
    <div class="relative">
      <input
        ref="inputRef"
        :name="name"
        type="text"
        :value="displayValue"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
        @keydown="onKeyDown"
        :placeholder="placeholder"
        class="input input-bordered w-full"
        autocomplete="off"
      />
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="absolute right-3 top-1/2 -translate-y-1/2">
        <span class="loading loading-spinner loading-sm"></span>
      </div>
    </div>
    
    <!-- Dropdown Results -->
    <div
      v-if="isOpen && results.length > 0"
      ref="dropdownRef"
      class="absolute z-50 w-full mt-1 bg-base-100 border border-base-300 rounded-box shadow-lg max-h-60 overflow-auto"
    >
      <ul class="menu w-full p-2">
        <li
          v-for="(item, index) in results"
          :key="item.name"
          :class="{ 'bg-base-200': index === selectedIndex }"
          @click="selectItem(item)"
        >
          <a class="block">
            <div class="flex flex-col">
              <span class="font-medium">{{ formatDisplayValue(item) }}</span>
              <span v-if="item.name !== formatDisplayValue(item)" class="text-xs opacity-60">{{ item.name }}</span>
            </div>
          </a>
        </li>
      </ul>
    </div>
    
    <!-- Loading Message -->
    <div
      v-if="isOpen && loading && results.length === 0 && displayValue.length >= minSearchLength"
      class="absolute z-50 w-full mt-1 bg-base-100 border border-base-300 rounded-box shadow-lg p-4"
    >
      <p class="text-sm text-base-content/60 text-center flex items-center justify-center gap-2">
        <span class="loading loading-spinner loading-sm"></span>
        Searching...
      </p>
    </div>
    
    <!-- No Results Message -->
    <div
      v-if="isOpen && results.length === 0 && !loading && displayValue.length >= minSearchLength"
      class="absolute z-50 w-full mt-1 bg-base-100 border border-base-300 rounded-box shadow-lg p-4"
    >
      <p class="text-sm text-base-content/60 text-center">No results found</p>
    </div>
    
    <!-- Hint Text -->
    <div
      v-if="!isOpen && !displayValue && minSearchLength > 0"
      class="absolute z-50 w-full mt-1 bg-base-100 border border-base-300 rounded-box shadow-lg p-2"
    >
      <p class="text-xs text-base-content/60 text-center">Type at least {{ minSearchLength }} characters to search</p>
    </div>
  </div>
</template>

<style scoped>
/* Ensure dropdown appears above other elements */
.absolute.z-50 {
  z-index: 50;
}

/* Smooth scrolling for keyboard navigation */
.menu li {
  transition: background-color 0.15s ease;
}

/* Better mobile touch targets */
.menu li a {
  min-height: 3rem;
  display: flex;
  align-items: center;
}
</style>
