# Copyright (c) 2026 Blueway Consulting LLC.
# Licensed under the LGPL-3.0 License. See LICENSE file for details.

import frappe


def execute():
	"""Sync the chronotally Desktop Icon from add_to_apps_screen hooks.

	Frappe copies `add_to_apps_screen` (logo + route) into a `Desktop Icon`
	record only when the icon does not already exist. Changes to hooks.py are
	therefore not reflected for an already-installed app. This patch re-syncs
	the record from the current hooks.
	"""
	app_details = frappe.get_hooks("add_to_apps_screen", app_name="chronotally")
	if not app_details:
		return

	details = app_details[0]

	if not frappe.db.exists("Desktop Icon", {"app": "chronotally"}):
		return

	frappe.db.set_value(
		"Desktop Icon",
		{"app": "chronotally"},
		{
			"link": details.get("route"),
			"logo_url": details.get("logo"),
		},
	)
