# Copyright (c) 2025, Enerlinq and Contributors
# See license.txt

from unittest.mock import MagicMock, patch, PropertyMock

import frappe
from frappe.tests.utils import FrappeTestCase
from werkzeug.wrappers import Response

from chronotally.chronotally.cors import add_cors_headers, handle_cors


class TestHandleCors(FrappeTestCase):
	"""Tests for handle_cors (OPTIONS preflight handler)."""

	@patch("chronotally.chronotally.cors.frappe")
	def test_options_request_returns_response(self, mock_frappe):
		"""OPTIONS request should return a 200 response."""
		mock_frappe.request = MagicMock()
		mock_frappe.request.method = "OPTIONS"
		mock_frappe.local = MagicMock()
		mock_frappe.get_request_header.return_value = "http://localhost:4321"
		mock_frappe.conf.get.return_value = False
		mock_frappe._dict = frappe._dict

		result = handle_cors()
		self.assertIsNotNone(result)
		self.assertEqual(result.status_code, 200)

	@patch("chronotally.chronotally.cors.frappe")
	def test_non_options_request_returns_none(self, mock_frappe):
		"""Non-OPTIONS requests should return None (no preflight handling)."""
		mock_frappe.request = MagicMock()
		mock_frappe.request.method = "GET"

		result = handle_cors()
		self.assertIsNone(result)

	@patch("chronotally.chronotally.cors.frappe")
	def test_no_request_returns_none(self, mock_frappe):
		"""When there is no request, should return None."""
		mock_frappe.request = None
		result = handle_cors()
		self.assertIsNone(result)


class TestAddCorsHeaders(FrappeTestCase):
	"""Tests for add_cors_headers."""

	@patch("chronotally.chronotally.cors.frappe")
	def test_adds_all_expected_headers(self, mock_frappe):
		"""Should add all required CORS headers."""
		mock_frappe.get_request_header.return_value = "http://localhost:4321"
		mock_frappe.conf.get.return_value = False
		mock_frappe._dict = frappe._dict

		response = Response()
		add_cors_headers(response)

		# Verify all CORS headers are present
		self.assertIn("Access-Control-Allow-Origin", response.headers)
		self.assertIn("Access-Control-Allow-Methods", response.headers)
		self.assertIn("Access-Control-Allow-Headers", response.headers)
		self.assertIn("Access-Control-Allow-Credentials", response.headers)
		self.assertIn("Access-Control-Max-Age", response.headers)

	@patch("chronotally.chronotally.cors.frappe")
	def test_allowed_origin_set_correctly(self, mock_frappe):
		"""Allowed origin from the list should be set as-is."""
		mock_frappe.get_request_header.return_value = "http://localhost:4321"
		mock_frappe.conf.get.return_value = False
		mock_frappe._dict = frappe._dict

		response = Response()
		add_cors_headers(response)
		self.assertEqual(
			response.headers.get("Access-Control-Allow-Origin"),
			"http://localhost:4321",
		)

	@patch("chronotally.chronotally.cors.frappe")
	def test_developer_mode_allows_any_origin(self, mock_frappe):
		"""In developer mode, any origin should be allowed."""
		mock_frappe.get_request_header.return_value = "http://custom-dev:9999"
		mock_frappe.conf.get.return_value = True  # developer_mode = True
		mock_frappe._dict = frappe._dict

		response = Response()
		add_cors_headers(response)
		self.assertEqual(
			response.headers.get("Access-Control-Allow-Origin"),
			"http://custom-dev:9999",
		)

	@patch("chronotally.chronotally.cors.frappe")
	def test_unknown_origin_in_production_gets_wildcard(self, mock_frappe):
		"""Unknown origin in non-developer mode should get wildcard."""
		mock_frappe.get_request_header.return_value = "http://evil.example.com"
		mock_frappe.conf.get.return_value = False
		mock_frappe._dict = frappe._dict

		response = Response()
		add_cors_headers(response)
		self.assertEqual(
			response.headers.get("Access-Control-Allow-Origin"),
			"*",
		)

	def test_none_response_does_not_raise(self):
		"""Passing None should not raise an error."""
		add_cors_headers(None)  # Should not throw

	@patch("chronotally.chronotally.cors.frappe")
	def test_credentials_header_is_true(self, mock_frappe):
		mock_frappe.get_request_header.return_value = "http://localhost:4321"
		mock_frappe.conf.get.return_value = False
		mock_frappe._dict = frappe._dict

		response = Response()
		add_cors_headers(response)
		self.assertEqual(
			response.headers.get("Access-Control-Allow-Credentials"),
			"true",
		)

	@patch("chronotally.chronotally.cors.frappe")
	def test_max_age_is_24_hours(self, mock_frappe):
		mock_frappe.get_request_header.return_value = "http://localhost:4321"
		mock_frappe.conf.get.return_value = False
		mock_frappe._dict = frappe._dict

		response = Response()
		add_cors_headers(response)
		self.assertEqual(
			response.headers.get("Access-Control-Max-Age"),
			"86400",
		)
