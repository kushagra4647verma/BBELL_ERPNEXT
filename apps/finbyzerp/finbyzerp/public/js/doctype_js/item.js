frappe.ui.form.on('Item', {
	is_non_factory_item: function(frm) {
		if (frm.doc.is_non_factory_item) {
			// Set default warehouse to Non-Factory Stores for all item defaults
			let updated = false;
			if (frm.doc.item_defaults && frm.doc.item_defaults.length) {
				frm.doc.item_defaults.forEach(function(row) {
					if (!row.default_warehouse) {
						frappe.model.set_value(row.doctype, row.name, 'default_warehouse', 'Non-Factory Stores - Test');
						updated = true;
					}
				});
			}
			if (!updated) {
				frappe.msgprint(__('Please set the Default Warehouse to "Non-Factory Stores - Test" in the Item Defaults table.'));
			}
		}
	}
});
