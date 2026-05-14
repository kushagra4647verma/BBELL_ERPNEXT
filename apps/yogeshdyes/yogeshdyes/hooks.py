# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "yogeshdyes"
app_title = "Yogeshdyes"
app_publisher = "Finbyz Tech. Pvt. Ltd."
app_description = "Customize App for Yogesh dye stuff"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@finbyz.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/yogeshdyes/css/yogeshdyes.css"
# app_include_js = "/assets/yogeshdyes/js/yogeshdyes.js"

# include js, css files in header of web template
# web_include_css = "/assets/yogeshdyes/css/yogeshdyes.css"
# web_include_js = "/assets/yogeshdyes/js/yogeshdyes.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

doctype_js = {
	"Sales Order": "public/js/doctype_js/sales_order.js",
	"Sales Invoice": "public/js/doctype_js/sales_invoice.js",
	"Payment Entry":"public/js/doctype_js/payment_entry.js",
	"Quotation":"public/js/doctype_js/quotation.js",
	"Purchase Order":"public/js/doctype_js/purchase_order.js",
	"Purchase Invoice":"public/js/doctype_js/purchase_invoice.js",
	"Purchase Receipt":"public/js/doctype_js/purchase_receipt.js",
	"Delivery Note":"public/js/doctype_js/delivery_note.js",
	"Outward Sample": "public/js/doctype_js/outward_sample.js",
	"Outward Tracking": "public/js/doctype_js/outward_tracking.js",
}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "yogeshdyes.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "yogeshdyes.install.before_install"
# after_install = "yogeshdyes.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "yogeshdyes.notifications.get_notification_config"

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

# Document Events
# ---------------
# Hook on document methods and events


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"yogeshdyes.tasks.all"
# 	],
# 	"daily": [
# 		"yogeshdyes.tasks.daily"
# 	],
# 	"hourly": [
# 		"yogeshdyes.tasks.hourly"
# 	],
# 	"weekly": [
# 		"yogeshdyes.tasks.weekly"
# 	]
# 	"monthly": [
# 		"yogeshdyes.tasks.monthly"
# 	]
# }
scheduler_events = {
	"cron":{
		"5 */12 * * SUN": [
			"yogeshdyes.api.sales_invoice_mails",
		],
	}
}
# Testing
# -------

# before_tests = "yogeshdyes.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "yogeshdyes.event.get_events"
# }
override_whitelisted_methods = {
	"erpnext.controllers.accounts_controller.update_child_qty_rate": "yogeshdyes.yogeshdyes.doc_event.accounts_controller.update_child_qty_rate"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "yogeshdyes.task.get_dashboard_data"
# }


doc_events = {
	"User Permission":{
		"validate":"yogeshdyes.api.validate_user_permission",
		"on_trash":"yogeshdyes.api.validate_user_permission",
	},
	"Purchase Invoice":{
		"validate":"yogeshdyes.api.pi_validate",
		"on_submit":"yogeshdyes.api.pi_on_submit"
	},
	"Sales Invoice": {
		"before_save": "yogeshdyes.api.si_before_save",
		"on_update": "yogeshdyes.api.si_on_update",
	},
	'Inward Sample':{
		'before_naming':"yogeshdyes.api.before_naming"
	}
}