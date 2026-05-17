import frappe
from erpnext.stock.doctype.quality_inspection.quality_inspection import QualityInspection as _QualityInspection

# Custom doctypes that don't follow the "{doctype} Item" naming convention
CUSTOM_REFERENCE_CHILD_MAP = {
	"Outward Sample": "Outward Sample Detail",
	"Inward Sample": "Inward Sample Detail",
}

class QualityInspection(_QualityInspection):
	def set_child_row_reference(self):
		# Skip for custom doctypes that don't have a standard "{doctype} Item" child table
		if self.reference_type in CUSTOM_REFERENCE_CHILD_MAP:
			return
		# Also skip if the child table doesn't exist
		doctype = self.reference_type + " Item"
		if self.reference_type == "Stock Entry":
			doctype = "Stock Entry Detail"
		if not frappe.db.table_exists(f"tab{doctype}"):
			return
		super().set_child_row_reference()

	def update_qc_reference(self, remove_reference=False):
		# TODO: to be done in version-15
		# Added Item Reference Field For Proper Update

		quality_inspection = self.name if self.docstatus == 1 else ""

		if self.reference_type == "Job Card":
			if self.reference_name:
				frappe.db.sql(
					"""
					UPDATE `tab{doctype}`
					SET quality_inspection = %s, modified = %s
					WHERE name = %s and production_item = %s
				""".format(
						doctype=self.reference_type
					),
					(quality_inspection, self.modified, self.reference_name, self.item_code),
				)

		else:
			args = [quality_inspection, self.modified, self.reference_name, self.ref_item, self.item_code]
			doctype = self.reference_type + " Item"

			if self.reference_type == "Stock Entry":
				doctype = "Stock Entry Detail"

			# Skip for custom doctypes that don't have a standard child table
			if self.reference_type in CUSTOM_REFERENCE_CHILD_MAP:
				return
			if not frappe.db.table_exists(f"tab{doctype}"):
				return

			if self.reference_type and self.reference_name:
				conditions = ""
				if self.batch_no and self.docstatus == 1:
					conditions += " and t1.batch_no = %s"
					args.append(self.batch_no)

				if self.docstatus == 2:  # if cancel, then remove qi link wherever same name
					conditions += " and t1.quality_inspection = %s"
					args.append(self.name)

				frappe.db.sql(
					"""
					UPDATE
						`tab{child_doc}` t1, `tab{parent_doc}` t2
					SET
						t1.quality_inspection = %s, t2.modified = %s
					WHERE
						t1.parent = %s
						and t1.name = %s
						and t1.item_code = %s
						and t1.parent = t2.name
						{conditions}
				""".format(
						parent_doc=self.reference_type, child_doc=doctype, conditions=conditions
					),
					args,
				)
