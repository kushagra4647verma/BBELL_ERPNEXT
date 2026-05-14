import frappe
from frappe import _
from frappe.utils import add_days, cint, formatdate, get_datetime, getdate

NON_FACTORY_WAREHOUSE = "Non-Factory Stores - Test"

def validate(self, method):
	before_validate(self, method)
	if self.is_new() and not self.is_stock_item:
		for row in self.item_defaults:
			if not row.expense_account:
				frappe.msgprint("Please define correct expense account in Item Defaults.<br>In absence of same expense will be parked in 'Cost of Goods Sold' account")

	# If Non-Factory Item, set default warehouse to Non-Factory Stores
	if self.get("is_non_factory_item"):
		for row in self.item_defaults:
			if row.default_warehouse and row.default_warehouse != NON_FACTORY_WAREHOUSE:
				frappe.throw(
					_("Item is marked as Non-Factory Item. Default Warehouse must be set to '{0}', not '{1}'.").format(
						NON_FACTORY_WAREHOUSE, row.default_warehouse
					)
				)
			if not row.default_warehouse:
				row.default_warehouse = NON_FACTORY_WAREHOUSE
		# frappe.msgprint("Please define correct expense account in Item Defaults.<br>In absence of same expense will be parked in 'Cost of Goods Sold' account")

def before_validate(self,method):
	if "'" in self.item_code or '"' in self.item_code:
		frappe.throw(""" Item Code not allowed with any special Characters like " or ' """)

def before_rename(self, method, old, new, merge=False):
	fiscal_year_frozen_till_date = frappe.db.get_value("Accounts Settings", None, "fiscal_year_frozen_till_date")
	if fiscal_year_frozen_till_date and merge:
		frappe.throw(
			_("No one Authorized to Merge Items as Fiscal Year Frozen Date has Applied")
			)