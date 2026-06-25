// Copyright (c) 2026 Blueway Consulting LLC.
// Licensed under the LGPL-3.0 License. See LICENSE file for details.

import api from './api'

/**
 * Generic interface for list records parameters
 */
export interface ListRecordsParams {
  docType: string
  fields?: string[]
  filters?: any[][]
  orFilters?: any[][]
  limit?: number
  orderBy?: string
  searchTerm?: string
  searchFields?: string[]
}

/**
 * Generic interface for Frappe response
 */
export interface FrappeListResponse<T = any> {
  data?: T[]
  message?: T[]
}

/**
 * Generic function to list records from any Frappe DocType
 * Supports both filtered queries and search functionality
 *
 * @param params - ListRecordsParams object
 * @returns Promise<T[]> - Array of records
 *
 * @example
 * // Simple list with fields
 * const employees = await listRecords({
 *   docType: 'Employee',
 *   fields: ['name', 'employee_name'],
 *   limit: 20
 * })
 *
 * @example
 * // Search across multiple fields
 * const projects = await listRecords({
 *   docType: 'Project',
 *   fields: ['name', 'project_name', 'status'],
 *   searchTerm: 'website',
 *   searchFields: ['project_name', 'description'],
 *   limit: 10
 * })
 *
 * @example
 * // With specific filters
 * const activeProjects = await listRecords({
 *   docType: 'Project',
 *   fields: ['name', 'project_name'],
 *   filters: [['status', '=', 'Active']],
 *   orderBy: 'project_name asc'
 * })
 */
export const listRecords = async <T = any>(
  params: ListRecordsParams
): Promise<T[]> => {
  const {
    docType,
    fields = ['name'],
    filters,
    orFilters,
    limit = 20,
    orderBy,
    searchTerm,
    searchFields
  } = params

  try {
    // Build query parameters
    const queryParams: Record<string, any> = {
      fields: JSON.stringify(fields),
      limit_page_length: limit
    }

    // Add filters if provided
    if (filters && filters.length > 0) {
      queryParams.filters = JSON.stringify(filters)
    }

    // Add OR filters if provided
    if (orFilters && orFilters.length > 0) {
      queryParams.or_filters = JSON.stringify(orFilters)
    }

    // If search term and search fields are provided, build OR filters for search
    if (searchTerm && searchFields && searchFields.length > 0) {
      const searchFilters = searchFields.map(field => [
        field,
        'like',
        `%${searchTerm}%`
      ])
      queryParams.or_filters = JSON.stringify(searchFilters)
    }

    // Add order by if provided
    if (orderBy) {
      queryParams.order_by = orderBy
    }

    // Make API request
    const response = await api.get<FrappeListResponse<T>>(
      `/api/resource/${docType}`,
      { params: queryParams }
    )

    // Handle different response structures from Frappe
    if (response.data) {
      // Direct data array in response.data
      if (Array.isArray(response.data)) {
        return response.data
      }
      // Data wrapped in data property
      if (response.data.data && Array.isArray(response.data.data)) {
        return response.data.data
      }
      // Data wrapped in message property
      if (response.data.message && Array.isArray(response.data.message)) {
        return response.data.message
      }
    }

    return []
  } catch (error) {
    console.error(`Error fetching ${docType} records:`, error)
    throw error
  }
}

/**
 * Generic function to get a single record by name
 *
 * @param docType - The Frappe DocType name
 * @param name - The document name/ID
 * @param fields - Optional array of fields to fetch
 * @returns Promise<T> - Single record
 *
 * @example
 * const employee = await getRecord('Employee', 'HR-EMP-00001', ['name', 'employee_name', 'company'])
 */
export const getRecord = async <T = any>(
  docType: string,
  name: string,
  fields?: string[]
): Promise<T | null> => {
  try {
    const url = `/api/resource/${docType}/${name}`
    const params = fields ? { fields: JSON.stringify(fields) } : {}

    const response = await api.get<{ data: T }>(url, { params })

    if (response.data && response.data.data) {
      return response.data.data
    }

    return null
  } catch (error) {
    console.error(`Error fetching ${docType} record ${name}:`, error)
    throw error
  }
}

/**
 * Generic function to create a new record
 *
 * @param docType - The Frappe DocType name
 * @param data - The document data
 * @returns Promise<T> - Created record
 *
 * @example
 * const newProject = await createRecord('Project', {
 *   project_name: 'New Website',
 *   status: 'Open'
 * })
 */
export const createRecord = async <T = any>(
  docType: string,
  data: Partial<T>
): Promise<T> => {
  try {
    const response = await api.post<{ data: T }>(`/api/resource/${docType}`, {
      ...data,
      doctype: docType
    })

    if (response.data && response.data.data) {
      return response.data.data
    }

    throw new Error('Invalid response from server')
  } catch (error) {
    console.error(`Error creating ${docType} record:`, error)
    throw error
  }
}

/**
 * Generic function to update a record
 *
 * @param docType - The Frappe DocType name
 * @param name - The document name/ID
 * @param data - The fields to update
 * @returns Promise<T> - Updated record
 *
 * @example
 * const updated = await updateRecord('Project', 'PROJ-001', {
 *   status: 'Completed'
 * })
 */
export const updateRecord = async <T = any>(
  docType: string,
  name: string,
  data: Partial<T>
): Promise<T> => {
  try {
    const response = await api.put<{ data: T }>(
      `/api/resource/${docType}/${name}`,
      data
    )

    if (response.data && response.data.data) {
      return response.data.data
    }

    throw new Error('Invalid response from server')
  } catch (error) {
    console.error(`Error updating ${docType} record ${name}:`, error)
    // console.error(`Error updating ${docType} record ${name}:`, error)
    throw error
  }
}

/**
 * Generic function to delete a record
 *
 * @param docType - The Frappe DocType name
 * @param name - The document name/ID
 * @returns Promise<void>
 *
 * @example
 * await deleteRecord('Project', 'PROJ-001')
 */
export const deleteRecord = async (
  docType: string,
  name: string
): Promise<void> => {
  try {
    await api.delete(`/api/resource/${docType}/${name}`)
  } catch (error) {
    console.error(`Error deleting ${docType} record ${name}:`, error)
    throw error
  }
}

/**
 * Get current user ID from document cookies
 * Frappe stores user_id in cookies
 *
 * @returns string | null - User ID or null if not found
 */
export const getCurrentUserId = (): string | null => {
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'user_id') {
      return decodeURIComponent(value)
    }
  }
  return null
}

/**
 * Get employee record by user_id
 * Returns the first employee associated with the given user
 *
 * @param userId - The user ID to search for
 * @returns Promise<T | null> - Employee record or null if not found
 *
 * @example
 * const employee = await getEmployeeByUserId('user@example.com')
 */
export const getEmployeeByUserId = async <T = any>(
  userId: string
): Promise<T | null> => {
  try {
    const employees = await listRecords<T>({
      docType: 'Employee',
      fields: ['name', 'employee_name', 'user_id', 'company'],
      filters: [['user_id', '=', userId]],
      limit: 1
    })

    return employees.length > 0 ? employees[0] : null
  } catch (error) {
    console.error(`Error fetching employee for user ${userId}:`, error)
    throw error
  }
}

/**
 * Get current user's employee record
 * Retrieves the user_id from cookies and fetches the associated employee
 *
 * @returns Promise<T | null> - Employee record or null if not found
 *
 * @example
 * const currentEmployee = await getCurrentUserEmployee()
 * if (currentEmployee) {
 *   console.log('Employee:', currentEmployee.name)
 * }
 */
export const getCurrentUserEmployee = async <T = any>(): Promise<T | null> => {
  try {
    const userId = getCurrentUserId()

    if (!userId) {
      console.warn('No user_id found in cookies')
      return null
    }

    return await getEmployeeByUserId<T>(userId)
  } catch (error) {
    console.error('Error fetching current user employee:', error)
    throw error
  }
}

/**
 * Logout response interface
 */
interface LogoutResponse {
  message?: string
  home_page?: string
  full_name?: string
}

/**
 * Logout the current user
 * Calls the Frappe logout API and redirects to home_page if user becomes Guest
 *
 * @returns Promise<void>
 *
 * @example
 * await logout()
 */
export const logout = async (): Promise<void> => {
  try {
    const response = await api.get<LogoutResponse>('/api/method/logout')

    if (response.data) {
      const { full_name, home_page } = response.data

      // If user is now Guest and home_page is provided, redirect
      if (full_name === 'Guest' && home_page) {
        window.location.href = home_page
      }
    }
  } catch (error) {
    console.error('Error during logout:', error)
    throw error
  }
}

/**
 * Workflow transition interface
 */
export interface WorkflowTransition {
  name: string
  owner: string
  creation: string
  modified: string
  modified_by: string
  docstatus: number
  idx: number
  state: string
  action: string
  next_state: string
  allowed: string
  allow_self_approval: number
  send_email_to_creator: number
  condition?: string
  workflow_builder_id: string
  parent: string
  parentfield: string
  parenttype: string
  doctype: string
}

/**
 * Workflow transitions response interface
 */
interface WorkflowTransitionsResponse {
  message?: WorkflowTransition[]
  transitions?: WorkflowTransition[]
}

/**
 * Get available workflow transitions for a document
 * Calls frappe.model.workflow.get_transitions
 *
 * @param doc - Document object with at least a 'name' property
 * @returns Promise<WorkflowTransition[]> - Array of available transitions
 *
 * @example
 * const transitions = await getWorkflowTransitions({ name: 'TS-2025-00031' })
 * console.log('Available actions:', transitions.map(t => t.action))
 */
export const getWorkflowTransitions = async (
  doc: { name: string; [key: string]: any }
): Promise<WorkflowTransition[]> => {
  try {
    const response = await api.post<WorkflowTransitionsResponse>(
      '/api/method/frappe.model.workflow.get_transitions',
      { doc }
    )

    if (response.data) {
      // Handle different response structures
      if (response.data.message && Array.isArray(response.data.message)) {
        return response.data.message
      }
      if (response.data.transitions && Array.isArray(response.data.transitions)) {
        return response.data.transitions
      }
    }

    return []
  } catch (error) {
    console.error('Error fetching workflow transitions:', error)
    throw error
  }
}

/**
 * Apply workflow response interface
 */
interface ApplyWorkflowResponse<T = any> {
  message?: T
}

/**
 * Apply a workflow action to a document
 * Calls frappe.model.workflow.apply_workflow
 *
 * @param doc - Document object to apply the workflow action on
 * @param action - The workflow action to apply (e.g., "Submit for Approval")
 * @returns Promise<T> - Updated document after workflow action
 *
 * @example
 * const updatedTimesheet = await applyWorkflow(
 *   { name: 'TS-2025-00031', doctype: 'Timesheet' },
 *   'Submit for Approval'
 * )
 * console.log('New workflow state:', updatedTimesheet.workflow_state)
 */
export const applyWorkflow = async <T = any>(
  doc: { name: string; [key: string]: any },
  action: string
): Promise<T> => {
  try {
    const response = await api.post<ApplyWorkflowResponse<T>>(
      '/api/method/frappe.model.workflow.apply_workflow',
      { doc, action }
    )

    if (response.data && response.data.message) {
      return response.data.message
    }

    throw new Error('Invalid response from server')
  } catch (error) {
    console.error('Error applying workflow action:', error)
    throw error
  }
}
