# Copyright (c) 2026 Blueway Consulting LLC.
# Licensed under the LGPL-3.0 License. See LICENSE file for details.

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import frappe


@frappe.whitelist()
def convert_iso_to_localized_datetime(iso_datetime_string: str) -> str:
	"""
	Convert an ISO formatted datetime to the server's local timezone and return
	an ISO 8601 string including the timezone offset.

	Behavior:
	- If the input has a timezone offset, it is respected and converted to the server TZ.
	- If the input is naive, it is assumed to be UTC and then converted to the server TZ.

	Args:
	    iso_datetime_string (str): ISO datetime string, e.g., "2025-08-28T06:00:00-00:00".

	Returns:
	    str: ISO 8601 string with offset in the server timezone, e.g., "2025-08-28T00:00:00-06:00".
	"""
	try:
		dt_object = datetime.fromisoformat(iso_datetime_string)
		local_dt = to_local(dt_object, None)
		# Return ISO string with seconds precision and timezone offset
		return local_dt.isoformat(timespec="seconds")
	except ValueError as e:
		frappe.log_error(f"Error converting ISO datetime: {e}", "ISO to Localized Datetime Conversion")
		frappe.throw(f"Invalid ISO datetime format: {iso_datetime_string}")


def to_utc(dt, server_tz, use_end_of_day=False):
	"""
	Convert a datetime to true UTC.

	Behavior:
	- If the input datetime is naive (no tzinfo), it is first interpreted in the
	server's timezone as configured in Frappe's System Settings, then converted to UTC.
	- If the input is timezone-aware, it is directly converted to UTC.
	- If the input is a date object, it is converted to datetime.

	Args:
	    dt (datetime or date): The datetime or date to convert.
	    server_tz (str): The server timezone string.
	    use_end_of_day (bool): If True and dt is a date, use end of day (23:59:59.999999),
	                        otherwise use start of day (00:00:00). Default False.

	Returns:
	    datetime: A timezone-aware datetime in UTC (offset +00:00).

	Notes:
	- The server timezone is resolved on each call using System Settings. If not set,
	falls back to 'UTC'.
	"""
	# Convert date to datetime if needed
	dt = date_to_datetime(dt, use_end_of_day)

	# Resolve server timezone safely each call (avoids module import-time DB access)
	server_tz = ZoneInfo(server_tz or frappe.db.get_single_value("System Settings", "time_zone") or "UTC")
	utc_tz = timezone.utc

	if getattr(dt, "tzinfo", None) is None:
		dt = dt.replace(tzinfo=server_tz)
	return dt.astimezone(utc_tz)


def to_local(dt, server_tz, use_end_of_day=False):
	"""
	Convert a datetime to the server's local timezone.

	Behavior:
	- If the input datetime is naive (no tzinfo), it is treated as UTC first,
	then converted to the server's timezone from Frappe's System Settings.
	- If the input is timezone-aware (UTC or otherwise), it is converted directly
	to the server's timezone.
	- If the input is a date object, it is converted to datetime.

	Args:
	    dt (datetime or date): The datetime or date to convert.
	    server_tz (str): The server timezone string.
	    use_end_of_day (bool): If True and dt is a date, use end of day (23:59:59.999999),
	                        otherwise use start of day (00:00:00). Default False.

	Returns:
	    datetime: A timezone-aware datetime in the server's local timezone.

	Notes:
	- The server timezone is resolved on each call using System Settings. If not set,
	falls back to 'UTC'.
	"""
	# Convert date to datetime if needed
	dt = date_to_datetime(dt, use_end_of_day)

	server_tz = ZoneInfo(server_tz or frappe.db.get_single_value("System Settings", "time_zone") or "UTC")

	if getattr(dt, "tzinfo", None) is None:
		# Treat naive input as UTC before converting
		dt = dt.replace(tzinfo=timezone.utc)
	return dt.astimezone(server_tz)


def get_system_timezone():
	"""
	Get the system timezone from Frappe's System Settings.

	Returns:
	    String: The server's timezone as string.
	"""
	tz = frappe.db.get_single_value("System Settings", "time_zone") or "UTC"
	return tz


def get_user_timezone():
	"""
	Get the user's timezone from their profile settings.

	Returns:
	    ZoneInfo: The user's timezone as a ZoneInfo object.
	"""
	tz = frappe.db.get_value("User", frappe.session.user, "time_zone") or "UTC"
	return ZoneInfo(tz)


def date_to_datetime(dt, use_end_of_day=False):
	"""
	Convert a date object to datetime.
	If already a datetime, returns as is.

	Args:
	    dt (date or datetime): The date or datetime to convert.
	    use_end_of_day (bool): If True, use end of day (23:59:59.999999),
	                        otherwise use start of day (00:00:00). Default False.

	Returns:
	    datetime: A datetime object at the appropriate time if input was a date, otherwise unchanged.
	"""
	from datetime import date, time

	if isinstance(dt, date) and not isinstance(dt, datetime):
		time_value = time.max if use_end_of_day else time.min
		return datetime.combine(dt, time_value)
	return dt
