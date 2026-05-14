frappe.ui.form.on("Delivery Note",  {
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
    }
    });