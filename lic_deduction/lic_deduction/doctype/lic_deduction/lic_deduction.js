// Copyright (c) 2024, quantbit.erpdata.in and contributors
// For license information, please see license.txt

frappe.ui.form.on('LIC Deduction', {
	// refresh: function(frm) {

	// }
});


// frappe.ui.form.on('LIC Deduction', {
//     refresh: function(frm) {
//         frm.fields_dict['items'].grid.get_field('item_name').get_query = function(doc, cdt, cdn) {
//             var child = locals[cdt][cdn];
//             return {
//                 filters: [
//                     ["Policy Name", "policy_type", '=', frm.doc.item_code]
//                 ]
//             };
//         };
//     }
// });


// frappe.ui.form.on('LIC Deduction', {
// 	setup: function(frm) {	
// 			frm.set_query("item_name", "items", function(doc, cdt, cdn) {
// 				let d = locals[cdt][cdn];
// 				if(frm.doc.item_code){
// 					return {
// 						filters: [
// 							["Policy Name", "policy_type", '=', frm.doc.item_code]
//                     ]
// 					};
// 				}
						
// 			})
	
//     },
// });


frappe.ui.form.on("Policy Info Details", {
    inst_amount: function(frm, cdt, cdn) {
        var total1 = 0;
        frm.doc.items.forEach(function(d) {
            // Check if the checkbox is unchecked before adding the installment amount
            if (!d.disabled) {
                total1 += d.inst_amount;
            }
        });
        frm.set_value("total_inst_amount", total1);
        refresh_field("total_inst_amount");
    },
    items_remove: function(frm, cdt, cdn) {
        var total1 = 0;
        frm.doc.items.forEach(function(d) {
            // Check if the checkbox is unchecked before adding the installment amount
            if (!d.disabled) {
                total1 += d.inst_amount;
            }
        });
        frm.set_value("total_inst_amount", total1);
        refresh_field("total_inst_amount");
    }
});


frappe.ui.form.on("Policy Info Details", {
    disabled: function(frm, cdt, cdn) {
        var total1 = 0;
        frm.doc.items.forEach(function(d) {
            // Check if the checkbox is unchecked before adding the installment amount
            if (!d.disabled) {
                total1 += d.inst_amount;
            }
        });
        frm.set_value("total_inst_amount", total1);
        refresh_field("total_inst_amount");
    },
    items_remove: function(frm, cdt, cdn) {
        var total1 = 0;
        frm.doc.items.forEach(function(d) {
            // Check if the checkbox is unchecked before adding the installment amount
            if (!d.disabled) {
                total1 += d.inst_amount;
            }
        });
        frm.set_value("total_inst_amount", total1);
        refresh_field("total_inst_amount");
    }
});



frappe.ui.form.on('Policy Info Details', {
	end_date: function(frm) {
		frm.call({
			method:'cal_total_installment',
			doc:frm.doc
		})
	}
});



frappe.ui.form.on('Policy Info Details', {
	item_code: function(frm) {
		frm.call({
			method:'set_reference',
			doc:frm.doc
		})
	}
});

frappe.ui.form.on('Policy Info Details', {
	disabled: function(frm) {
		frm.call({
			method:'checkall',
			doc:frm.doc
		})
	}
});