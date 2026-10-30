# Copyright (c) 2026 Blueway Consulting LLC.
# Licensed under the LGPL-3.0 License. See LICENSE file for details.

import time
from datetime import datetime, timezone

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, cint, date_diff, flt, get_datetime, getdate, nowdate

from chronotally.chronotally.utility_datetime import (
	convert_iso_to_localized_datetime,
	get_system_timezone,
	to_utc,
)

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("chronotally", allow_site=True)


def to_iso(dt, tm=None):
	if not dt:
		return None
	if tm:
		return f"{dt}T{tm}"
	return dt


def append_local_timezone(datetime_string):
	"""
	Append local timezone to datetime string without changing the time.
	"""
	# Parse the input datetime string
	dt = datetime.fromisoformat(datetime_string)

	# Get local timezone offset
	local_tz = datetime.now().astimezone().tzinfo

	# Apply local timezone to the datetime WITHOUT conversion
	dt_with_tz = dt.replace(tzinfo=local_tz)

	return dt_with_tz.isoformat()


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_timesheets(start_date: str | None = None, end_date: str | None = None):
	user = frappe.session.user

	# Resolve system timezone
	tz = get_system_timezone()

	# Convert incoming ISO dates to localized datetime strings for DB filtering
	localized_start_date = convert_iso_to_localized_datetime(start_date)
	localized_end_date = convert_iso_to_localized_datetime(end_date)

	# Build filters based on provided dates
	filters = {"owner": user}
	if localized_start_date and localized_end_date:
		filters["start_date"] = ["between", [localized_start_date, localized_end_date]]
	elif localized_start_date:
		filters["start_date"] = [">=", localized_start_date]
	elif localized_end_date:
		filters["start_date"] = ["<=", localized_end_date]

	logger.debug(f"\nFiltering timesheets with: {filters}\n")

	timesheets = frappe.get_all(
		"Timesheet", filters=filters, fields=["name", "status", "total_hours", "start_date", "end_date"]
	)
	logger.debug(f"\nFetched {len(timesheets)} timesheets for user {user}\n")
	# For each timesheet, fetch its Timesheet Detail children and build events
	events = []
	for ts in timesheets:
		# Check both "Timesheet Detail" and "time_logs" to be safe
		details = []
		try:
			details = frappe.get_all(
				"Timesheet Detail",
				filters={"parent": ts["name"]},
				fields=["activity_type", "from_time", "to_time", "hours"],
			)
			logger.debug(f"Found {len(details)} Timesheet Detail items")
		except Exception as e:
			logger.warning(f"Error getting Timesheet Detail: {e!s}")
			logger.debug(f"Error getting Timesheet Detail: {e!s}")
			continue

		# If no details found, try time_logs
		if len(details) == 0:
			try:
				time_logs = frappe.get_doc("Timesheet", ts["name"]).time_logs
				logger.debug(f"Found {len(time_logs)} time_logs")

				# Convert time_logs to same format as details
				for log in time_logs:
					details.append(
						{
							"activity_type": log.activity_type,
							"from_time": log.from_time,
							"to_time": log.to_time,
							"hours": log.hours,
						}
					)
			except Exception as e:
				logger.warning(f"Error getting time_logs: {e!s}")
				logger.debug(f"Error getting time_logs: {e!s}")

		# Log for debugging
		logger.debug(f"Timesheet: {ts['name']}, Details count: {len(details)}")

		for d in details:
			# Make sure we have valid date and time components
			if not ts["start_date"]:
				logger.debug(f"Missing start_date for timesheet {ts['name']}")
				continue

			# Ensure proper ISO format for FullCalendar
			try:
				# Format: YYYY-MM-DDThh:mm:ss
				ts_start_date = str(ts["start_date"])
				ts_end_date = str(ts["end_date"])
				# Handle times that might be strings or datetime objects
				from_time = d["from_time"] if d["from_time"] else "00:00:00"
				to_time = d["to_time"] if d["to_time"] else "00:00:00"

				# Convert datetime objects to strings if needed
				if isinstance(from_time, datetime):
					from_time = from_time.strftime("%H:%M:%S")
				if isinstance(to_time, datetime):
					to_time = to_time.strftime("%H:%M:%S")

				# If times are not in HH:MM:SS format, adjust them
				if isinstance(from_time, str) and len(from_time.split(":")) < 3:
					from_time += ":00"
				if isinstance(to_time, str) and len(to_time.split(":")) < 3:
					to_time += ":00"

				# Create datetime objects by combining date and time components
				start_datetime_str = f"{ts_start_date}T{from_time}"
				end_datetime_str = f"{ts_end_date}T{to_time}"

				# Convert to datetime objects and then to UTC using system timezone
				start_dt = get_datetime(start_datetime_str)
				end_dt = get_datetime(end_datetime_str)

				# Convert to UTC using system timezone
				start_dt_utc = to_utc(start_dt, tz)
				end_dt_utc = to_utc(end_dt, tz)

				# Format as ISO strings for FullCalendar
				start = start_dt_utc.isoformat()
				end = end_dt_utc.isoformat()

				# Log the exact formatted times we're sending
				logger.debug(f"Event time range: {start} to {end}")

				event = {
					"id": ts["name"] + ":" + d["activity_type"],
					"title": f"{d['activity_type']} ({d['hours']}h)",
					"start": start,
					"end": end,
					"timesheet": ts["name"],
					"status": ts["status"],
					"allDay": False,  # Explicitly set to false for time grid
				}

				events.append(event)
				logger.debug(f"Created event: {event}")

			except Exception as e:
				logger.debug(f"Error creating event for timesheet {ts['name']}: {e!s}")
				continue

	logger.debug(f"Returning {len(events)} events")
	return events


@frappe.whitelist(allow_guest=False, methods=["POST"])
def cancel_timesheet(name: str | None = None):
	"""Cancel a submitted timesheet"""
	if not name:
		frappe.throw(_("Timesheet name is required"))
	doc = frappe.get_doc("Timesheet", name)
	if doc.owner != frappe.session.user:
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if doc.status != "Submitted":
		frappe.throw(_("Only submitted timesheets can be cancelled"))

	doc.cancel()
	return True


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_timesheet_stats(start_date: str | None = None, end_date: str | None = None):
	"""Calculate timesheet statistics for the given date range"""
	user = frappe.session.user

	if not start_date or not end_date:
		frappe.throw(_("Both start_date and end_date are required"))

	localized_start_date = convert_iso_to_localized_datetime(start_date) if start_date else None
	localized_end_date = convert_iso_to_localized_datetime(end_date) if end_date else None
	# Build filters based on provided dates
	filters = {"owner": user, "start_date": ["between", [localized_start_date, localized_end_date]]}

	logger.debug(f"Calculating stats with filters: {filters}")

	# Fetch timesheets in the date range
	timesheets = frappe.get_all(
		"Timesheet", filters=filters, fields=["name", "total_hours", "start_date", "end_date"]
	)

	total_hours = 0
	time_logs = []

	# Calculate total hours from timesheet records
	for ts in timesheets:
		doc = frappe.get_doc("Timesheet", ts["name"])
		if hasattr(doc, "time_logs") and doc.time_logs:
			for log in doc.time_logs:
				time_logs.append(log)

		if ts.get("total_hours"):
			total_hours += ts["total_hours"]
		else:
			# If total_hours is not available, calculate from time_logs
			try:
				if log.hours:
					total_hours += log.hours
			except Exception as e:
				logger.warning(f"Error getting time_logs for {ts['name']}: {e!s}")
				continue

	result = {
		"total_hours": total_hours,
		"timesheet_count": len(timesheets),
		"start_date": start_date,
		"end_date": end_date,
		"time_logs": time_logs,
	}

	logger.debug(f"Stats result: {result}")
	return result


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_timesheet_status_stats():
	"""Get status statistics for timesheets (draft, submitted, approved, etc.)"""
	user = frappe.session.user

	# Get all timesheets for the user
	timesheets = frappe.get_all("Timesheet", filters={"owner": user}, fields=["status"])

	# Count by status
	stats = {"draft": 0, "submitted": 0, "billed": 0, "cancelled": 0}

	for ts in timesheets:
		status = ts.get("status", "").lower()
		if status in stats:
			stats[status] += 1

	logger.debug(f"Status stats: {stats}")
	return stats


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_timesheet_list(
	start_date: str | None = None,
	end_date: str | None = None,
	status_filter: str | None = None,
	limit: str | None = None,
	start: str | None = None,
	employee: str | None = None,
	project: str | None = None,
):
	"""Get timesheet list with filtering and pagination"""

	# Convert string parameters to integers independently so a bad/missing
	# value for one does not reset the other to its default.
	try:
		limit = int(limit)
	except (ValueError, TypeError):
		limit = 20

	try:
		start = int(start)
	except (ValueError, TypeError):
		start = 0

	# Build filters
	filters = {}

	localized_start_date = convert_iso_to_localized_datetime(start_date) if start_date else None
	localized_end_date = convert_iso_to_localized_datetime(end_date) if end_date else None

	if localized_start_date and localized_end_date:
		filters["start_date"] = ["between", [localized_start_date, localized_end_date]]
	elif localized_start_date:
		filters["start_date"] = [">=", localized_start_date]
	elif localized_end_date:
		filters["start_date"] = ["<=", localized_end_date]

	if status_filter and status_filter.lower() != "all":
		# Handle multiple status values separated by comma
		if "," in status_filter:
			status_list = [s.strip() for s in status_filter.split(",") if s.strip()]
			if status_list:
				filters["status"] = ["in", status_list]
		else:
			# Single status filter (backward compatibility)
			filters["status"] = status_filter

	# Add employee filter
	if employee:
		filters["employee"] = employee

	# Add project filter
	if project:
		filters["parent_project"] = project

	logger.debug(f"Fetching timesheet list with filters: {filters}")

	fields = [
		"name",
		"status",
		"start_date",
		"end_date",
		"total_hours",
		"company",
		"customer",
		"parent_project",
		"creation",
		"modified",
		"employee_name",
		"employee",
	]

	active_workflow = False
	meta = frappe.get_meta("Timesheet")
	if meta.has_field("workflow_state"):
		fields.append("workflow_state")
		active_workflow = True

	# Get timesheets with pagination
	timesheets = frappe.get_all(
		"Timesheet",
		filters=filters,
		fields=fields,
		order_by="creation desc",
		start=start,
		page_length=limit,
	)

	# Get total count for pagination
	total_count = frappe.db.count("Timesheet", filters)

	# Format timesheet data for frontend
	formatted_timesheets = []
	for ts in timesheets:
		# Calculate hours from time_logs if total_hours is not available
		hours_worked = ts.get("total_hours", 0)
		time_logs = []
		try:
			doc = frappe.get_doc("Timesheet", ts["name"])
			if hasattr(doc, "time_logs") and doc.time_logs:
				time_logs = [log.as_dict() for log in doc.time_logs]
		except Exception as e:
			logger.warning(f"Error calculating hours for {ts['name']}: {e!s}")

		tz = get_system_timezone()
		# Use use_end_of_day parameter: False for start_date (00:00:00), True for end_date (23:59:59)
		utc_start_date = to_utc(ts["start_date"], tz, use_end_of_day=False) if ts.get("start_date") else None
		utc_end_date = to_utc(ts["end_date"], tz, use_end_of_day=True) if ts.get("end_date") else None

		# Fetch project name if parent_project exists
		project_name = ""
		if ts.get("parent_project"):
			try:
				project_name = frappe.db.get_value("Project", ts["parent_project"], "project_name") or ""
			except Exception as e:
				logger.warning(f"Error fetching project name for {ts['parent_project']}: {e!s}")

		formatted_ts = {
			"id": ts["name"],
			"name": ts["name"],
			"status": ts["status"],
			"workflow_state": ts.get("workflow_state", "") if active_workflow else "",
			"start_date": str(utc_start_date) if utc_start_date else None,
			"end_date": str(utc_end_date) if utc_end_date else None,
			"total_hours": hours_worked,
			"company": ts.get("company", ""),
			"parent_project": ts.get("parent_project", ""),
			"project_name": project_name,
			"customer": ts.get("customer", ""),
			"created_at": ts["creation"].isoformat() if ts["creation"] else None,
			"modified_at": ts["modified"].isoformat() if ts["modified"] else None,
			"time_logs": time_logs,
			"employee_name": ts.get("employee_name", ""),
			"employee": ts.get("employee", ""),
		}
		formatted_timesheets.append(formatted_ts)

	result = {
		"timesheets": formatted_timesheets,
		"total_count": total_count,
		"has_more": (start + limit) < total_count,
	}

	logger.debug(f"Returning {len(formatted_timesheets)} timesheets out of {total_count} total")
	return result


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_timesheet_details(timesheet: str | None = None):
	"""Get detailed information for a specific timesheet"""
	user = frappe.session.user

	# Fetch the timesheet document
	try:
		doc = frappe.get_doc("Timesheet", timesheet)

		# Check permissions - only allow users to see their own timesheets
		if doc.owner != user and not frappe.has_permission("Timesheet", "read", doc):
			frappe.throw(_("You don't have permission to access this timesheet"), frappe.PermissionError)

		# Get basic timesheet info
		result = {
			"name": doc.name,
			"status": doc.status,
			"company": doc.company,
			"customer": doc.customer,
			"parent_project": doc.parent_project,
			"start_date": doc.start_date,
			"end_date": doc.end_date,
			"total_hours": doc.total_hours,
			"time_logs": [],
		}

		# Try to get project and client information
		if hasattr(doc, "project") and doc.project:
			result["project"] = doc.project

			# Try to get client from project
			try:
				project_doc = frappe.get_doc("Project", doc.project)
				if hasattr(project_doc, "customer") and project_doc.customer:
					result["client"] = project_doc.customer
			except Exception as e:
				logger.warning(f"Error fetching project details: {e!s}")

		# Get time log details
		if hasattr(doc, "time_logs") and doc.time_logs:
			for log in doc.time_logs:
				time_log = {
					"activity_type": log.activity_type,
					"from_time": log.from_time,
					"to_time": log.to_time,
					"hours": log.hours,
					"description": log.description if hasattr(log, "description") else "",
				}
				result["time_logs"].append(time_log)

		return result
	except Exception as e:
		logger.error(f"Error fetching timesheet details: {e!s}")
		frappe.throw(_("Error fetching timesheet details: {0}").format(f"{e!s}"))


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_new_timesheet_data():
	current_user = frappe.session.user

	# Get employee information (ID, display name, and company)
	employee_data = frappe.db.get_value(
		"Employee", {"user_id": current_user}, ["name", "employee_name", "company"], as_dict=True
	)

	employee_id = None
	employee_name = None
	default_company = None

	if employee_data:
		employee_id = employee_data.get("name")  # This is the Employee ID
		employee_name = employee_data.get("employee_name")  # This is the display name
		default_company = employee_data.get("company")  # Company from Employee document

	# If no company from employee, get the first company as fallback
	if not default_company:
		first_company = frappe.db.get_value("Company", filters={}, fieldname="name")
		default_company = first_company

	return {
		"employee_id": employee_id,  # Employee document ID (e.g., "HR-EMP-00001")
		"employee_name": employee_name or "Guest User",  # Employee display name
		"default_company": default_company,  # Company from Employee document
	}


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_chronotally_settings():
	# Get settings related to timesheets
	settings = frappe.get_doc("ChronoTally Settings")

	return {"default_period": settings.default_period}


@frappe.whitelist(allow_guest=False, methods=["POST"])
def create_invoice_from_billable_hours(
	employee: str | None = None,
	start_date: str | None = None,
	end_date: str | None = None,
	customer: str | None = None,
	project: str | None = None,
	item: str | None = None,
):
	"""
	Create a Sales Invoice with the sum of billable hours for a given employee,
	date range, customer, and project.

	Args:
		employee: Employee ID
		start_date: Start date in ISO format
		end_date: End date in ISO format
		customer: Customer ID
		project: Project ID
		item: Item code for the invoice line item

	Returns:
		dict: Created Sales Invoice document details
	"""

	# Validate required parameters
	if not all([employee, start_date, end_date, customer, project, item]):
		frappe.throw(
			_(
				"Missing required parameters: employee, start_date, end_date, customer, project, and item are required"
			)
		)

	# Convert ISO dates to localized datetime strings for DB filtering
	localized_start_date = convert_iso_to_localized_datetime(start_date)
	localized_end_date = convert_iso_to_localized_datetime(end_date)

	# Build filters for timesheets
	filters = {
		"employee": employee,
		"parent_project": project,
		"customer": customer,
		"docstatus": 1,  # Only submitted timesheets
		"start_date": ["between", [localized_start_date, localized_end_date]],
	}

	logger.debug(f"Fetching timesheets with filters: {filters}")

	# Fetch timesheets matching the criteria
	timesheets = frappe.get_all("Timesheet", filters=filters, fields=["name", "total_hours", "company"])

	if not timesheets:
		frappe.throw(_("No submitted timesheets found for the given criteria"))

	# Calculate total billable hours and get rate from first time_log
	total_billable_hours = 0
	company = None
	timesheet_names = []
	rate = None
	timesheet_details = []  # Store all time_logs for the invoice

	for ts in timesheets:
		timesheet_names.append(ts["name"])
		if not company:
			company = ts.get("company")

		# Fetch timesheet details to check for billable hours
		try:
			doc = frappe.get_doc("Timesheet", ts["name"])
			if hasattr(doc, "time_logs") and doc.time_logs:
				for log in doc.time_logs:
					# Get rate from first time_log's billing_rate
					if rate is None and hasattr(log, "billing_rate") and log.billing_rate:
						rate = log.billing_rate

					# Check if the log is billable (default to True if field doesn't exist)
					is_billable = log.get("is_billable", 1)
					if is_billable and log.hours:
						total_billable_hours += log.hours

						# Get project name if available
						project_name = ""
						if log.get("project"):
							try:
								project_name = (
									frappe.db.get_value("Project", log.project, "project_name") or ""
								)
							except Exception:
								project_name = log.project

						# Add time_log details for invoice timesheets child table
						timesheet_details.append(
							{
								"time_sheet": ts["name"],
								"timesheet_detail": log.name,  # Critical: Link to specific time log entry
								"activity_type": log.get("activity_type", ""),
								"description": log.get("description", ""),
								"from_time": log.get("from_time"),
								"to_time": log.get("to_time"),
								"billing_hours": log.hours,
								"billing_amount": log.hours
								* (
									log.billing_rate
									if hasattr(log, "billing_rate") and log.billing_rate
									else rate
								),
								"project_name": project_name,
							}
						)
		except Exception as e:
			logger.error(f"Error processing timesheet {ts['name']}: {e!s}")
			continue

	if total_billable_hours <= 0:
		frappe.throw(_("No billable hours found in the selected timesheets"))

	# Get company from employee if not found in timesheets
	if not company:
		company = frappe.db.get_value("Employee", employee, "company")

	if not company:
		frappe.throw(_("Could not determine company for the invoice"))

	# Validate that rate was found
	if not rate:
		frappe.throw(_("Could not determine billing rate from timesheet time_logs"))

	# Convert rate to float
	try:
		rate = float(rate)
	except (ValueError, TypeError):
		frappe.throw(_("Invalid rate value from timesheet"))

	# Use the provided item code
	item_code = item

	# Check if the item exists, if not provide a helpful error
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_(f"Item '{item_code}' does not exist. Please select a valid item."))

	# Create Sales Invoice
	try:
		invoice = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"customer": customer,
				"tax_id": frappe.db.get_value("Customer", customer, "tax_id"),
				"company": company,
				"posting_date": nowdate(),
				"due_date": nowdate(),
				"project": project,
				"currency": "USD",
				"items": [
					{
						"item_code": item_code,
						"qty": total_billable_hours,
						"rate": rate,
						"description": f"IT Consulting Services - {total_billable_hours} billable hours\nPeriod: {start_date} to {end_date}\nEmployee: {frappe.db.get_value('Employee', employee, 'employee_name')}\nTimesheets: {', '.join(timesheet_names)}",
					}
				],
				"timesheets": timesheet_details,  # Add all time_logs to timesheets child table
			}
		)

		invoice.insert()
		frappe.db.commit()

		logger.info(
			f"Created Sales Invoice {invoice.name} for {total_billable_hours} billable hours with {len(timesheet_details)} time log entries"
		)

		return {
			"success": True,
			"invoice_name": invoice.name,
			"total_billable_hours": total_billable_hours,
			"rate": rate,
			"total_amount": total_billable_hours * rate,
			"timesheets": timesheet_names,
			"time_log_count": len(timesheet_details),
			"message": _(
				"Sales Invoice {0} created successfully with {1} billable hours from {2} time log entries"
			).format(invoice.name, total_billable_hours, len(timesheet_details)),
		}

	except Exception as e:
		logger.error(f"Error creating Sales Invoice: {e!s}")
		frappe.throw(_("Error creating Sales Invoice: {0}").format(f"{e!s}"))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

REPORT_MANAGER_ROLES = ("System Manager", "Projects Manager", "Accounts Manager")

# Max number of series in the hours chart; remaining groups are merged into "Other"
REPORT_CHART_MAX_SERIES = 8

# Project / customer resolved from the time log first, then the timesheet header
_REPORT_PROJECT_SQL = "COALESCE(NULLIF(td.project, ''), NULLIF(ts.parent_project, ''))"
_REPORT_CUSTOMER_SQL = "COALESCE(NULLIF(ts.customer, ''), NULLIF(p.customer, ''))"
_REPORT_DATE_SQL = "DATE(COALESCE(td.from_time, ts.start_date))"

_REPORT_FROM_SQL = f"""
	FROM `tabTimesheet Detail` td
	INNER JOIN `tabTimesheet` ts ON ts.name = td.parent AND td.parenttype = 'Timesheet'
	LEFT JOIN `tabProject` p ON p.name = {_REPORT_PROJECT_SQL}
	LEFT JOIN `tabCustomer` c ON c.name = {_REPORT_CUSTOMER_SQL}
"""

# Time logs not yet linked to a submitted or draft Sales Invoice
_REPORT_UNBILLED_SQL = """
	ts.docstatus = 1
	AND td.is_billable = 1
	AND COALESCE(td.sales_invoice, '') = ''
	AND NOT EXISTS (
		SELECT 1 FROM `tabSales Invoice Timesheet` sit
		INNER JOIN `tabSales Invoice` si ON si.name = sit.parent
		WHERE sit.timesheet_detail = td.name AND si.docstatus < 2
	)
"""

_REPORT_GROUP_BY_SQL = {
	"project": f"COALESCE(p.project_name, {_REPORT_PROJECT_SQL}, 'No project')",
	"customer": f"COALESCE(c.customer_name, {_REPORT_CUSTOMER_SQL}, 'No customer')",
	"employee": "COALESCE(NULLIF(ts.employee_name, ''), ts.employee, 'No employee')",
	"activity": "COALESCE(NULLIF(td.activity_type, ''), 'No activity')",
	"billable": "CASE WHEN td.is_billable = 1 THEN 'Billable' ELSE 'Non-billable' END",
}

_REPORT_MEASURE_SQL = {
	"hours": "SUM(td.hours)",
	"amount": "SUM(CASE WHEN td.is_billable = 1 THEN td.billing_amount ELSE 0 END)",
	"cost": "SUM(td.costing_amount)",
}


def _check_reports_access():
	"""Reports expose company-wide financials; restrict them to manager roles."""
	frappe.only_for(REPORT_MANAGER_ROLES)


def _parse_report_dates(start_date, end_date):
	if not start_date or not end_date:
		frappe.throw(_("Both start_date and end_date are required"))
	start, end = getdate(start_date), getdate(end_date)
	if start > end:
		frappe.throw(_("start_date must be before end_date"))
	return start, end


def _build_report_conditions(
	start_date, end_date, customer=None, project=None, employee=None, include_drafts=None
):
	"""Build the WHERE clause shared by all report endpoints (the page's global filters)."""
	conditions = [f"{_REPORT_DATE_SQL} BETWEEN %(start_date)s AND %(end_date)s"]
	params = {"start_date": start_date, "end_date": end_date}

	# Submitted + Billed by default (docstatus 1); drafts optional; cancelled never
	if cint(include_drafts):
		conditions.append("ts.docstatus IN (0, 1)")
	else:
		conditions.append("ts.docstatus = 1")

	if customer:
		conditions.append(f"{_REPORT_CUSTOMER_SQL} = %(customer)s")
		params["customer"] = customer
	if project:
		conditions.append(f"{_REPORT_PROJECT_SQL} = %(project)s")
		params["project"] = project
	if employee:
		conditions.append("ts.employee = %(employee)s")
		params["employee"] = employee

	return " AND ".join(conditions), params


def _get_report_totals(conditions, params):
	row = frappe.db.sql(
		f"""
		SELECT
			COALESCE(SUM(td.hours), 0) AS total_hours,
			COALESCE(SUM(CASE WHEN td.is_billable = 1 THEN td.hours ELSE 0 END), 0) AS billable_hours,
			COALESCE(SUM(CASE WHEN td.is_billable = 1 THEN td.billing_amount ELSE 0 END), 0) AS revenue,
			COALESCE(SUM(td.costing_amount), 0) AS cost
		{_REPORT_FROM_SQL}
		WHERE {conditions}
		""",
		params,
		as_dict=True,
	)[0]

	total_hours = flt(row.total_hours)
	billable_hours = flt(row.billable_hours)
	revenue = flt(row.revenue)
	cost = flt(row.cost)

	return {
		"total_hours": total_hours,
		"billable_hours": billable_hours,
		"utilization": (billable_hours / total_hours * 100) if total_hours else 0,
		"revenue": revenue,
		"cost": cost,
		"margin": ((revenue - cost) / revenue * 100) if revenue else 0,
	}


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_report_summary(
	start_date: str | None = None,
	end_date: str | None = None,
	customer: str | None = None,
	project: str | None = None,
	employee: str | None = None,
	include_drafts: str | None = None,
):
	"""KPIs for the reports page: hours, utilization, unbilled amount and margin,
	plus the same-length prior period for comparison."""
	_check_reports_access()
	start, end = _parse_report_dates(start_date, end_date)
	filters = {
		"customer": customer,
		"project": project,
		"employee": employee,
		"include_drafts": include_drafts,
	}

	conditions, params = _build_report_conditions(start, end, **filters)
	current = _get_report_totals(conditions, params)

	prior_end = add_days(start, -1)
	prior_start = add_days(prior_end, -date_diff(end, start))
	prior_conditions, prior_params = _build_report_conditions(prior_start, prior_end, **filters)
	prior = _get_report_totals(prior_conditions, prior_params)

	unbilled = frappe.db.sql(
		f"""
		SELECT
			COALESCE(SUM(td.hours), 0) AS hours,
			COALESCE(SUM(td.billing_amount), 0) AS amount,
			COUNT(DISTINCT {_REPORT_CUSTOMER_SQL}) AS customers
		{_REPORT_FROM_SQL}
		WHERE {conditions} AND {_REPORT_UNBILLED_SQL}
		""",
		params,
		as_dict=True,
	)[0]

	return {
		**current,
		"prior": {**prior, "start_date": str(prior_start), "end_date": str(prior_end)},
		"unbilled_hours": flt(unbilled.hours),
		"unbilled_amount": flt(unbilled.amount),
		"unbilled_customers": unbilled.customers or 0,
	}


def _report_bucket(day, period):
	"""Start date of the week (Monday) or month containing `day`."""
	if period == "monthly":
		return day.replace(day=1)
	return add_days(day, -day.weekday())


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_report_hours_chart(
	start_date: str | None = None,
	end_date: str | None = None,
	customer: str | None = None,
	project: str | None = None,
	employee: str | None = None,
	include_drafts: str | None = None,
	group_by: str | None = "project",
	measure: str | None = "hours",
	period: str | None = "weekly",
):
	"""Time series for the hours chart, one series per group."""
	_check_reports_access()
	start, end = _parse_report_dates(start_date, end_date)

	if group_by not in _REPORT_GROUP_BY_SQL:
		frappe.throw(_("Invalid group_by: {0}").format(group_by))
	if measure not in _REPORT_MEASURE_SQL:
		frappe.throw(_("Invalid measure: {0}").format(measure))
	if period not in ("weekly", "monthly"):
		frappe.throw(_("Invalid period: {0}").format(period))

	conditions, params = _build_report_conditions(
		start, end, customer=customer, project=project, employee=employee, include_drafts=include_drafts
	)

	rows = frappe.db.sql(
		f"""
		SELECT
			{_REPORT_DATE_SQL} AS day,
			{_REPORT_GROUP_BY_SQL[group_by]} AS label,
			COALESCE({_REPORT_MEASURE_SQL[measure]}, 0) AS value
		{_REPORT_FROM_SQL}
		WHERE {conditions}
		GROUP BY day, label
		""",
		params,
		as_dict=True,
	)

	# Every bucket in the range, so empty weeks/months still show on the axis
	buckets = []
	bucket = _report_bucket(start, period)
	while bucket <= end:
		buckets.append(bucket)
		bucket = add_days(bucket, 7) if period == "weekly" else getdate(add_months(bucket, 1))
	bucket_index = {b: i for i, b in enumerate(buckets)}

	values_by_label = {}
	for row in rows:
		values = values_by_label.setdefault(row.label, [0.0] * len(buckets))
		values[bucket_index[_report_bucket(getdate(row.day), period)]] += flt(row.value)

	# Largest groups first; collapse the tail into "Other"
	ranked = sorted(values_by_label.items(), key=lambda item: sum(item[1]), reverse=True)
	if len(ranked) > REPORT_CHART_MAX_SERIES:
		head = ranked[: REPORT_CHART_MAX_SERIES - 1]
		tail = [values for _label, values in ranked[REPORT_CHART_MAX_SERIES - 1 :]]
		other = [sum(column) for column in zip(*tail, strict=True)]
		ranked = [*head, ("Other", other)]

	return {
		"buckets": [str(b) for b in buckets],
		"series": [{"label": label, "values": [round(v, 2) for v in values]} for label, values in ranked],
		"group_by": group_by,
		"measure": measure,
		"period": period,
	}


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_unbilled_by_customer(
	start_date: str | None = None,
	end_date: str | None = None,
	customer: str | None = None,
	project: str | None = None,
	employee: str | None = None,
	include_drafts: str | None = None,
):
	"""Submitted billable hours not yet on a Sales Invoice, grouped by customer."""
	_check_reports_access()
	start, end = _parse_report_dates(start_date, end_date)
	conditions, params = _build_report_conditions(
		start, end, customer=customer, project=project, employee=employee, include_drafts=include_drafts
	)

	rows = frappe.db.sql(
		f"""
		SELECT
			{_REPORT_CUSTOMER_SQL} AS customer,
			COALESCE(MAX(c.customer_name), {_REPORT_CUSTOMER_SQL}) AS customer_name,
			COALESCE(SUM(td.hours), 0) AS hours,
			COALESCE(SUM(td.billing_amount), 0) AS amount
		{_REPORT_FROM_SQL}
		WHERE {conditions} AND {_REPORT_UNBILLED_SQL}
		GROUP BY customer
		ORDER BY amount DESC
		""",
		params,
		as_dict=True,
	)

	return [
		{
			"customer": row.customer,
			"customer_name": row.customer_name or _("No customer"),
			"hours": flt(row.hours),
			"amount": flt(row.amount),
		}
		for row in rows
	]


# "Budget at Risk Amount" options in ChronoTally Settings -> Project fields; the first is the default
BUDGET_AMOUNT_FIELDS = {
	"Total Costing Amount": "total_costing_amount",
	"Total Billable Amount": "total_billable_amount",
	"Total Billed Amount": "total_billed_amount",
}


def _get_budget_amount_setting():
	"""Return (label, Project fieldname) of the amount compared against each project's budget."""
	label = frappe.db.get_single_value("ChronoTally Settings", "budget_amount_field")
	if label not in BUDGET_AMOUNT_FIELDS:
		label = next(iter(BUDGET_AMOUNT_FIELDS))
	return label, BUDGET_AMOUNT_FIELDS[label]


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_budget_at_risk(customer: str | None = None, project: str | None = None):
	"""Open projects with a submitted Budget, comparing a project amount to it.

	`used_pct` = Project amount (chosen in ChronoTally Settings) / sum of submitted
	Budget.budget_amount for the project. Budgets are project-lifetime figures, so the
	page's date, employee and status filters don't apply.
	"""
	_check_reports_access()
	amount_label, amount_field = _get_budget_amount_setting()

	conditions = ["b.docstatus = 1", "b.budget_against = 'Project'", "p.status = 'Open'"]
	params = {}
	if customer:
		conditions.append("p.customer = %(customer)s")
		params["customer"] = customer
	if project:
		conditions.append("p.name = %(project)s")
		params["project"] = project

	# amount_field comes from the BUDGET_AMOUNT_FIELDS whitelist
	rows = frappe.db.sql(
		f"""
		SELECT
			p.name AS project,
			COALESCE(NULLIF(p.project_name, ''), p.name) AS project_name,
			p.customer,
			COALESCE(c.customer_name, p.customer) AS customer_name,
			COALESCE(p.{amount_field}, 0) AS amount,
			COALESCE(SUM(b.budget_amount), 0) AS budget
		FROM `tabBudget` b
		INNER JOIN `tabProject` p ON p.name = b.project
		LEFT JOIN `tabCustomer` c ON c.name = p.customer
		WHERE {" AND ".join(conditions)}
		GROUP BY p.name
		HAVING budget > 0
		""",
		params,
		as_dict=True,
	)

	result = [
		{
			"project": row.project,
			"project_name": row.project_name,
			"customer": row.customer,
			"customer_name": row.customer_name or _("No customer"),
			"amount": flt(row.amount),
			"budget": flt(row.budget),
			"used_pct": flt(row.amount) / flt(row.budget) * 100,
		}
		for row in rows
	]
	# Worst first
	result.sort(key=lambda row: row["used_pct"], reverse=True)
	return {"amount_label": _(amount_label), "rows": result}
