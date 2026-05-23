import frappe


def set_has_attachment(doc, method=None):
	"""Set has_attachment field based on file attachments."""
	count = frappe.db.count("File", {
		"attached_to_doctype": doc.doctype,
		"attached_to_name": doc.name
	})
	doc.has_attachment = "Yes" if count else "No"


def update_has_attachment_on_file_change(doc, method=None):
	"""Update has_attachment on the parent document when a file is attached or deleted."""
	if doc.attached_to_doctype not in ("Sales Invoice", "Purchase Invoice"):
		return
	if not doc.attached_to_name:
		return

	count = frappe.db.count("File", {
		"attached_to_doctype": doc.attached_to_doctype,
		"attached_to_name": doc.attached_to_name
	})
	if method == "on_trash":
		count = max(0, count - 1)

	value = "Yes" if count else "No"
	frappe.db.set_value(doc.attached_to_doctype, doc.attached_to_name, "has_attachment", value, update_modified=False)


def backfill_has_attachment():
	"""Backfill has_attachment for all existing Sales Invoice and Purchase Invoice records."""
	for doctype in ("Sales Invoice", "Purchase Invoice"):
		# Get all docs with attachments
		attached = frappe.db.sql("""
			SELECT DISTINCT attached_to_name
			FROM `tabFile`
			WHERE attached_to_doctype = %s
		""", doctype, as_list=True)
		attached_names = {r[0] for r in attached}

		# Set Yes for those with attachments
		if attached_names:
			frappe.db.sql("""
				UPDATE `tab{doctype}` SET has_attachment = 'Yes'
				WHERE name IN ({placeholders})
			""".format(
				doctype=doctype,
				placeholders=", ".join(["%s"] * len(attached_names))
			), list(attached_names))

		# Set No for the rest
		frappe.db.sql("""
			UPDATE `tab{doctype}` SET has_attachment = 'No'
			WHERE has_attachment IS NULL OR has_attachment = ''
		""".format(doctype=doctype))

		frappe.db.commit()
		print(f"{doctype}: {len(attached_names)} with attachments, rest set to No")
