// Copyright (c) 2026 Blueway Consulting LLC.
// Licensed under the LGPL-3.0 License. See LICENSE file for details.

import api from './api'

// TypeScript interfaces
interface TimesheetListParams {
    startDate?: string | null;
    endDate?: string | null;
    statusFilter?: string | null;
    limit?: number;
    start?: number;
    employee?: string | null;
    project?: string | null;
}

// Get Timesheet Stats
export const getTimesheetStats = async (startDate: string, endDate: string) => {
    try {
        const response = await api.get('/api/method/chronotally.chronotally.api_timesheet.get_timesheet_stats', {
            params: {
                start_date: startDate,
                end_date: endDate
            }
        });
        return response.data.message;
    } catch (error) {
        console.error('Error fetching timesheet stats:', error);
        throw error;
    }
}

// Get Timesheet Status Stats
export const getTimesheetStatusStats = async () => {
    try {
        const response = await api.get('/api/method/chronotally.chronotally.api_timesheet.get_timesheet_status_stats');
        return response.data.message;
    } catch (error) {
        console.error('Error fetching timesheet status stats:', error);
        throw error;
    }
}

// Get Timesheet List
export const getTimesheetList = async (params: TimesheetListParams = {}) => {
    const {
        startDate = null,
        endDate = null,
        statusFilter = null,
        limit = 20,
        start = 0,
        employee = null,
        project = null
    } = params;

    try {
        const response = await api.get('/api/method/chronotally.chronotally.api_timesheet.get_timesheet_list', {
            params: {
                start_date: startDate,
                end_date: endDate,
                status_filter: statusFilter,
                limit: limit,
                start: start,
                ...(employee ? { employee } : {}),
                ...(project ? { project } : {})
            }
        });
        return response.data.message;
    } catch (error) {
        console.error('Error fetching timesheet list:', error);
        throw error;
    }
}

export const getNewTimesheetData = async () => {
    try {
        const response = await api.get('/api/method/chronotally.chronotally.api_timesheet.get_new_timesheet_data');
        return response.data.message;
    } catch (error) {
        console.error('Error fetching new timesheet data:', error);
        throw error;
    }
}

// Get Timesheet
export const getTimesheets = async (startDate: string | null = null, endDate: string | null = null) => {
    try {
        const response = await api.get('/api/method/chronotally.chronotally.api_timesheet.get_timesheets', {
            params: {
                start_date: startDate,
                end_date: endDate
            }
        });
        return response.data.message;
    } catch (error) {
        console.error('Error fetching timesheets:', error);
        throw error;
    }
}

// Create Timesheet using out-of-the-box Frappe API
export const createTimesheet = async (data: any) => {
    try {
        const response = await api.post('/api/resource/Timesheet', {
            doctype: 'Timesheet',
            employee: data.employee,
            company: data.company,
            parent_project: data.project,
            customer: data.customer || '',
            currency: data.currency,
            time_logs: data.time_logs.map((log: any) => ({
                activity_type: log.activity_type,
                hours: log.hours,
                from_time: log.from_time,
                to_time: log.to_time,
                description: log.description || '',
                project: log.project,
                is_billable: log.is_billable || false
            }))
        });
        return response.data.data;
    } catch (error) {
        console.error('Error creating timesheet:', error);
        throw error;
    }
}

// Delete Timesheet using out-of-the-box Frappe API
export const deleteTimesheet = async (name: string) => {
    try {
        const response = await api.delete(`/api/resource/Timesheet/${name}`);
        return response.data;
    } catch (error) {
        console.error('Error deleting timesheet:', error);
        throw error;
    }
}

// Cancel Timesheet
export const cancelTimesheet = async (name: string) => {
    try {
        const response = await api.post('/api/method/chronotally.chronotally.api_timesheet.cancel_timesheet',
            {
                name
            }
        );
        return response.data.message;
    } catch (error) {
        console.error('Error cancelling timesheet:', error);
        throw error;
    }
}

// Amend Timesheet - Create a new draft from a cancelled timesheet
export const amendTimesheet = async (name: string) => {
    try {
        // Get the cancelled timesheet data
        const response = await api.get(`/api/resource/Timesheet/${name}`);
        const cancelledTimesheet = response.data.data;

        // Create a new timesheet with amended naming convention
        // Remove system fields and set new values
        const newTimesheet = {
            doctype: 'Timesheet',
            employee: cancelledTimesheet.employee,
            company: cancelledTimesheet.company,
            parent_project: cancelledTimesheet.parent_project,
            amended_from: name, // Link to the cancelled document
            time_logs: (cancelledTimesheet.time_logs || []).map((log: any) => ({
                activity_type: log.activity_type,
                hours: log.hours,
                from_time: log.from_time,
                to_time: log.to_time,
                description: log.description || '',
                project: log.project
            }))
        };

        // Create the new amended timesheet
        const createResponse = await api.post('/api/resource/Timesheet', newTimesheet);
        return createResponse.data.data;
    } catch (error) {
        console.error('Error amending timesheet:', error);
        throw error;
    }
}

// Check if an activity type is billable
export const checkActivityBillable = async (activityTypeName: string, employeeName: string) => {
    try {
        // First, get the Activity Type to check for billing_rate
        const activityTypeResponse = await api.get(`/api/resource/Activity Type/${activityTypeName}`, {
            params: {
                fields: JSON.stringify(['name', 'billing_rate'])
            }
        });

        const activityType = activityTypeResponse.data.data;

        // If Activity Type has a billing_rate, it's billable
        if (activityType.billing_rate && activityType.billing_rate > 0) {
            return true;
        }

        // Check if there's an Activity Cost record for this Activity Type and Employee
        const activityCostResponse = await api.get('/api/resource/Activity Cost', {
            params: {
                fields: JSON.stringify(['name', 'billing_rate']),
                filters: JSON.stringify([
                    ['activity_type', '=', activityTypeName],
                    ['employee', '=', employeeName]
                ]),
                limit_page_length: 1
            }
        });

        const activityCosts = activityCostResponse.data.data || activityCostResponse.data.message || [];

        // If there's an Activity Cost record with a billing_rate, it's billable
        if (activityCosts.length > 0 && activityCosts[0].billing_rate && activityCosts[0].billing_rate > 0) {
            return true;
        }

        // Not billable
        return false;
    } catch (error) {
        console.error('Error checking activity billable status:', error);
        // Default to false if there's an error
        return false;
    }
}

// Get Project customer
export const getProjectCustomer = async (projectName: string) => {
    try {
        const response = await api.get(`/api/resource/Project/${projectName}`, {
            params: {
                fields: JSON.stringify(['name', 'customer'])
            }
        });

        const project = response.data.data;
        return project.customer || null;
    } catch (error) {
        console.error('Error fetching project customer:', error);
        return null;
    }
}

// Get Timesheet Settings
export const getTimesheetSettings = async () => {
    try {
        const response = await api.get('/api/method/chronotally.chronotally.api_timesheet.get_chronotally_settings');
        return response.data.message;
    } catch (error) {
        console.error('Error fetching timesheet settings:', error);
        throw error;
    }
}
