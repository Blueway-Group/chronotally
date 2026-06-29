<!--
Copyright (c) 2026 Blueway Consulting LLC.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, onMounted, computed } from 'vue'
import { createInvoiceFromBillableHours, getInvoices } from '@/utils/client/api/invoices.api'
import { getNewTimesheetData } from '@/utils/client/api'
import { getFormattedISODate } from '@/utils/client/dates'
import ComboBox from '../ComboBox.vue'

// State
const showCreateInvoiceModal = ref(false)
const invoices = ref([])
const loading = ref(false)
const loadingInvoices = ref(false)
const newTimesheetData = ref(null)

// Pagination state
const currentPage = ref(1)
const pageSize = ref(10)
const totalInvoices = ref(0)

// Form state
const invoiceForm = ref({
  employee: '',
  start_date: '',
  end_date: '',
  customer: '',
  project: '',
  item: ''
})

// Toast state
const toast = ref({
  show: false,
  message: '',
  type: 'success'
})

// Load initial data
onMounted(async () => {
  await loadNewTimesheetData()
  await loadInvoices()
})

const loadNewTimesheetData = async () => {
  try {
    const response = await getNewTimesheetData()
    newTimesheetData.value = response

    // Auto-populate employee with current user's employee ID
    if (response.employee_id) {
      invoiceForm.value.employee = response.employee_id
    }
  } catch (error) {
    console.error('Error loading employee data:', error)
  }
}

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

const handleEmployeeSelect = (employee) => {
  invoiceForm.value.employee = employee.name
}

const handleCustomerSelect = (customer) => {
  invoiceForm.value.customer = customer.name
}

const handleProjectSelect = (project) => {
  invoiceForm.value.project = project.name
  if (project.customer) {
    invoiceForm.value.customer = project.customer
  }
}

const handleItemSelect = (item) => {
  invoiceForm.value.item = item.name
}

const openCreateInvoiceModal = () => {
  // Reset form
  invoiceForm.value = {
    employee: newTimesheetData.value?.employee_id || '',
    start_date: '',
    end_date: '',
    customer: '',
    project: '',
    item: ''
  }
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

const createInvoice = async () => {
  try {
    loading.value = true

    // Validate form
    if (!invoiceForm.value.employee || !invoiceForm.value.start_date ||
        !invoiceForm.value.end_date || !invoiceForm.value.customer ||
        !invoiceForm.value.project || !invoiceForm.value.item) {
      showToast('Please fill in all required fields', 'error')
      return
    }

    // Convert dates to ISO format with proper time boundaries
    const startDate = new Date(invoiceForm.value.start_date)
    const endDate = new Date(invoiceForm.value.end_date)

    // Set start date to beginning of day (00:00:00.000)
    startDate.setHours(0, 0, 0, 0)
    // Set end date to end of day (23:59:59.999)
    endDate.setHours(23, 59, 59, 999)

    const params = {
      employee: invoiceForm.value.employee,
      start_date: getFormattedISODate(startDate),
      end_date: getFormattedISODate(endDate),
      customer: invoiceForm.value.customer,
      project: invoiceForm.value.project,
      item: invoiceForm.value.item
    }

    const response = await createInvoiceFromBillableHours(params)

    showToast(response.message, 'success')
    closeCreateInvoiceModal()

    // Reload invoices
    await loadInvoices()
  } catch (error) {
    console.error('Error creating invoice:', error)
    const errorMessage = error.response?.data?.message || error.message || 'Failed to create invoice'
    showToast(errorMessage, 'error')
  } finally {
    loading.value = false
  }
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
        <h1 class="text-3xl font-bold">Reports & Invoices</h1>
        <p class="text-base-content/70 mt-1">Manage invoices and view reports</p>
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
    <dialog :class="{ 'modal-open': showCreateInvoiceModal }" class="modal">
      <div class="modal-box w-11/12 max-w-2xl">
        <h3 class="font-bold text-lg mb-4">Create Invoice from Billable Hours</h3>

        <form @submit.prevent="createInvoice" class="space-y-4">
          <fieldset class="fieldset bg-base-200 border-base-300 rounded-box border p-4">
            <legend class="fieldset-legend">Invoice Details</legend>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Employee -->
              <div>
                <label class="label" for="employee">
                  <span class="label-text">Employee <span class="text-error">*</span></span>
                </label>
                <ComboBox
                  name="employee"
                  docType="Employee"
                  v-model="invoiceForm.employee"
                  :displayFields="['employee_name', 'name']"
                  placeholder="Search employee by name or ID..."
                  @select="handleEmployeeSelect"
                />
                <p class="label text-xs text-base-content/60">Search and select employee</p>
              </div>

              <!-- Customer -->
              <div>
                <label class="label" for="customer">
                  <span class="label-text">Customer <span class="text-error">*</span></span>
                </label>
                <ComboBox
                  name="customer"
                  docType="Customer"
                  v-model="invoiceForm.customer"
                  :displayFields="['customer_name', 'name']"
                  placeholder="Search customer..."
                  @select="handleCustomerSelect"
                />
                <p class="label text-xs text-base-content/60">Search and select customer</p>
              </div>

              <!-- Start Date -->
              <div>
                <label class="label" for="start_date">
                  <span class="label-text">Start Date <span class="text-error">*</span></span>
                </label>
                <input
                  id="start_date"
                  v-model="invoiceForm.start_date"
                  type="date"
                  class="input input-bordered w-full"
                  required
                />
              </div>

              <!-- End Date -->
              <div>
                <label class="label" for="end_date">
                  <span class="label-text">End Date <span class="text-error">*</span></span>
                </label>
                <input
                  id="end_date"
                  v-model="invoiceForm.end_date"
                  type="date"
                  class="input input-bordered w-full"
                  required
                />
              </div>
            </div>

            <!-- Project -->
            <div class="mt-4">
              <label class="label" for="project">
                <span class="label-text">Project <span class="text-error">*</span></span>
              </label>
              <ComboBox
                name="project"
                docType="Project"
                v-model="invoiceForm.project"
                :displayFields="['project_name', 'name', 'customer']"
                placeholder="Search project..."
                @select="handleProjectSelect"
                :minSearchLength="0"
                :filters="[['is_active', '=', 'Yes']]"
              />
              <p class="label text-xs text-base-content/60">Search and select project</p>
            </div>

            <!-- Item -->
            <div class="mt-4">
              <label class="label" for="item">
                <span class="label-text">Item <span class="text-error">*</span></span>
              </label>
              <ComboBox
                name="item"
                docType="Item"
                v-model="invoiceForm.item"
                :displayFields="['item_name', 'name', 'item_code']"
                placeholder="Search item..."
                @select="handleItemSelect"
                :minSearchLength="0"
              />
              <p class="label text-xs text-base-content/60">Search and select item for invoice</p>
            </div>
          </fieldset>

          <!-- Modal Actions -->
          <div class="modal-action">
            <button type="button" class="btn" @click="closeCreateInvoiceModal">Cancel</button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="loading"
            >
              <span v-if="loading" class="loading loading-spinner loading-sm"></span>
              Create Invoice
            </button>
          </div>
        </form>
      </div>
      <form method="dialog" class="modal-backdrop" @click="closeCreateInvoiceModal">
        <button>close</button>
      </form>
    </dialog>

    <!-- Toast Notification -->
    <div v-if="toast.show" class="toast toast-top toast-end">
      <div :class="['alert', toast.type === 'success' ? 'alert-success' : 'alert-error']">
        <span>{{ toast.message }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fieldset {
  position: relative;
}

.fieldset-legend {
  position: absolute;
  top: -0.75rem;
  left: 1rem;
  padding: 0 0.5rem;
  background: inherit;
  font-weight: 600;
  font-size: 0.875rem;
}
</style>
