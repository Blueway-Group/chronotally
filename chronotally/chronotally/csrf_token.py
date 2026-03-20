import json
import os

import frappe
from frappe.utils import get_abbr

# Disable caching for this page
no_cache = 1

"""Update website context for /chronotally routes"""


def extend_context(context):
	"""
	This function is called by Frappe for all pages under /chronotally
	via the update_website_context hook in hooks.py
	"""

	# Redirect to login if user is not authenticated
	current_path = frappe.request.path

	if current_path.startswith("/chronotally"):
		# Check if user has permission to create Sales Invoices
		# This is the key permission check for accessing the reports/invoicing page
		has_invoice_permission = frappe.has_permission(
			doctype="Sales Invoice", ptype="create", user=frappe.session.user
		)

		if frappe.session.user == "Guest":
			frappe.local.flags.redirect_location = "/login?redirect-to=" + current_path
			raise frappe.Redirect
		if current_path.startswith("/chronotally/reports") and not has_invoice_permission:
			# User doesn't have permission to create invoices, redirect to main page
			frappe.local.flags.redirect_location = "/chronotally"
			raise frappe.Redirect

		# Generate a fresh CSRF token for this request
		# This ensures the token is always current and valid
		csrf_token = frappe.sessions.get_csrf_token()
		frappe.db.commit()

		# Add no-cache directive to context
		context.no_cache = 1

		# Add CSRF token and site info to context
		context.csrf_token = csrf_token
		context.site_name = frappe.local.site

		# Add flattened user info to context
		user_info = get_user_info()
		context.user_name = user_info.get("name", "")
		context.user_full_name = user_info.get("full_name", "")
		context.user_image = user_info.get("user_image", "")
		context.user_initials = user_info.get("initials", "")

		# Pass route information to frontend
		context.current_route = current_path

		# Indicate if user has invoice permission
		context.has_invoice_permission = has_invoice_permission

	return context


"""Get current user information"""


def get_user_info():
	"""Get current user information"""
	if frappe.session.user == "Guest":
		return {}

	full_name = frappe.get_value("User", frappe.session.user, "full_name")

	return {
		"name": frappe.session.user,
		"full_name": full_name,
		"user_image": frappe.get_value("User", frappe.session.user, "user_image"),
		"initials": get_abbr(full_name),
	}
