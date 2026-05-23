// filters
// cur_frm.fields_dict.notify_party_address_table.grid.get_field("notify_party").get_query = function (doc) {
//     return {
//         query: "frappe.contacts.doctype.address.address.address_query",
//         filters: { link_doctype: "Customer", link_name: cur_frm.doc.customer }
//     };
// };
frappe.ui.form.on("Sales Invoice",  {
    validate: function(frm){
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
    },
    commission_rate: function(frm) {
        if (frm.doc.freight<0 && frm.doc.insurance<0){
        let tot_cal=(frm.doc.total+frm.doc.freight+frm.doc.insurance);
        let value=(tot_cal*frm.doc.commission_rate)/100
        // this.frm.doc.total_commission = flt(value,precision("total_commission"));
        frm.set_value("commission_usd",value);
        // frm.set_value("total_commission",value);
       }
       if (frm.doc.freight>=0 && frm.doc.insurance>=0){
        let tot_cal=(frm.doc.total);
        let value=(tot_cal * frm.doc.commission_rate)/100
        frm.set_value("commission_usd",value);
       }
     
		// frm.trigger('calculate_commission_');
	},
    custom_consignee_address:function(frm){
        if(!frm.doc.custom_consignee_address){
            frm.set_value('custom_consignee_address_display' , '')
        }

    },
    custom_address:function(frm){
        if(!frm.doc.custom_address){
            console.log("test")
            frm.set_value('custom_address_display' , '')
        }

    },

    // calculate_commission_: function (frm) {
    //     console.log(frm.doc.freight)
    //    if (frm.doc.freight<0 && frm.doc.insurance<0){
    //     let tot_cal=(frm.doc.total+frm.doc.freight+frm.doc.insurance)*frm.doc.conversion_rate;
    //     let value=(tot_cal*frm.doc.commission_rate)/100
    //     console.log(value)
    //     frm.set_value("total_commission",value);
    //    }
    //    if (frm.doc.freight>0 && frm.doc.insurance>0){
    //     let tot_cal=(frm.doc.total)*frm.doc.conversion_rate;
    //     let value=(tot_cal * frm.doc.commission_rate)/100
    //     console.log(value)
    //     frm.set_value("total_commission",value);
    //    }
    // },

    cal_pallets: function (frm){
        let total_pallets = 0;
        let total_qty = 0;

        frm.doc.items.forEach(function (d) {
            total_qty += flt(d.qty);
            total_pallets += flt(d.total_pallets);
        });

        frm.set_value("pallet_weight",total_pallets);
        frm.set_value("total_net_weight", total_qty);
    },
    before_save: function (frm) {
        frm.trigger("cal_total");
        frm.trigger("cal_pallets");
        // frm.trigger("calculate_commission_");
    },
    cal_total: function (frm) {
        let total_gt_wt = frm.doc.total_tare_wt + frm.doc.total_qty;
        frm.set_value("total_gr_wt", total_gt_wt);
        
    },
    onload: function(frm){
        if(frm.doc.letter_head){
        cur_frm.fields_dict.letter_head.get_query = function(doc) {
            return {
                filters: {
                    "Company": doc.company
                }
            }
        };
        }
        cur_frm.fields_dict.lut_detail.get_query = function(doc) {
            return {
                filters: {
                    "Company": frm.doc.company
                }
            }
        };
        
    }, 
    before_save: function(frm){
        frm.trigger('cal_igst_amount');
    },
    cal_igst_amount: function (frm) {
        let total_igst = 0.0;
            if(frm.doc.gst_category == "Overseas"){
                frm.doc.items.forEach(function (d) {
                    if (d.igst_rate) {
                        frappe.model.set_value(d.doctype, d.name, 'igst_amount', d.base_amount * parseInt(d.igst_rate) / 100);
                    } else {
                        frappe.model.set_value(d.doctype, d.name, 'igst_amount', 0.0);
                    }
                    total_igst += flt(d.igst_amount);
                });
                frm.set_value('total_igst_amount', total_igst);
            }
    },
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
    },
});
// frappe.ui.form.on("Sales Invoice Item",  {
//     freight: function(frm, cdt, cdn) {
//         frm.events.calculate_total_freight(frm, cdt, cdn)
//     },
//     items_remove: function(frm, cdt, cdn) {
//         frm.events.calculate_total_freight(frm, cdt, cdn)
//     }
// });

erpnext.accounts.SalesInvoiceController = class SalesInvoiceController extends erpnext.accounts.SalesInvoiceController{
    payment_terms_template() {
		var me = this;
        const doc = me.frm.doc;
		if(doc.payment_terms_template && doc.doctype !== 'Delivery Note' && doc.docstatus != 1) {
            if (frappe.meta.get_docfield("Sales Invoice", "bl_date") || frappe.meta.get_docfield("Sales Invoice", "shipping_bill_date")){
                var posting_date = doc.bl_date || doc.shipping_bill_date || doc.posting_date || doc.transaction_date;
            }
            else{
                var posting_date =  doc.posting_date || doc.transaction_date;
            }

			frappe.call({
				method: "erpnext.controllers.accounts_controller.get_payment_terms",
				args: {
					terms_template: doc.payment_terms_template,
					posting_date: posting_date,
					grand_total: doc.rounded_total || doc.grand_total,
                    base_grand_total: doc.base_rounded_total || doc.base_grand_total,
					bill_date: doc.bill_date
				},
				callback: function(r) {
					if(r.message && !r.exc) {
						me.frm.set_value("payment_schedule", r.message);
					}
				}
			})
		}
    }
    bl_date() {
		var me = this;
        const doc = me.frm.doc;
		if(doc.payment_terms_template && doc.doctype !== 'Delivery Note' && doc.docstatus != 1) {
            if (frappe.meta.get_docfield("Sales Invoice", "bl_date") || frappe.meta.get_docfield("Sales Invoice", "shipping_bill_date")){
                var posting_date = doc.bl_date || doc.shipping_bill_date || doc.posting_date || doc.transaction_date;
            }
            else{
                var posting_date =  doc.posting_date || doc.transaction_date;
            }

			frappe.call({
				method: "erpnext.controllers.accounts_controller.get_payment_terms",
				args: {
					terms_template: doc.payment_terms_template,
					posting_date: posting_date,
					grand_total: doc.rounded_total || doc.grand_total,
                    base_grand_total: doc.base_rounded_total || doc.base_grand_total,
					bill_date: doc.bill_date
				},
				callback: function(r) {
					if(r.message && !r.exc) {
						me.frm.set_value("payment_schedule", r.message);
					}
				}
			})
		}
}}


