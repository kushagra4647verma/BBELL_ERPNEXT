// Copyright (c) 2023, Finbyz Tech. Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Purchase Comparison"] = {
	"filters": [
		{
			"label": __("Company"),
			"fieldname":"company",
			"fieldtype":"Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"label": __("Item"),
			"fieldname":"item_code",
			"fieldtype":"Link",
			"options": "Item",
		},
		{
			"label": __("Warehouse"),
			"fieldname":"warehouse",
			"fieldtype":"Link",
			"options": "Warehouse",
			"get_query": () =>{
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {"company": company}
				}
			}
		}
	]
};
