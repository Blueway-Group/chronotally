// Copyright (c) 2026 Blueway Consulting LLC.
// Licensed under the LGPL-3.0 License. See LICENSE file for details.

// Export the base API instance as both default and named export
import api from './api'
export { api }

// Export generic API functions
export {
  listRecords,
  getRecord,
  createRecord,
  updateRecord,
  deleteRecord,
  getCurrentUserId,
  getEmployeeByUserId,
  getCurrentUserEmployee,
  logout,
  type ListRecordsParams,
  type FrappeListResponse
} from './generic.api'

// Export all timesheet API methods
export {
  getTimesheetStats,
  getTimesheetStatusStats,
  getTimesheetList,
  getNewTimesheetData,
  getTimesheets,
  createTimesheet,
  deleteTimesheet,
  cancelTimesheet,
  amendTimesheet,
  checkActivityBillable,
  getProjectCustomer,
  getTimesheetSettings
} from './timesheets.api'

// Export all invoice API methods
export {
  createInvoiceFromBillableHours,
  getInvoices,
  type CreateInvoiceParams,
  type CreateInvoiceResponse,
  type Invoice
} from './invoices.api'
