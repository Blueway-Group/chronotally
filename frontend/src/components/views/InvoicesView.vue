<!--
Copyright (c) 2026 Blueway Consulting LLC.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getInvoices } from '@/utils/client/api/invoices.api'
import CreateInvoiceModal from '../CreateInvoiceModal.vue'

// State
const showCreateInvoiceModal = ref(false)
const invoices = ref([])
const loadingInvoices = ref(false)

// Pagination state
const currentPage = ref(1)
const pageSize = ref(10)
const totalInvoices = ref(0)

// Toast state
const toast = ref({
  show: false,
  message: '',
  type: 'success'
})

// Load initial data
onMounted(async () => {
  await loadInvoices()
})

const loadInvoices = async () => {
  try {
    loadingInvoices.value = true
    const response = await getInvoices({
      limit: pageSize.value,
      start: (currentPage.value - 1) * pageSize.value,
      order_by: 'modified desc'
    })
    invoices.value = response.data
    totalInvoices.value = response.total_count
  } catch (error) {
    console.error('Error loading invoices:', error)
    showToast('Failed to load invoices', 'error')
  } finally {
    loadingInvoices.value = false
  }
}

const goToPage = (page) => {
  currentPage.value = page
  loadInvoices()
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadInvoices()
  }
}

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    loadInvoices()
  }
}

const totalPages = computed(() => {
  return Math.ceil(totalInvoices.value / pageSize.value)
})

const paginationRange = computed(() => {
  const range = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    range.push(i)
  }
  
  return range
})

const openCreateInvoiceModal = () => {
  showCreateInvoiceModal.value = true
}

const closeCreateInvoiceModal = () => {
  showCreateInvoiceModal.value = false
}

const showToast = (message, type = 'success') => {
  toast.value = {
    show: true,
    message,
    type
  }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

const handleInvoiceCreated = async (response) => {
  showToast(response.message, 'success')

  // Reload invoices
  await loadInvoices()
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

const formatCurrency = (amount) => {
  if (!amount) return '0.00'
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount)
}

const getStatusBadgeClass = (status) => {
  const statusLower = status?.toLowerCase() || ''
  if (statusLower === 'paid') return 'badge-success'
  if (statusLower === 'unpaid') return 'badge-warning'
  if (statusLower === 'draft') return 'badge-ghost'
  if (statusLower === 'cancelled') return 'badge-error'
  return 'badge-neutral'
}
</script>

<template>
  <div class="container mx-auto p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold">Invoices</h1>
        <p class="text-base-content/70 mt-1">Manage your invoices</p>
      </div>
      <button class="btn btn-primary" @click="openCreateInvoiceModal">
        <span class="material-symbols-rounded text-xl">
          add
        </span>
        Create Invoice
      </button>
    </div>

    <!-- Invoices List -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title mb-4">Invoices</h2>

        <!-- Loading State -->
        <div v-if="loadingInvoices" class="flex justify-center py-12">
          <span class="loading loading-spinner loading-lg"></span>
        </div>

        <!-- Empty State -->
        <div v-else-if="invoices.length === 0" class="text-center py-12">
          <span class="material-symbols-rounded text-6xl text-base-content/30">
            receipt_long
          </span>
          <p class="text-base-content/70 mt-4">No invoices found</p>
          <p class="text-sm text-base-content/50 mt-2">Create your first invoice to get started</p>
        </div>

        <!-- Invoices Table -->
        <div v-else class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Customer</th>
                <th>Project</th>
                <th>Posting Date</th>
                <th>Due Date</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="invoice in invoices" :key="invoice.name">
                <td class="font-mono text-sm">{{ invoice.name }}</td>
                <td>{{ invoice.customer }}</td>
                <td>{{ invoice.project || '-' }}</td>
                <td>{{ formatDate(invoice.posting_date) }}</td>
                <td>{{ formatDate(invoice.due_date) }}</td>
                <td class="font-semibold">{{ formatCurrency(invoice.grand_total) }}</td>
                <td>
                  <span :class="['badge', getStatusBadgeClass(invoice.status)]">
                    {{ invoice.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Pagination -->
          <div class="flex items-center justify-between mt-4 border-t pt-4">
            <div class="text-sm text-base-content/70">
              Showing {{ (currentPage - 1) * pageSize + 1 }} to {{ Math.min(currentPage * pageSize, totalInvoices) }} of {{ totalInvoices }} invoices
            </div>
            
            <div class="join">
              <button 
                class="join-item btn btn-sm"
                :disabled="currentPage === 1"
                @click="previousPage"
              >
                «
              </button>
              
              <button 
                v-for="page in paginationRange" 
                :key="page"
                class="join-item btn btn-sm"
                :class="{ 'btn-active': page === currentPage }"
                @click="goToPage(page)"
              >
                {{ page }}
              </button>
              
              <button 
                class="join-item btn btn-sm"
                :disabled="currentPage === totalPages"
                @click="nextPage"
              >
                »
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Invoice Modal -->
    <CreateInvoiceModal
      :show="showCreateInvoiceModal"
      @close="closeCreateInvoiceModal"
      @created="handleInvoiceCreated"
      @error="(message) => showToast(message, 'error')"
    />

    <!-- Toast Notification -->
    <div v-if="toast.show" class="toast toast-top toast-end">
      <div :class="['alert', toast.type === 'success' ? 'alert-success' : 'alert-error']">
        <span>{{ toast.message }}</span>
      </div>
    </div>
  </div>
</template>
