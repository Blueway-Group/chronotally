# Copyright (c) 2025, Blueway Consulting LLC and Contributors
# See license.txt

from datetime import date, datetime, time, timezone
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from chronotally.chronotally.utility_datetime import (
	convert_iso_to_localized_datetime,
	date_to_datetime,
	get_system_timezone,
	get_user_timezone,
	to_local,
	to_utc,
)

MOCK_TZ = "America/Chicago"  # UTC-6 standard / UTC-5 DST


class TestDateToDatetime(FrappeTestCase):
	"""Tests for date_to_datetime helper."""

	def test_date_returns_start_of_day(self):
		d = date(2025, 6, 15)
		result = date_to_datetime(d)
		self.assertIsInstance(result, datetime)
		self.assertEqual(result, datetime(2025, 6, 15, 0, 0, 0))

	def test_date_returns_end_of_day(self):
		d = date(2025, 6, 15)
		result = date_to_datetime(d, use_end_of_day=True)
		self.assertEqual(result.hour, 23)
		self.assertEqual(result.minute, 59)
		self.assertEqual(result.second, 59)

	def test_datetime_passthrough(self):
		dt = datetime(2025, 6, 15, 10, 30, 0)
		result = date_to_datetime(dt)
		self.assertIs(result, dt)

	def test_datetime_passthrough_ignores_end_of_day(self):
		dt = datetime(2025, 6, 15, 10, 30, 0)
		result = date_to_datetime(dt, use_end_of_day=True)
		self.assertIs(result, dt)


class TestToUtc(FrappeTestCase):
	"""Tests for to_utc conversion."""

	def test_naive_datetime_treated_as_server_tz(self):
		"""Naive datetime should be interpreted in server TZ then converted to UTC."""
		dt = datetime(2025, 6, 15, 12, 0, 0)  # noon
		result = to_utc(dt, MOCK_TZ)
		self.assertEqual(result.tzinfo, timezone.utc)
		# Chicago CDT is UTC-5 in June, so noon CDT = 17:00 UTC
		self.assertEqual(result.hour, 17)

	def test_aware_datetime_converted_to_utc(self):
		"""Aware datetime should be directly converted to UTC."""
		from zoneinfo import ZoneInfo

		eastern = ZoneInfo("America/New_York")
		dt = datetime(2025, 6, 15, 12, 0, 0, tzinfo=eastern)
		result = to_utc(dt, MOCK_TZ)
		self.assertEqual(result.tzinfo, timezone.utc)
		# EDT is UTC-4, so noon EDT = 16:00 UTC
		self.assertEqual(result.hour, 16)

	def test_utc_datetime_stays_utc(self):
		dt = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
		result = to_utc(dt, MOCK_TZ)
		self.assertEqual(result.hour, 12)

	def test_date_input_converts_to_start_of_day(self):
		d = date(2025, 6, 15)
		result = to_utc(d, MOCK_TZ)
		self.assertIsInstance(result, datetime)
		# Midnight CDT (UTC-5) = 05:00 UTC
		self.assertEqual(result.hour, 5)
		self.assertEqual(result.minute, 0)

	def test_date_input_with_end_of_day(self):
		d = date(2025, 6, 15)
		result = to_utc(d, MOCK_TZ, use_end_of_day=True)
		# 23:59:59 CDT (UTC-5) = 04:59:59 UTC next day
		self.assertEqual(result.hour, 4)
		self.assertEqual(result.minute, 59)

	@patch("chronotally.chronotally.utility_datetime.frappe")
	def test_none_server_tz_falls_back_to_db(self, mock_frappe):
		"""When server_tz is None, should read from System Settings."""
		mock_frappe.db.get_single_value.return_value = "America/Chicago"
		dt = datetime(2025, 6, 15, 12, 0, 0)
		result = to_utc(dt, None)
		mock_frappe.db.get_single_value.assert_called_with("System Settings", "time_zone")
		self.assertEqual(result.tzinfo, timezone.utc)


class TestToLocal(FrappeTestCase):
	"""Tests for to_local conversion."""

	def test_naive_datetime_treated_as_utc(self):
		"""Naive datetime should be treated as UTC then converted to server TZ."""
		dt = datetime(2025, 6, 15, 17, 0, 0)  # 5pm UTC
		result = to_local(dt, MOCK_TZ)
		# UTC-5 (CDT in June): 17:00 UTC = 12:00 CDT
		self.assertEqual(result.hour, 12)

	def test_aware_utc_datetime(self):
		dt = datetime(2025, 6, 15, 17, 0, 0, tzinfo=timezone.utc)
		result = to_local(dt, MOCK_TZ)
		self.assertEqual(result.hour, 12)

	def test_date_input(self):
		d = date(2025, 6, 15)
		result = to_local(d, MOCK_TZ)
		self.assertIsInstance(result, datetime)

	@patch("chronotally.chronotally.utility_datetime.frappe")
	def test_none_server_tz_falls_back_to_db(self, mock_frappe):
		mock_frappe.db.get_single_value.return_value = "UTC"
		dt = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
		result = to_local(dt, None)
		mock_frappe.db.get_single_value.assert_called_with("System Settings", "time_zone")
		self.assertEqual(result.hour, 12)


class TestGetSystemTimezone(FrappeTestCase):
	"""Tests for get_system_timezone."""

	def test_returns_configured_timezone(self):
		tz = get_system_timezone()
		self.assertIsInstance(tz, str)
		self.assertTrue(len(tz) > 0)

	@patch("chronotally.chronotally.utility_datetime.frappe")
	def test_falls_back_to_utc(self, mock_frappe):
		mock_frappe.db.get_single_value.return_value = None
		result = get_system_timezone()
		self.assertEqual(result, "UTC")


class TestGetUserTimezone(FrappeTestCase):
	"""Tests for get_user_timezone."""

	@patch("chronotally.chronotally.utility_datetime.frappe")
	def test_returns_user_timezone(self, mock_frappe):
		from zoneinfo import ZoneInfo

		mock_frappe.session.user = "test@example.com"
		mock_frappe.db.get_value.return_value = "America/New_York"
		result = get_user_timezone()
		self.assertEqual(result, ZoneInfo("America/New_York"))

	@patch("chronotally.chronotally.utility_datetime.frappe")
	def test_falls_back_to_utc(self, mock_frappe):
		from zoneinfo import ZoneInfo

		mock_frappe.session.user = "test@example.com"
		mock_frappe.db.get_value.return_value = None
		result = get_user_timezone()
		self.assertEqual(result, ZoneInfo("UTC"))


class TestConvertIsoToLocalizedDatetime(FrappeTestCase):
	"""Tests for convert_iso_to_localized_datetime."""

	def test_utc_iso_string_converted_to_local(self):
		"""UTC datetime should be converted to server timezone."""
		result = convert_iso_to_localized_datetime("2025-06-15T17:00:00+00:00")
		self.assertIsInstance(result, str)
		# Result should contain a timezone offset (+ or -)
		has_offset = "+" in result[10:] or "-" in result[10:]
		self.assertTrue(has_offset, f"Expected timezone offset in result: {result}")

	def test_naive_iso_string_treated_as_utc(self):
		"""Naive ISO string should be treated as UTC."""
		result = convert_iso_to_localized_datetime("2025-06-15T12:00:00")
		self.assertIsInstance(result, str)

	def test_offset_iso_string_respected(self):
		"""An offset-aware ISO string should have its timezone respected."""
		result = convert_iso_to_localized_datetime("2025-06-15T12:00:00-05:00")
		self.assertIsInstance(result, str)

	def test_invalid_format_throws(self):
		"""Invalid ISO format should throw an error."""
		with self.assertRaises(Exception):
			convert_iso_to_localized_datetime("not-a-date")
