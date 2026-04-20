app_name = "purchase_fast_entry"
app_title = "purchase_fast_entry"
app_publisher = "Neural Pulse"
app_description = "Fast purchase entries"
app_email = "kushagra4647@gmail.com"
app_license = "MIT"

# ---------------------------------------------------------------------------
# DocType Class Overrides
# ---------------------------------------------------------------------------
# Replaces the standard PurchaseInvoice class with our custom subclass.
# The subclass fixes GL entries so that the Supplier (credit_to) account is
# credited with Grand Total MINUS any TDS / deduction rows, instead of the
# full Grand Total.
#
# All other PurchaseInvoice behaviour is inherited unchanged.

override_doctype_class = {
    "Purchase Invoice": "purchase_fast_entry.overrides.purchase_invoice.CustomPurchaseInvoice"
}

# ---------------------------------------------------------------------------
# Includes in <head>
# ---------------------------------------------------------------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/purchase_fast_entry/css/purchase_fast_entry.css"
# app_include_js = "/assets/purchase_fast_entry/js/purchase_fast_entry.js"

# include js, css files in header of web template
# web_include_css = "/assets/purchase_fast_entry/css/purchase_fast_entry.css"
# web_include_js = "/assets/purchase_fast_entry/js/purchase_fast_entry.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# ---------------------------------------------------------------------------
# DocType JS Overrides
# ---------------------------------------------------------------------------
# Injects custom JS into the Purchase Invoice form.
# Adds the "Manage Attachments" button under the Actions dropdown.
# Visible only to Accounts Manager / System Manager.

doctype_js = {
    "Purchase Invoice": "public/js/purchase_invoice_overrides.js",
    "Sales Invoice":    "public/js/sales_invoice_gst.js",
}

# Amendment / Create-Edit-Display mode controller
# Applied to both Purchase Invoice and Sales Invoice via app_include_js
app_include_js = ["/assets/purchase_fast_entry/js/document_controls.js"]

# include js in doctype views
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# ---------------------------------------------------------------------------
# Home Pages
# ---------------------------------------------------------------------------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#     "Role": "home_page"
# }

# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# ---------------------------------------------------------------------------
# Jinja
# ---------------------------------------------------------------------------

# add methods and filters to jinja environment
# jinja = {
#     "methods": "purchase_fast_entry.utils.jinja_methods",
#     "filters": "purchase_fast_entry.utils.jinja_filters"
# }

# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

# before_install = "purchase_fast_entry.install.before_install"
after_install = "purchase_fast_entry.setup.create_custom_fields_on_install"

# ---------------------------------------------------------------------------
# Uninstallation
# ---------------------------------------------------------------------------

# before_uninstall = "purchase_fast_entry.uninstall.before_uninstall"
# after_uninstall = "purchase_fast_entry.uninstall.after_uninstall"

# ---------------------------------------------------------------------------
# Document Events
# ---------------------------------------------------------------------------

# doc_events = {
#     "*": {
#         "on_update": "method",
#         "on_cancel": "method",
#         "on_trash": "method"
#     }
# }

# ---------------------------------------------------------------------------
# Scheduled Tasks
# ---------------------------------------------------------------------------

# scheduler_events = {
#     "all": [
#         "purchase_fast_entry.tasks.all"
#     ],
#     "daily": [
#         "purchase_fast_entry.tasks.daily"
#     ],
#     "hourly": [
#         "purchase_fast_entry.tasks.hourly"
#     ],
#     "weekly": [
#         "purchase_fast_entry.tasks.weekly"
#     ],
#     "monthly": [
#         "purchase_fast_entry.tasks.monthly"
#     ],
# }

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

# before_tests = "purchase_fast_entry.install.before_tests"

# ---------------------------------------------------------------------------
# Overriding Methods
# ---------------------------------------------------------------------------

# override_whitelisted_methods = {
#     "frappe.desk.doctype.event.event.get_events": "purchase_fast_entry.event.get_events"
# }

# ---------------------------------------------------------------------------
# DocType Dashboards
# ---------------------------------------------------------------------------

# override_doctype_dashboards = {
#     "Task": "purchase_fast_entry.task.get_dashboard_data"
# }

# ---------------------------------------------------------------------------
# Exempt linked doctypes from being automatically cancelled
# ---------------------------------------------------------------------------

# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# ---------------------------------------------------------------------------
# Ignore links to specified DocTypes when deleting documents
# ---------------------------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# ---------------------------------------------------------------------------
# Request Events
# ---------------------------------------------------------------------------

# before_request = ["purchase_fast_entry.utils.before_request"]
# after_request = ["purchase_fast_entry.utils.after_request"]

# ---------------------------------------------------------------------------
# User Data Protection
# ---------------------------------------------------------------------------

# user_data_fields = [
#     {
#         "doctype": "{doctype_1}",
#         "filter_by": "{filter_by}",
#         "redact_fields": ["{field_1}", "{field_2}"],
#         "partial": 1,
#     },
# ]

# ---------------------------------------------------------------------------
# Authentication and authorization
# ---------------------------------------------------------------------------

# auth_hooks = [
#     "purchase_fast_entry.auth.validate"
# ]