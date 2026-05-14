frappe.ui.form.on("Payment Entry",  {
    onload: function(frm){
        cur_frm.fields_dict.letter_head.get_query = function(doc) {
            return {
                filters: {
                    "Company": doc.company
                }
            }
        };
        cur_frm.fields_dict.bank_account.get_query = function(doc) {
            return {
                filters: {
                    "Company": doc.company
                }
            }
        };

    }
})