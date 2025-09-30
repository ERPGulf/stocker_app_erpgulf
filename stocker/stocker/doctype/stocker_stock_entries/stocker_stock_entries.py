# Copyright (c) 2025, asithara@htsqatar.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class StockerStockEntries(Document):
	pass
import json
from frappe.utils import getdate, get_time, flt
import frappe
from frappe.utils.data import add_to_date, get_time, getdate
from frappe.utils import flt, now_datetime
@frappe.whitelist()

def create_stock_reconciliation(entries):


    entries = json.loads(entries)
    grouped_entries = {}


    for entry in entries:
        if isinstance(entry, dict):
            entry = entry.get("name")

        se_doc = frappe.get_doc("Stocker Stock Entries", entry)
        item_code = frappe.db.get_value("Item", {"name": se_doc.item_code}, "name")
        date_only = getdate(se_doc.date)
        time_only = get_time(se_doc.date)

        bin_val_rate = frappe.db.sql("""
            SELECT valuation_rate
            FROM `tabBin`
            WHERE item_code = %s AND warehouse = %s AND actual_qty > 0
            LIMIT 1
        """, (item_code, se_doc.warehouse))

        if bin_val_rate:
            bin_val_rate = bin_val_rate[0][0]
        else:

            bin_val_rate = frappe.db.sql("""
                SELECT valuation_rate
                FROM `tabBin`
                WHERE item_code = %s AND actual_qty > 0
                ORDER BY creation DESC
                LIMIT 1
            """, (item_code,))

            bin_val_rate = bin_val_rate[0][0] if bin_val_rate else None


        if not bin_val_rate:
            last_purchase_rate = frappe.db.get_value("Item", item_code, "last_purchase_rate")



        if not bin_val_rate and not last_purchase_rate:
            frappe.log_error(f"Skipping {item_code} in {se_doc.warehouse}: no valuation rate found.", "Stock Reconciliation")
            continue

        uom1, qty1 = normalize_to_default_uom(item_code, se_doc.uom, se_doc.qty)
        valuation_rate = bin_val_rate or frappe.db.get_value("Item", item_code, "last_purchase_rate") or 0

        key = (item_code, se_doc.warehouse, date_only, time_only)

        if key not in grouped_entries:
            grouped_entries[key] = {
                "item_code": item_code,
                "warehouse": se_doc.warehouse,
                "qty": 0,
                "valuation_rate": valuation_rate,
                "barcode": se_doc.barcode,
                "custom_stocker_id": [],
                "date": date_only,
                "time": time_only,
            }

        grouped_entries[key]["qty"] += qty1
        grouped_entries[key]["custom_stocker_id"].append(se_doc.name)

    created_reconciliations = []


    for key, data in grouped_entries.items():
        recon_doc = frappe.get_doc({
            "doctype": "Stock Reconciliation",
            "purpose": "Stock Reconciliation",
            "naming_series":"STK-.YY..MM.-",
            "posting_date": data["date"],
            "posting_time": data["time"],
            "set_warehouse": data["warehouse"],
            "set_posting_time": 1,
            "items": [{
                "item_code": data["item_code"],
                "warehouse": data["warehouse"],
                "qty": data["qty"],
                "valuation_rate": flt(data["valuation_rate"]),
                "barcode": data["barcode"],


            }]
        })

        try:
            recon_doc.insert(ignore_permissions=True)
            recon_doc.submit()
            created_reconciliations.append(recon_doc.name)

            for se_name in data["custom_stocker_id"]:
                frappe.db.set_value("Stocker Stock Entries", se_name, "stock_reconciliation", 1)

        except Exception as e:
            err_msg = str(e)

            if "None of the items have any change in quantity or value" in err_msg:
                frappe.log_error(
                    f"Skipping reconciliation for {data['item_code']} in {data['warehouse']}: {err_msg}",
                    "Stock Reconciliation"
                )
                continue
            else:

                raise

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

