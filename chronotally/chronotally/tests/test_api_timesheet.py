# Copyright (c) 2025, Enerlinq and Contributors
# See license.txt

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from chronotally.chronotally.api_timesheet import (
	append_local_timezone,
	cancel_timesheet,
	create_invoice_from_billable_hours,
	get_new_timesheet_data,
	get_timesheet_details,
	get_timesheet_list,
	get_timesheet_settings,
	get_timesheet_stats,
	get_timesheet_status_stats,
	get_timesheets,
	to_iso,
)


class TestToIso(FrappeTestCase):
	"""Tests for to_iso helper."""

	def test_date_only(self):
		self.assertEqual(to_iso("2025-06-15"), "2025-06-15")

	def test_date_and_time(self):
		self.assertEqual(to_iso("2025-06-15", "10:30:00"), "2025-06-15T10:30:00")

	def test_none_date(self):
		self.assertIsNone(to_iso(None))

	def test_none_date_with_time(self):
		self.assertIsNone(to_iso(None, "10:30:00"))

	def test_empty_string_date(self):
		self.assertIsNone(to_iso(""))


class TestAppendLocalTimezone(FrappeTestCase):
	"""Tests for append_local_timezone helper."""

	def test_appends_timezone_offset(self):
		result = append_local_timezone("2025-06-15T12:00:00")
		# Should contain a timezone offset (+ or -)
		dt = datetime.fromisoformat(result)
		self.assertIsNotNone(dt.tzinfo)

	def test_preserves_time_value(self):
		result = append_local_timezone("2025-06-15T12:00:00")
		dt = datetime.fromisoformat(result)
		self.assertEqual(dt.hour, 12)
		self.assertEqual(dt.minute, 0)


class TestGetTimesheets(FrappeTestCase):
	"""Tests for get_timesheets API endpoint."""

	def setUp(self):
		super().setUp()
		self.test_user = "test@example.com"
		# Create test user if it doesn't exist
		if not frappe.db.exists("User", self.test_user):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": self.test_user,
					"first_name": "Test",
					"last_name": "User",
					"user_type": "Website User",
				}
			).insert(ignore_permissions=True)

	def test_returns_list(self):
		"""get_timesheets should return a list when given a valid date range."""
		frappe.set_user(self.test_user)
		result = get_timesheets(
			start_date="2025-01-01T00:00:00+00:00",
			end_date="2025-12-31T23:59:59+00:00",
		)
		self.assertIsInstance(result, list)

	def test_filters_by_date_range(self):
		"""get_timesheets should accept date range parameters without error."""
		frappe.set_user(self.test_user)
		result = get_timesheets(
			start_date="2025-06-01T00:00:00+00:00",
			end_date="2025-06-30T23:59:59+00:00",
		)
		self.assertIsInstance(result, list)

	def test_event_structure(self):
		"""Events returned should have the correct keys when timesheets exist."""
		frappe.set_user("Administrator")
		# Create a test timesheet
		ts = _create_test_timesheet()
		try:
			result = get_timesheets(
				start_date="2025-01-01T00:00:00+00:00",
				end_date="2025-12-31T23:59:59+00:00",
			)
			if result:
				event = result[0]
				expected_keys = {"id", "title", "start", "end", "timesheet", "status", "allDay"}
				self.assertTrue(expected_keys.issubset(set(event.keys())))
				self.assertFalse(event["allDay"])
		finally:
			_cleanup_timesheet(ts)


class TestCancelTimesheet(FrappeTestCase):
	"""Tests for cancel_timesheet API endpoint."""

	def test_cancel_non_submitted_throws(self):
		"""Cancelling a draft timesheet should raise an error."""
		frappe.set_user("Administrator")
		ts = _create_test_timesheet()
		try:
			with self.assertRaises(frappe.ValidationError):
				cancel_timesheet(ts.name)
		finally:
			_cleanup_timesheet(ts)

	def test_cancel_wrong_owner_throws(self):
		"""Cancelling another user's timesheet should raise PermissionError."""
		frappe.set_user("Administrator")
		ts = _create_test_timesheet()

		test_user = "other_user@example.com"
		if not frappe.db.exists("User", test_user):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": test_user,
					"first_name": "Other",
					"last_name": "User",
					"user_type": "Website User",
				}
			).insert(ignore_permissions=True)

		try:
			frappe.set_user(test_user)
			with self.assertRaises(frappe.PermissionError):
				cancel_timesheet(ts.name)
		finally:
			frappe.set_user("Administrator")
			_cleanup_timesheet(ts)


class TestGetTimesheetStats(FrappeTestCase):
	"""Tests for get_timesheet_stats API endpoint."""

	def test_missing_dates_throws(self):
		"""Should throw if start_date or end_date is missing."""
		frappe.set_user("Administrator")
		with self.assertRaises(Exception):
			get_timesheet_stats(start_date=None, end_date=None)

	def test_missing_end_date_throws(self):
		frappe.set_user("Administrator")
		with self.assertRaises(Exception):
			get_timesheet_stats(start_date="2025-01-01T00:00:00+00:00", end_date=None)

	def test_returns_stats_structure(self):
		"""Should return dict with expected keys."""
		frappe.set_user("Administrator")
		result = get_timesheet_stats(
			start_date="2025-01-01T00:00:00+00:00",
			end_date="2025-12-31T23:59:59+00:00",
		)
		self.assertIn("total_hours", result)
		self.assertIn("timesheet_count", result)
		self.assertIn("start_date", result)
		self.assertIn("end_date", result)
		self.assertIn("time_logs", result)
		self.assertIsInstance(result["total_hours"], (int, float))
		self.assertIsInstance(result["timesheet_count"], int)


class TestGetTimesheetStatusStats(FrappeTestCase):
	"""Tests for get_timesheet_status_stats API endpoint."""

	def test_returns_status_dict(self):
		frappe.set_user("Administrator")
		result = get_timesheet_status_stats()
		expected_keys = {"draft", "submitted", "billed", "cancelled"}
		self.assertTrue(expected_keys.issubset(set(result.keys())))

	def test_values_are_non_negative(self):
		frappe.set_user("Administrator")
		result = get_timesheet_status_stats()
		for _key, value in result.items():
			self.assertGreaterEqual(value, 0)


class TestGetTimesheetList(FrappeTestCase):
	"""Tests for get_timesheet_list API endpoint."""

	def test_returns_paginated_structure(self):
		frappe.set_user("Administrator")
		result = get_timesheet_list()
		self.assertIn("timesheets", result)
		self.assertIn("total_count", result)
		self.assertIn("has_more", result)
		self.assertIsInstance(result["timesheets"], list)

	def test_respects_limit(self):
		frappe.set_user("Administrator")
		result = get_timesheet_list(limit=5)
		self.assertLessEqual(len(result["timesheets"]), 5)

	def test_status_filter_single(self):
		frappe.set_user("Administrator")
		result = get_timesheet_list(status_filter="Draft")
		# Should not raise and should return valid structure
		self.assertIn("timesheets", result)

	def test_status_filter_multiple(self):
		frappe.set_user("Administrator")
		result = get_timesheet_list(status_filter="Draft,Submitted")
		self.assertIn("timesheets", result)

	def test_status_filter_all(self):
		frappe.set_user("Administrator")
		result = get_timesheet_list(status_filter="all")
		self.assertIn("timesheets", result)

	def test_date_range_filter(self):
		frappe.set_user("Administrator")
		result = get_timesheet_list(
			start_date="2025-01-01T00:00:00+00:00",
			end_date="2025-12-31T23:59:59+00:00",
		)
		self.assertIn("timesheets", result)

	def test_invalid_limit_defaults(self):
		"""Invalid limit/start values should default gracefully."""
		frappe.set_user("Administrator")
		result = get_timesheet_list(limit="abc", start="xyz")
		self.assertIn("timesheets", result)

	def test_formatted_timesheet_structure(self):
		"""Each returned timesheet should have the expected fields."""
		frappe.set_user("Administrator")
		ts = _create_test_timesheet()
		try:
			result = get_timesheet_list()
			if result["timesheets"]:
				item = result["timesheets"][0]
				expected_keys = {
					"id",
					"name",
					"status",
					"start_date",
					"end_date",
					"total_hours",
					"company",
					"time_logs",
				}
				self.assertTrue(expected_keys.issubset(set(item.keys())))
		finally:
			_cleanup_timesheet(ts)


class TestGetTimesheetDetails(FrappeTestCase):
	"""Tests for get_timesheet_details API endpoint."""

	def test_returns_details(self):
		frappe.set_user("Administrator")
		ts = _create_test_timesheet()
		try:
			result = get_timesheet_details(ts.name)
			self.assertEqual(result["name"], ts.name)
			self.assertIn("status", result)
			self.assertIn("time_logs", result)
			self.assertIsInstance(result["time_logs"], list)
		finally:
			_cleanup_timesheet(ts)

	def test_nonexistent_timesheet_throws(self):
		frappe.set_user("Administrator")
		with self.assertRaises(Exception):
			get_timesheet_details("NONEXISTENT-TS-00000")

	def test_permission_check(self):
		"""User without permission should get an error."""
		frappe.set_user("Administrator")
		ts = _create_test_timesheet()

		test_user = "noperm_user@example.com"
		if not frappe.db.exists("User", test_user):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": test_user,
					"first_name": "NoPerm",
					"last_name": "User",
					"user_type": "Website User",
				}
			).insert(ignore_permissions=True)

		try:
			frappe.set_user(test_user)
			# The PermissionError is caught internally and re-raised as ValidationError
			with self.assertRaises(Exception):
				get_timesheet_details(ts.name)
		finally:
			frappe.set_user("Administrator")
			_cleanup_timesheet(ts)


class TestGetNewTimesheetData(FrappeTestCase):
	"""Tests for get_new_timesheet_data API endpoint."""

	def test_returns_expected_keys(self):
		frappe.set_user("Administrator")
		result = get_new_timesheet_data()
		self.assertIn("employee_id", result)
		self.assertIn("employee_name", result)
		self.assertIn("default_company", result)

	def test_guest_gets_default_name(self):
		"""User without employee record should get 'Guest User' as name."""
		test_user = "no_employee@example.com"
		if not frappe.db.exists("User", test_user):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": test_user,
					"first_name": "No",
					"last_name": "Employee",
					"user_type": "Website User",
				}
			).insert(ignore_permissions=True)

		frappe.set_user(test_user)
		result = get_new_timesheet_data()
		self.assertIsNone(result["employee_id"])
		self.assertEqual(result["employee_name"], "Guest User")


class TestGetTimesheetSettings(FrappeTestCase):
	"""Tests for get_timesheet_settings API endpoint."""

	def test_returns_settings(self):
		frappe.set_user("Administrator")
		result = get_timesheet_settings()
		self.assertIn("default_period", result)


class TestCreateInvoiceFromBillableHours(FrappeTestCase):
	"""Tests for create_invoice_from_billable_hours API endpoint."""

	def test_missing_params_throws(self):
		"""Should throw when required parameters are missing."""
		frappe.set_user("Administrator")
		with self.assertRaises(Exception):
			create_invoice_from_billable_hours(
				employee=None,
				start_date=None,
				end_date=None,
				customer=None,
				project=None,
				item=None,
			)

	def test_no_timesheets_found_throws(self):
		"""Should throw when no submitted timesheets match the criteria."""
		frappe.set_user("Administrator")
		with self.assertRaises(Exception):
			create_invoice_from_billable_hours(
				employee="HR-EMP-NONEXISTENT",
				start_date="2025-01-01T00:00:00+00:00",
				end_date="2025-01-02T00:00:00+00:00",
				customer="Test Customer",
				project="Test Project",
				item="Test Item",
			)


# ── Test Helpers ─────────────────────────────────────────────────────────────


def _create_test_timesheet():
	"""Create a minimal test timesheet for use in tests."""
	# Ensure Warehouse Type exists
	if not frappe.db.exists("Warehouse Type", "Transit"):
		frappe.get_doc(
			{
				"doctype": "Warehouse Type",
				"name": "Transit",
			}
		).insert(ignore_permissions=True)

	# Get the first available company
	company = frappe.db.get_value("Company", filters={}, fieldname="name")
	if not company:
		company = (
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": "Test Company CT",
					"default_currency": "USD",
					"country": "United States",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	# Ensure Activity Type exists
	if not frappe.db.exists("Activity Type", "Testing"):
		frappe.get_doc(
			{
				"doctype": "Activity Type",
				"activity_type": "Testing",
			}
		).insert(ignore_permissions=True)

	ts = frappe.get_doc(
		{
			"doctype": "Timesheet",
			"company": company,
			"time_logs": [
				{
					"activity_type": "Testing",
					"from_time": "2025-06-15 09:00:00",
					"to_time": "2025-06-15 17:00:00",
					"hours": 8,
				}
			],
		}
	)
	ts.insert(ignore_permissions=True)
	return ts


def _cleanup_timesheet(ts):
	"""Delete a test timesheet safely."""
	try:
		frappe.set_user("Administrator")
		if ts.docstatus == 1:
			ts.cancel()
		frappe.delete_doc("Timesheet", ts.name, force=True)
	except Exception:
		pass
