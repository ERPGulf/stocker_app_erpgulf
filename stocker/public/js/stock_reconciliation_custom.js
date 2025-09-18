frappe.ui.form.on('Stock Reconciliation', {
    refresh(frm) {
        frm.add_custom_button(__('Stocker Stock Entries'), () => {
            let d = new frappe.ui.form.MultiSelectDialog({
                doctype: "Stocker Stock Entries",
                target: frm,
                setters: {
                    warehouse: frm.doc.set_warehouse || undefined
                },
                add_filters_group: 1,
                get_query() {
                    return {
                        filters: {}
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
                                    r.message.forEach(d => {
                                        let empty_row = frm.doc.items.find(i => !i.item_code);
                                        let row = empty_row || frm.add_child("items");
                                        row.item_code = d.item_code;
                                        row.warehouse = d.warehouse;
                                        row.uom = d.uom;
                                        row.qty = d.qty;
                                        row.barcode = d.barcode;
                                        // row.shelf = d.shelf;
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
