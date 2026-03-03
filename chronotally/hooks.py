app_name = "chronotally"
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
# 		"name": "chronotally",
# 		"logo": "/assets/chronotally/logo.png",
# 		"title": "enerlinq-timesheets",
# 		"route": "/chronotally",
# 		"has_permission": "chronotally.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/chronotally/css/chronotally.css"
# app_include_js = "/assets/chronotally/js/chronotally.js"

# include js, css files in header of web template
# web_include_css = "/assets/chronotally/css/chronotally.css"
# web_include_js = "/assets/chronotally/js/chronotally.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "chronotally/public/scss/website"

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
# app_include_icons = "chronotally/public/icons.svg"

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
# 	"methods": "chronotally.utils.jinja_methods",
# 	"filters": "chronotally.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "chronotally.install.before_install"
# after_install = "chronotally.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "chronotally.uninstall.before_uninstall"
# after_uninstall = "chronotally.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "chronotally.utils.before_app_install"
# after_app_install = "chronotally.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "chronotally.utils.before_app_uninstall"
# after_app_uninstall = "chronotally.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "chronotally.notifications.get_notification_config"

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
# 		"chronotally.tasks.all"
# 	],
# 	"daily": [
# 		"chronotally.tasks.daily"
# 	],
# 	"hourly": [
# 		"chronotally.tasks.hourly"
# 	],
# 	"weekly": [
# 		"chronotally.tasks.weekly"
# 	],
# 	"monthly": [
# 		"chronotally.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "chronotally.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "chronotally.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "chronotally.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = ["chronotally.chronotally.cors.handle_cors"]
after_request = ["chronotally.chronotally.cors.add_cors_headers"]

# Job Events
# ----------
# before_job = ["chronotally.utils.before_job"]
# after_job = ["chronotally.utils.after_job"]

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
# 	"chronotally.auth.validate"
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

update_website_context = "chronotally.chronotally.csrf_token.extend_context"
