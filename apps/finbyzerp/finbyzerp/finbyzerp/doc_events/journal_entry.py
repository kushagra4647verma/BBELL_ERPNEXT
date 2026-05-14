import frappe

def on_trash(doc, method=None):
	"""Delete cancelled GL entries when a cancelled Journal Entry is deleted."""
	frappe.db.delete("GL Entry", {
		"voucher_no": doc.name,
		"is_cancelled": 1
	})
