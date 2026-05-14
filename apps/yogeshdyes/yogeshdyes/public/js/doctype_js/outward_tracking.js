frappe.ui.form.on('Outward Tracking', {
    company_address: function(frm){
        if(frm.doc.company_address) {
			frappe.call({
				method: "frappe.contacts.doctype.address.address.get_address_display",
				args: {"address_dict": frm.doc.company_address },
				callback: function(r) {
					if(r.message) {
						me.frm.set_value("company_address_display", r.message)
					}
				}
			})
		} else {
			frm.set_value("company_address_display", "");
		}
    },
	before_save: function (frm) {
		let total_qty = 0.0;
		let total_amount = 0.0;
		
		if (frm.doc.has_sample && frm.doc.sample_items) { 
			frm.doc.sample_items.forEach(function (d) {
				total_qty += flt(d.quantity);
				total_amount += flt(d.rate);
			});
		}
		frm.set_value("total_qty", total_qty);
		frm.set_value("total_amount", total_amount);
		
	}
   
})