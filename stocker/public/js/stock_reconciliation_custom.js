frappe.ui.form.on('Stock Reconciliation', {
    refresh(frm) {
        frm.add_custom_button(__('Stocker Stock Entries'), () => {
            let d = new frappe.ui.form.MultiSelectDialog({
                doctype: "Stocker Stock Entries",
                target: frm,
                setters: {
                    warehouse: frm.doc.set_warehouse || undefined,
                    employee:frm.doc.employee ||undefined,
                    branch :frm.doc.branch || undefined,
                    date :frm.doc.date || undefined,
                    shelf: frm.doc.shelf ||undefined,
                    item_code: frm.doc.item_code|| undefined

                },
                add_filters_group: 1,
                get_query() {
                    return {
                        filters: {
                            stock_reconciliation: 0
                        }
                    };
                },
                action(selections) {
                    if (selections.length) {
                        frappe.call({
                            method: "stocker.stocker.api.make_stock_entry",
                            args: {
                                source_name: JSON.stringify(selections)
                            },
                            callback(r) {
                                if (r.message) {
                                    let first = r.message[0];
                                    frm.set_value("set_posting_time", 1);
                                    if (first.posting_date) frm.set_value("posting_date", first.posting_date);
                                    if (first.posting_time) frm.set_value("posting_time", first.posting_time);
                                    if (first.warehouse) frm.set_value("set_warehouse", first.warehouse);
                                    r.message.forEach(d => {
                                        let empty_row = frm.doc.items.find(i => !i.item_code);
                                        let row = empty_row || frm.add_child("items");
                                        row.item_code = d.item_code;
                                        row.warehouse = d.warehouse;
                                        row.uom = d.uom;
                                        row.qty = d.qty;
                                        row.barcode = d.barcode;
                                        row.shelf = d.shelf;
                                        row.valuation_rate = d.valuation_rate;
                                        row.custom_stocker_id = d.custom_stocker_id;

                                    });
                                    frm.refresh_field("items");

                                    d.dialog.hide();
                                }
                            }
                        });
                    }
                }
            });
        }, __("Get Items From"));
    }
});


