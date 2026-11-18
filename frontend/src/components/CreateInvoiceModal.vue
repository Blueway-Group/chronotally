<!--
Copyright (c) 2026 Blueway Consulting LLC.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { ref, watch, onMounted } from 'vue'
import { createInvoiceFromBillableHours } from '@/utils/client/api/invoices.api'
import { getNewTimesheetData } from '@/utils/client/api'
import { getFormattedISODate } from '@/utils/client/dates'
import ComboBox from './ComboBox.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  // Initial values applied each time the modal opens:
  // { customer, start_date, end_date, project, employee, item } (dates as YYYY-MM-DD)
  prefill: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close', 'created', 'error'])

const loading = ref(false)
const newTimesheetData = ref(null)

// Form state
const invoiceForm = ref({
  employee: '',
  start_date: '',
  end_date: '',
  customer: '',
  project: '',
  item: ''
})

onMounted(async () => {
  try {
    newTimesheetData.value = await getNewTimesheetData()

    // Auto-populate employee with current user's employee ID
    if (!invoiceForm.value.employee && newTimesheetData.value?.employee_id) {
      invoiceForm.value.employee = newTimesheetData.value.employee_id
    }
  } catch (error) {
    console.error('Error loading employee data:', error)
  }
})

// Reset the form with the prefill each time the modal opens
watch(() => props.show, (isOpen) => {
  if (!isOpen) return
  invoiceForm.value = {
    employee: newTimesheetData.value?.employee_id || '',
    start_date: '',
    end_date: '',
    customer: '',
    project: '',
    item: '',
    ...Object.fromEntries(Object.entries(props.prefill).filter(([, value]) => value))
  }
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

const close = () => {
  emit('close')
}

const createInvoice = async () => {
  try {
    loading.value = true

    // Validate form
    if (!invoiceForm.value.employee || !invoiceForm.value.start_date ||
        !invoiceForm.value.end_date || !invoiceForm.value.customer ||
        !invoiceForm.value.project || !invoiceForm.value.item) {
      emit('error', 'Please fill in all required fields')
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

    emit('created', response)
    close()
  } catch (error) {
    console.error('Error creating invoice:', error)
    const errorMessage = error.response?.data?.message || error.message || 'Failed to create invoice'
    emit('error', errorMessage)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <dialog :class="{ 'modal-open': show }" class="modal">
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
          <button type="button" class="btn" @click="close">Cancel</button>
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
    <form method="dialog" class="modal-backdrop" @click="close">
      <button>close</button>
    </form>
  </dialog>
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
