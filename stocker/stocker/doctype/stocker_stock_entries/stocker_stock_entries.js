// // Copyright (c) 2025, asithara@htsqatar.com and contributors
// // For license information, please see license.txt

// // frappe.ui.form.on("Stocker Stock Entries", {
// // 	refresh(frm) {

// // 	},
// // });
// frappe.listview_settings['Stocker Stock Entries'] = {
//     onload: function(listview) {
//         listview.page.add_action_item(__('Create Stock Reconciliation'), function() {
//             let selected = listview.get_checked_items();

//             if (!selected.length) {
//                 frappe.msgprint(__('Please select at least one Stock Entry'));
//                 return;
//             }

//             frappe.call({
//                 method: "stocker.stocker.doctype.stocker_stock_entries.stocker_stock_entries.create_stock_reconciliation",
//                 args: {
//                     entries: selected
//                 },
//                 freeze: true,
//                 freeze_message: __("Creating Stock Reconciliation..."),
//                 callback: function(r) {
//                     if (!r.exc && r.message) {
//                         frappe.set_route("Form", "Stock Reconciliation", r.message);
//                     }
//                 }
//             });
//         });
//     }
// };
