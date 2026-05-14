// filters
// cur_frm.fields_dict.notify_party_address_table.grid.get_field("notify_party").get_query = function (doc) {
//     return {
//         query: "frappe.contacts.doctype.address.address.address_query",
//         filters: { link_doctype: "Customer", link_name: cur_frm.doc.customer }
//     };
// };
frappe.ui.form.on("Sales Order", "validate",  function(frm) {
    if (frm.doc.notify_party_address_table){
	frm.doc.notify_party_address_table.forEach( function(row) {
		if (row.notify_party) {
            return frappe.call({
                method: "frappe.contacts.doctype.address.address.get_address_display",
                args: {
                    "address_dict": row.notify_party
                },
                callback: function (r) {
                    if (r.message)
                    frappe.model.set_value(row.doctype,row.name,"notify_address_display", r.message);
                }
            });
            frm.refresh_field("notify_party_address_table");
        }
	});
    }

});
frappe.ui.form.on("Sales Order","onload",  function(frm) {
    if(frm.doc.letter_head){
        cur_frm.fields_dict.letter_head.get_query = function(doc) {
            return {
                filters: {
                    "Company": doc.company
                }
            }
        };
    }
});
frappe.ui.form.on("Notify Party Address",{
    notify_party: function(frm,cdt,cdn){
        let row = locals[cdt][cdn]
		if (row.notify_party) {
            return frappe.call({
                method: "frappe.contacts.doctype.address.address.get_address_display",
                args: {
                    "address_dict": row.notify_party
                },
                callback: function (r) {
                    if (r.message)
                        frappe.model.set_value(row.doctype,row.name,"notify_address_display", r.message);
                }
            });
        }
    }
});
frappe.ui.form.on("Sales Order", {
  
    before_save: function (frm) {
        frm.trigger("cal_total");
    },
    cal_total: function (frm) {
        let total_freight = 0.0;
        let total_insurance = 0.0;
        let total_fob_value = 0.0;

        frm.doc.items.forEach(function (d) {
            total_freight += flt(d.freight);
            total_insurance += flt(d.insurance);
            total_fob_value += flt(d.fob_value)

        });
        frm.set_value("freight", total_freight);
        frm.set_value("insurance", total_insurance);
        frm.set_value("total_fob_value",total_fob_value)
    }
   
})
frappe.ui.form.on("Sales Order Item", {
    qty: function (frm, cdt, cdn) {
        frappe.db.get_value("Address", frm.doc.customer_address, 'country', function (r) {
            if (r.country != "India") {
                frappe.model.set_value(cdt, cdn, "fob_value", flt(d.base_amount - d.freight_inr - d.insurance_inr));
            }
        })
    },
    freight: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        frappe.db.get_value("Address", frm.doc.customer_address, 'country', function (r) {
            if (r.country != "India") {
                frappe.model.set_value(cdt, cdn, "freight_inr", flt(d.freight * frm.doc.conversion_rate));
                frappe.model.set_value(cdt, cdn, "fob_value", flt(d.base_amount - d.insurance_inr - d.freight_inr));
                
            }
        })
    },
    insurance: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        frappe.db.get_value("Address", frm.doc.customer_address, 'country', function (r) {
            if (r.country != "India") {
                frappe.model.set_value(cdt, cdn, "insurance_inr", flt(d.insurance * frm.doc.conversion_rate));
                frappe.model.set_value(cdt, cdn, "fob_value", flt(d.base_amount - d.insurance_inr - d.freight_inr));
                
            }
        })
    }
});