/**
 * Edit Submitted Document
 * Adds an "Edit" option to the three-dots menu for submitted
 * Sales Invoice, Sales Order, and Purchase Invoice.
 * Cancels + deletes the document and pre-fills a new form.
 */

function add_edit_button(frm) {
	if (frm.doc.docstatus !== 1) return;

	frm.add_custom_button(__("Edit"), function () {
		frappe.confirm(
			__("This will cancel and delete {0}. A new form will open pre-filled with the same data. Are you sure?", [frm.doc.name]),
			function () {
				frappe.call({
					method: "finbyzerp.finbyzerp.doc_events.edit_submitted.cancel_delete_and_prefill",
					args: {
						doctype: frm.doc.doctype,
						docname: frm.doc.name,
					},
					freeze: true,
					freeze_message: __("Cancelling and preparing new form..."),
					callback: function (r) {
						if (r.message) {
							// Open new document with prefilled data
							let new_doc = frappe.model.make_new_doc_and_get_name(frm.doc.doctype);
							frappe.model.with_doc(frm.doc.doctype, new_doc, function () {
								let doc = frappe.get_doc(frm.doc.doctype, new_doc);
								// Copy all fields from response
								$.extend(doc, r.message);
								doc.name = new_doc;
								doc.docstatus = 0;
								frappe.set_route("Form", frm.doc.doctype, new_doc);
							});
						}
					},
					error: function (r) {
						// Error is shown by frappe automatically (PermissionError etc.)
					}
				});
			}
		);
	}, __("Actions"));
}

frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {
		add_edit_button(frm);
	}
});

frappe.ui.form.on("Sales Order", {
	refresh: function (frm) {
		add_edit_button(frm);
	}
});

frappe.ui.form.on("Purchase Invoice", {
	refresh: function (frm) {
		add_edit_button(frm);
	}
});
