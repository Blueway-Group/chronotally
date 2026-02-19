app_name = "enerlinq_timesheets"
app_title = "ChronoTally"
app_publisher = "ChronoTally"
app_description = "time tracking and timesheet management."
app_email = "jonaspm@enerlinq.com"
app_license = "agpl-3.0"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "enerlinq_timesheets",
# 		"logo": "/assets/enerlinq_timesheets/logo.png",
# 		"title": "enerlinq-timesheets",
# 		"route": "/enerlinq_timesheets",
# 		"has_permission": "enerlinq_timesheets.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/enerlinq_timesheets/css/enerlinq_timesheets.css"
# app_include_js = "/assets/enerlinq_timesheets/js/enerlinq_timesheets.js"

# include js, css files in header of web template
# web_include_css = "/assets/enerlinq_timesheets/css/enerlinq_timesheets.css"
# web_include_js = "/assets/enerlinq_timesheets/js/enerlinq_timesheets.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "enerlinq_timesheets/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "enerlinq_timesheets/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "enerlinq_timesheets.utils.jinja_methods",
# 	"filters": "enerlinq_timesheets.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "enerlinq_timesheets.install.before_install"
# after_install = "enerlinq_timesheets.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "enerlinq_timesheets.uninstall.before_uninstall"
# after_uninstall = "enerlinq_timesheets.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "enerlinq_timesheets.utils.before_app_install"
# after_app_install = "enerlinq_timesheets.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "enerlinq_timesheets.utils.before_app_uninstall"
# after_app_uninstall = "enerlinq_timesheets.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "enerlinq_timesheets.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"enerlinq_timesheets.tasks.all"
# 	],
# 	"daily": [
# 		"enerlinq_timesheets.tasks.daily"
# 	],
# 	"hourly": [
# 		"enerlinq_timesheets.tasks.hourly"
# 	],
# 	"weekly": [
# 		"enerlinq_timesheets.tasks.weekly"
# 	],
# 	"monthly": [
# 		"enerlinq_timesheets.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "enerlinq_timesheets.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "enerlinq_timesheets.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "enerlinq_timesheets.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = ["enerlinq_timesheets.enerlinq_timesheets.cors.handle_cors"]
after_request = ["enerlinq_timesheets.enerlinq_timesheets.cors.add_cors_headers"]

# Job Events
# ----------
# before_job = ["enerlinq_timesheets.utils.before_job"]
# after_job = ["enerlinq_timesheets.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"enerlinq_timesheets.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# Add web route for timesheet portal page
web_routes = [
    {
        "from_route": "/timesheet",
        "to_route": "timesheet"
    }
]

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

update_website_context = "enerlinq_timesheets.enerlinq_timesheets.csrf_token.extend_context"
