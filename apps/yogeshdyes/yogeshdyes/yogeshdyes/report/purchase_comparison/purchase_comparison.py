# Copyright (c) 2023, Finbyz Tech. Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import (
	nowdate,
	flt,
	cint,
	cstr,
	now_datetime,
	getdate,
	add_days,
	add_months,
	get_last_day,
)
from frappe import _
# from yogeshdyes.yogeshdyes.report.purchase_comparison.purchase_comparison import get_data

def execute(filters={"item_code":"3 Core X 0.5 mm Sq Copper Shielded  Cable"}):
	columns, data = [], []
	data = get_data(filters)
	columns = get_columns(filters)
	return columns, data
# .where(purchase_invoice.posting_date <= self.filters.to_date)
def get_last_purchase_rate(item_code):
		purchase_invoice = frappe.qb.DocType("Purchase Invoice")
		purchase_invoice_item = frappe.qb.DocType("Purchase Invoice Item")

		query = (
			frappe.qb.from_(purchase_invoice_item)
			.inner_join(purchase_invoice)
			.on(purchase_invoice.name == purchase_invoice_item.parent)
			.select(purchase_invoice_item.base_rate / purchase_invoice_item.conversion_factor , purchase_invoice_item.qty,purchase_invoice_item.uom , purchase_invoice.posting_date , purchase_invoice.supplier)
			.where(purchase_invoice.docstatus == 1)
			.where(purchase_invoice_item.item_code == item_code)
			.orderby(purchase_invoice.posting_date,order=frappe.qb.desc)
			.limit(1)
		)
		last_purchase_rate = query.run()
		return last_purchase_rate if last_purchase_rate else 0

def get_data(filters):
	conditions = ""
	if filters.get('item_code'):
		conditions += f" and item.name = '{filters.get('item_code')}' "
	if filters.get('company'):
		conditions += f" and item.company = '{filters.get('company')}' "
	if filters.get('warehouse'):
		conditions += f" and bin.warehouse = '{filters.get('warehouse')}' "
	item_data = frappe.db.sql(f"""
						SELECT item.name as item	, item.item_name ,bin.warehouse, sum(bin.actual_qty) as actual_qty , 
						ir.warehouse_reorder_level , ir.warehouse_reorder_qty
						From `tabItem` as item
						left join `tabBin` as bin ON bin.item_code =  item.name
						left join `tabItem Reorder` as ir ON ir.parent = item.name and ir.warehouse = bin.warehouse
						Where item.disabled = 0 {conditions}
						Group By item.name,bin.warehouse
						""" , as_dict = 1)

	for row in item_data:
		last_purchase_rate = get_last_purchase_rate(row.item)
		if last_purchase_rate:
			row.update({"last_purchase_rate": last_purchase_rate[0][0] , "last_purchase_qty":last_purchase_rate[0][1] ,"uom":last_purchase_rate[0][2], "last_purchase_date" : last_purchase_rate[0][3] , "last_purchase_supplier":last_purchase_rate[0][4] })



	return item_data


def get_columns(filters):
	columns = [
		{"label": _("Item"), "fieldname": "item", "fieldtype":"Link" , "options":"Item" , "width": 120},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype":"Data" , "width": 120},
		{"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype":"Link" , "options":"Warehouse" , "width": 120},
		{"label": _("Actual Qty"), "fieldname": "actual_qty", "fieldtype":"Float" , "width": 120},
		{"label": _("Reorder Level"), "fieldname": "warehouse_reorder_level", "fieldtype":"Data" , "width": 120},
		{"label": _("Reorder Qty"), "fieldname": "warehouse_reorder_qty", "fieldtype":"Float" , "width": 120},
		{"label": _("Last Purchase Rate"), "fieldname": "last_purchase_rate", "fieldtype":"Float" , "width": 120},
		{"label": _("Last Purchase Qty"), "fieldname": "last_purchase_qty", "fieldtype":"Float" , "width": 120},
		{"label": _("UOM"), "fieldname": "uom", "fieldtype":"Data" , "width": 120},
		{"label": _("Last Purchase Supplier"), "fieldname": "last_purchase_supplier", "fieldtype":"Link" , "options":"Supplier", "width": 120},
	]
	return columns