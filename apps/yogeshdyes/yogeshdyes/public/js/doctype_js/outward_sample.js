frappe.ui.form.on("Outward Sample",  {
    product_name: function(frm){
        frappe.db.get_value("Item", frm.doc.product_name, "msds_certificate", function (d) {
            if(d.msds_certificate){
                frm.set_value("msds_certificate",d.msds_certificate)
            }else{
                frm.set_value("msds_certificate","")
            }
        })
        frappe.db.get_value("Item", frm.doc.product_name, "tds_certificate", function (d) {
            if(d.tds_certificate){
                frm.set_value("tds_certificate",d.tds_certificate)
            }else{
                frm.set_value("tds_certificate","")
            }
        })
    }
})