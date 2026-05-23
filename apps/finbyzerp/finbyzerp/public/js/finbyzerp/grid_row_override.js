// Override frappe's grid row column width validation to remove the 10-column limit
frappe.after_ajax(function() {
	if (frappe.ui.form.GridRow) {
		frappe.ui.form.GridRow.prototype.validate_columns_width = function() {
			// No limit on total column width - allow all columns in quick entry
		};
	}
});
