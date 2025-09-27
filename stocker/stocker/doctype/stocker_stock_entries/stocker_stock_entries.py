# Copyright (c) 2025, asithara@htsqatar.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class StockerStockEntries(Document):
	pass
import json
import frappe
from frappe.utils.data import add_to_date, get_time, getdate
from frappe.utils import flt, now_datetime
@frappe.whitelist()
def create_stock_reconciliation(entries):

    entries = json.loads(entries)

    created_reconciliations = []
    for entry in entries:
        if isinstance(entry, dict):
            entry = entry.get("name")

        se_doc = frappe.get_doc("Stocker Stock Entries", entry)
        item_code = frappe.db.get_value("Item", {"name": se_doc.item_code}, "name")

        date_only = getdate(se_doc.date)
        time_only = get_time(se_doc.date)
        bin_val_rate = frappe.db.get_value(
        "Bin",
        {"item_code": item_code, "warehouse": se_doc.warehouse},
        "valuation_rate")


        uom1, qty1 = normalize_to_default_uom(item_code,se_doc.uom, se_doc.qty)
        if not bin_val_rate:
            last_purchase_rate = frappe.db.get_value("Item", item_code, "last_purchase_rate")

        recon_doc = frappe.get_doc({
            "doctype": "Stock Reconciliation",
            "purpose": "Stock Reconciliation",
            "posting_date": date_only,
            "posting_time": time_only,
            "set_posting_time":1,
            "items": [{
                "item_code": se_doc.item_code,
                "warehouse": se_doc.warehouse,
                "qty": qty1,
                "valuation_rate": flt(last_purchase_rate) if not bin_val_rate else bin_val_rate,
                "barcode": se_doc.barcode,
                "custom_stocker_id":se_doc.name
            }]
        })

        recon_doc.insert(ignore_permissions=True)
        recon_doc.submit()
        created_reconciliations.append(recon_doc.name)
        if recon_doc:
                frappe.db.set_value(
                    "Stocker Stock Entries",se_doc.name,"stock_reconciliation",1
                )

    return ", ".join(created_reconciliations)




def normalize_to_default_uom(item_code, uom, qty):
    qty = flt(qty)

    default_uom = frappe.db.get_value("Item", item_code, "stock_uom")
    if not default_uom or not uom or uom == default_uom:
        return uom, qty


    conversion_factor = frappe.db.get_value(
        "UOM Conversion Detail",
        {"parent": item_code, "uom": uom},
        "conversion_factor"
    )

    if not conversion_factor:
        frappe.throw(
            f"Conversion factor for UOM {uom} not defined for Item {item_code}"
        )


    new_qty = qty * flt(conversion_factor)
    return default_uom, new_qty

