import frappe
from frappe import _

SALES_ADMIN_USERS = ["Administrator", "admin@bbell.in"]
SALES_DOCTYPES = ["Sales Invoice", "Sales Order"]
PURCHASE_DOCTYPES = ["Purchase Invoice"]


def check_edit_permission(doctype):
	"""Check if current user has permission to edit the given doctype."""
	if doctype in SALES_DOCTYPES:
		if frappe.session.user not in SALES_ADMIN_USERS:
			frappe.throw(
				_("Only Administrator users can edit submitted {0}. Please contact your administrator.").format(doctype),
				frappe.PermissionError,
				title=_("Permission Denied")
			)
	# Purchase Invoice - any user can edit (no restriction)


@frappe.whitelist()
def cancel_delete_and_prefill(doctype, docname):
	"""
	Cancel and delete a submitted document, then return its data for re-creation.
	Used for the Edit workflow on submitted documents.
	"""
	check_edit_permission(doctype)

	doc = frappe.get_doc(doctype, docname)

	if doc.docstatus != 1:
		frappe.throw(_("Only submitted documents can be edited this way."))

	# Store data before cancelling
	doc_data = doc.as_dict()

	# Cancel the document
	doc.cancel()

	# Delete the cancelled document
	frappe.delete_doc(doctype, docname, force=True, ignore_permissions=True)

	# Clean up the data for re-creation
	fields_to_remove = [
		"name", "creation", "modified", "modified_by", "owner",
		"docstatus", "amended_from", "amendment_date",
		"irn", "irn_cancelled", "eway_bill_cancelled",
		"ewaybill", "eway_bill_validity",
	]
	for field in fields_to_remove:
		doc_data.pop(field, None)

	# Reset child table names
	for key, value in doc_data.items():
		if isinstance(value, list):
			for row in value:
				if isinstance(row, dict):
					row.pop("name", None)
					row.pop("creation", None)
					row.pop("modified", None)
					row.pop("parent", None)
					row.pop("docstatus", None)

	frappe.msgprint(
		_("{0} {1} has been cancelled and deleted. A new form has been pre-filled with the same data.").format(
			doctype, docname
		),
		alert=True
	)

	return doc_data
