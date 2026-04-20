# Copyright (c) 2025, Enerlinq and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from chronotally.chronotally.csrf_token import extend_context, get_user_info


class TestGetUserInfo(FrappeTestCase):
	"""Tests for get_user_info helper."""

	def test_guest_returns_empty_dict(self):
		frappe.set_user("Guest")
		result = get_user_info()
		self.assertEqual(result, {})

	def test_authenticated_user_returns_info(self):
		frappe.set_user("Administrator")
		result = get_user_info()
		self.assertIn("name", result)
		self.assertIn("full_name", result)
		self.assertIn("user_image", result)
		self.assertIn("initials", result)
		self.assertEqual(result["name"], "Administrator")

	def test_full_name_populated(self):
		frappe.set_user("Administrator")
		result = get_user_info()
		self.assertIsNotNone(result["full_name"])
		self.assertTrue(len(result["full_name"]) > 0)


class TestExtendContext(FrappeTestCase):
	"""Tests for extend_context (website context extension)."""

	def _make_context(self):
		return frappe._dict()

	@patch("chronotally.chronotally.csrf_token.frappe")
	def test_guest_redirects_to_login(self, mock_frappe):
		"""Guest users on /chronotally should be redirected to login."""
		mock_frappe.session.user = "Guest"
		mock_frappe.request = MagicMock()
		mock_frappe.request.path = "/chronotally"
		mock_frappe.local = MagicMock()
		mock_frappe.Redirect = frappe.Redirect

		context = self._make_context()
		with self.assertRaises(frappe.Redirect):
			extend_context(context)

	@patch("chronotally.chronotally.csrf_token.frappe")
	def test_authenticated_user_gets_csrf_token(self, mock_frappe):
		"""Authenticated users should get a CSRF token in context."""
		mock_frappe.session.user = "Administrator"
		mock_frappe.request = MagicMock()
		mock_frappe.request.path = "/chronotally"
		mock_frappe.local = MagicMock()
		mock_frappe.sessions.get_csrf_token.return_value = "test-token-123"
		mock_frappe.local.site = "testsite"
		mock_frappe.has_permission.return_value = True
		mock_frappe.get_value.return_value = "Administrator"
		mock_frappe.db = MagicMock()
		mock_frappe.Redirect = frappe.Redirect

		from frappe.utils import get_abbr

		context = self._make_context()
		result = extend_context(context)
		self.assertEqual(result.csrf_token, "test-token-123")

	@patch("chronotally.chronotally.csrf_token.frappe")
	def test_non_chronotally_path_skipped(self, mock_frappe):
		"""Paths not under /chronotally should pass through unchanged."""
		mock_frappe.request = MagicMock()
		mock_frappe.request.path = "/other-page"
		mock_frappe.session.user = "Administrator"

		context = self._make_context()
		result = extend_context(context)
		self.assertNotIn("csrf_token", result)

	@patch("chronotally.chronotally.csrf_token.frappe")
	def test_reports_without_permission_redirects(self, mock_frappe):
		"""User without Sales Invoice permission should be redirected from /chronotally/reports."""
		mock_frappe.session.user = "test@example.com"
		mock_frappe.request = MagicMock()
		mock_frappe.request.path = "/chronotally/reports"
		mock_frappe.local = MagicMock()
		mock_frappe.has_permission.return_value = False
		mock_frappe.Redirect = frappe.Redirect

		context = self._make_context()
		with self.assertRaises(frappe.Redirect):
			extend_context(context)

	@patch("chronotally.chronotally.csrf_token.frappe")
	def test_context_has_no_cache(self, mock_frappe):
		"""Context should have no_cache set to 1."""
		mock_frappe.session.user = "Administrator"
		mock_frappe.request = MagicMock()
		mock_frappe.request.path = "/chronotally"
		mock_frappe.local = MagicMock()
		mock_frappe.sessions.get_csrf_token.return_value = "token"
		mock_frappe.local.site = "testsite"
		mock_frappe.has_permission.return_value = True
		mock_frappe.get_value.return_value = "Admin"
		mock_frappe.db = MagicMock()
		mock_frappe.Redirect = frappe.Redirect

		context = self._make_context()
		result = extend_context(context)
		self.assertEqual(result.no_cache, 1)

	@patch("chronotally.chronotally.csrf_token.frappe")
	def test_context_has_site_name(self, mock_frappe):
		"""Context should contain site_name."""
		mock_frappe.session.user = "Administrator"
		mock_frappe.request = MagicMock()
		mock_frappe.request.path = "/chronotally"
		mock_frappe.local = MagicMock()
		mock_frappe.sessions.get_csrf_token.return_value = "token"
		mock_frappe.local.site = "my-test-site"
		mock_frappe.has_permission.return_value = True
		mock_frappe.get_value.return_value = "Admin"
		mock_frappe.db = MagicMock()
		mock_frappe.Redirect = frappe.Redirect

		context = self._make_context()
		result = extend_context(context)
		self.assertEqual(result.site_name, "my-test-site")

	@patch("chronotally.chronotally.csrf_token.frappe")
	def test_context_has_current_route(self, mock_frappe):
		"""Context should contain the current route."""
		mock_frappe.session.user = "Administrator"
		mock_frappe.request = MagicMock()
		mock_frappe.request.path = "/chronotally/timesheets"
		mock_frappe.local = MagicMock()
		mock_frappe.sessions.get_csrf_token.return_value = "token"
		mock_frappe.local.site = "testsite"
		mock_frappe.has_permission.return_value = True
		mock_frappe.get_value.return_value = "Admin"
		mock_frappe.db = MagicMock()
		mock_frappe.Redirect = frappe.Redirect

		context = self._make_context()
		result = extend_context(context)
		self.assertEqual(result.current_route, "/chronotally/timesheets")

	@patch("chronotally.chronotally.csrf_token.frappe")
	def test_context_has_invoice_permission_flag(self, mock_frappe):
		"""Context should include has_invoice_permission."""
		mock_frappe.session.user = "Administrator"
		mock_frappe.request = MagicMock()
		mock_frappe.request.path = "/chronotally"
		mock_frappe.local = MagicMock()
		mock_frappe.sessions.get_csrf_token.return_value = "token"
		mock_frappe.local.site = "testsite"
		mock_frappe.has_permission.return_value = True
		mock_frappe.get_value.return_value = "Admin"
		mock_frappe.db = MagicMock()
		mock_frappe.Redirect = frappe.Redirect

		context = self._make_context()
		result = extend_context(context)
		self.assertTrue(result.has_invoice_permission)
