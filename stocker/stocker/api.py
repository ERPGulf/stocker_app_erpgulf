import frappe
import json
from werkzeug.wrappers import Response, Request
from erpnext.stock.utils import get_stock_balance
import base64
from datetime import datetime, timedelta
from frappe.utils import now_datetime

from frappe import _
from frappe.utils.data import add_to_date, get_time, getdate
from erpnext import get_region
from pyqrcode import create as qr_create
from base64 import b64encode
import io
import os
from base64 import b64encode
@frappe.whitelist()
def warehouse_list(warehouse=None):
    """
    Returns a list of warehouses.
    """
    try:
        if warehouse:
            warehouse_list = frappe.get_all(
                "Warehouse",
                fields=[
                    "name as warehouse_id",
                    "warehouse_name",
                ],
                filters={"name": warehouse},
            )
        else:
            warehouse_list = frappe.get_all(
                "Warehouse",
                fields=[
                    "name as warehouse_id",
                    "warehouse_name"
                ],
            )

        return Response(
            json.dumps({"data": warehouse_list}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist()
def get_items(barcode,warehouse):
    try:
        barcode_doc = frappe.get_value(
            "Item Barcode",
            {"barcode": barcode},
            ["parent", "uom"],
            as_dict=True
        )

        if not barcode_doc:
            return Response(
                json.dumps({"error": "No item found for given barcode"}),
                status=404,
                mimetype="application/json"
            )

        item_code = barcode_doc.parent
        uom = barcode_doc.uom

        item = frappe.get_value(
            "Item",
            item_code,
            ["name", "item_code", "item_name"],
            as_dict=True
        )


        total_qty = frappe.db.sql("""
        SELECT COALESCE(SUM(actual_qty), 0)
        FROM `tabBin`
        WHERE item_code = %s AND warehouse = %s
    """, (item_code, warehouse))[0][0]


        # shelf_data = frappe.db.sql("""
        #     SELECT shelf, SUM(actual_qty) as qty
        #     FROM `tabStock Ledger Entry`
        #     WHERE item_code = %s
        #     GROUP BY shelf
        # """, (item_code,), as_dict=True)

        result = {
            "item_id": item.name,
            "item_name": item.item_name,
            "uom": uom,
            "total_qty": total_qty,
            "shelf_qty":total_qty
        }

        return Response(
            json.dumps({"data": result}, default=str),
            status=200,
            mimetype="application/json"
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_items (barcode) API Error")
        return Response(
            json.dumps({"error": str(e) or "Unknown error"}),
            status=500,
            mimetype="application/json"
        )



@frappe.whitelist()

def create_stock_entry(item_id, date_time, warehouse, barcode, uom, qty,employee,shelf=None):
    try:
        doc = frappe.get_doc({
            "doctype": "Stocker Stock Entries",
            "warehouse": warehouse,
            "barcode": barcode,
            "shelf": shelf,
            "date": date_time,
            "item_code": item_id,
            "uom": uom,
            "qty": qty,
            "employee":employee
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()


        data={
            "status": "success",
            "id": doc.name,
            "item_code": doc.item_code,
            "warehouse": doc.warehouse,
            "shelf": doc.shelf,
            "barcode": doc.barcode,
            "uom": doc.uom,
            "qty": doc.qty,
            "date": doc.date,
            "employee":doc.employee
        }
        return Response(
                json.dumps({"data":data}),
                status=200,
                mimetype="application/json"
            )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_stock_entry Error")
        return Response(
                    json.dumps({e}),
                    status=500,
                    mimetype="application/json"
                )





from datetime import date

@frappe.whitelist()
def list_stock_entries(warehouse=None, item_code=None, today_only=False):
    """
    Returns a list of Warehouse Stock Log entries, optionally filtered by warehouse, item_code, and today's date.
    """


    try:
        filters = {}
        if warehouse:
            filters["warehouse"] = warehouse
        if item_code:
            filters["item_code"] = item_code
        if today_only:

            start = datetime.combine(date.today(), datetime.min.time())
            end = datetime.combine(date.today(), datetime.max.time())
            filters["date"] = ["between", [start, end]]

        stock_entries = frappe.get_all(
            "Stocker Stock Entries",
            filters=filters,
            fields=[
                "name as entry_id",
                "warehouse",
                "item_code",
                "barcode",
                "shelf",
                "uom",
                "qty",
                "date"
            ],
            order_by="date desc"
        )

        return Response(
            json.dumps({"data": stock_entries}, default=str),
            status=200,
            mimetype="application/json"
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "list_stock_entries API Error")
        return Response(
            json.dumps({"error": str(e) or "Unknown error"}),
            status=500,
            mimetype="application/json"
        )





@frappe.whitelist()
def update_stock_entry(entry_id, warehouse=None, barcode=None, shelf=None, date=None, item_code=None, uom=None, qty=None):
    """
    Updates a Warehouse Stock Log entry by entry_id.
    """
    try:
        doc = frappe.get_doc("Stocker Stock Entries", entry_id)
        if warehouse is not None:
            doc.warehouse = warehouse
        if barcode is not None:
            doc.barcode = barcode
        if shelf is not None:
            doc.shelf = shelf
        if date is not None:
            doc.date = date
        if item_code is not None:
            doc.item_code = item_code
        if uom is not None:
            doc.uom = uom
        if qty is not None:
            doc.qty = qty

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        data = {
            "status": "success",
            "entry_id": doc.name,
            "warehouse": doc.warehouse,
            "barcode": doc.barcode,
            "shelf": doc.shelf,
            "date": doc.date,
            "item_code": doc.item_code,
            "uom": doc.uom,
            "qty": int(doc.qty)
        }
        return Response(
            json.dumps({"data": data}, default=str),
            status=200,
            mimetype="application/json"
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "update_stock_entry API Error")
        return Response(
            json.dumps({"error": str(e) or "Unknown error"}),
            status=500,
            mimetype="application/json"
        )





@frappe.whitelist()
def delete_stock_entry(entry_id):
    """
    Deletes a Warehouse Stock Log entry by entry_id.
    """
    try:
        frappe.delete_doc("Stocker Stock Entries", entry_id, ignore_permissions=True)
        frappe.db.commit()
        return Response(
            json.dumps({"status": "success", "message": f"Entry {entry_id} deleted"}),
            status=200,
            mimetype="application/json"
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "delete_stock_entry API Error")
        return Response(
            json.dumps({"error": str(e) or "Unknown error"}),
            status=500,
            mimetype="application/json"
        )




@frappe.whitelist()
def list_items(item_group=None, last_updated_time=None, pos_profile = None):


    try:
        fields = ["name", "stock_uom", "item_name", "item_group", "description", "modified","disabled"]
        # filters = {"item_group": ["like", f"%{item_group}%"]} if item_group else {}
        item_filters = {}
        if item_group:
            item_filters["item_group"] = ["like", f"%{item_group}%"]

        item_codes_set = set()

        if last_updated_time:
            try:
                last_updated_dt = datetime.strptime(last_updated_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return Response(
                    json.dumps(
                        {"error": "Invalid datetime format. Use YYYY-MM-DD HH:MM:SS"}
                    ),
                    status=400,
                    mimetype="application/json",
                )


            modified_item_filters = item_filters.copy()
            modified_item_filters["modified"] = [">", last_updated_dt]

            modified_items = frappe.get_all(
                "Item", fields=["name"], filters=modified_item_filters
            )
            item_codes_set.update([item["name"] for item in modified_items])


            price_items = frappe.get_all(
                "Item Price",
                fields=["item_code"],
                filters={"modified": [">", last_updated_dt]},
            )
            item_codes_set.update([p["item_code"] for p in price_items])

            if not item_codes_set:
                return Response(
                    json.dumps({"data": []}), status=200, mimetype="application/json"
                )

            item_filters["name"] = ["in", list(item_codes_set)]

        items = frappe.get_all("Item", fields=fields, filters=item_filters)
        item_meta = frappe.get_meta("Item")
        has_arabic = "custom_item_name_arabic" in [df.fieldname for df in item_meta.fields]
        has_english = "custom_item_name_in_english" in [
            df.fieldname for df in item_meta.fields
        ]

        grouped_items = {}

        for item in items:

            if item.disabled == 1:
                continue

            item_group_disabled = frappe.db.get_value(
                "Item Group", item.item_group, "custom_disabled"
            )


            if item.item_group not in grouped_items:
                grouped_items[item.item_group] = {
                    "item_group_id": item.item_group,
                    "item_group": item.item_group,
                    "item_group_disabled": bool(item_group_disabled),
                    "items": [] if not item_group_disabled else [],
                }

            if not item_group_disabled:
                item_doc = frappe.get_doc("Item", item.name)


                item_name_arabic = ""
                item_name_english = ""

                if has_arabic and item_doc.get("custom_item_name_arabic"):
                    item_name_arabic = item_doc.custom_item_name_arabic
                    item_name_english = item.item_name
                elif has_english and item_doc.get("custom_item_name_in_english"):
                    item_name_arabic = item.item_name
                    item_name_english = item_doc.custom_item_name_in_english

                uoms = frappe.get_all(
                    "UOM Conversion Detail",
                    filters={"parent": item.name},
                    fields=["name", "uom", "conversion_factor"],
                )

                barcodes = frappe.get_all(
                    "Item Barcode",
                    filters={"parent": item.name},
                    fields=["name", "barcode", "uom", "custom_editable_price", "custom_editable_quantity"],
                )

                price_list = "Retail Price"
                if pos_profile:
                    price_list = frappe.db.get_value(
                        "POS Profile", pos_profile, "selling_price_list"
                    ) or "Retail Price"

                item_prices = frappe.get_all(
                    "Item Price",
                    fields=["price_list_rate", "uom", "creation"],
                    filters={"item_code": item.name, "price_list": price_list},
                    order_by="creation",
                )

                price_map = {price.uom: price.price_list_rate for price in item_prices}
                barcode_map = {}
                for barcode in barcodes:
                    if barcode.uom in barcode_map:
                        barcode_map[barcode.uom].append(barcode.barcode)
                    else:
                        barcode_map[barcode.uom] = [barcode.barcode]

                grouped_items[item.item_group]["items"].append(
                    {
                        "item_id": item.name,
                        "item_code": item.name,
                        "item_name": item.item_name,
                        "item_name_english": item_name_english,
                        "item_name_arabic": item_name_arabic,
                        "tax_percentage": (item.get("custom_tax_percentage") or 0.0),
                        "description": item.description,
                        "barcodes": [
                            {
                                "id": barcode.name,
                                "barcode": barcode.barcode,
                                "uom": barcode.uom,
                            }
                            for barcode in barcodes
                        ],
                        "uom": [
                            {
                                "id": uom.name,
                                "uom": uom.uom,
                                "conversion_factor": uom.conversion_factor,
                                "price": round(price_map.get(uom.uom, 0.0), 2),
                                "barcode": ", ".join(barcode_map.get(uom.uom, [])),
                                "editable_price": bool(
                                    frappe.get_value("UOM", uom.uom, "custom_editable_price")
                                ),
                                "editable_quantity": bool(
                                    frappe.get_value("UOM", uom.uom, "custom_editable_quantity")
                                ),
                            }
                            for uom in uoms
                        ],
                    }
                )
        result = list(grouped_items.values())


        if not result:
            return Response(
            json.dumps({"error": "No items found"}),
            status=404,
            mimetype="application/json"
        )

        return Response(
            json.dumps({"data": result}),
            status=200,
            mimetype="application/json"
        )
    except Exception as e:
        return Response(
            json.dumps({"error":e}),
            status=404,
            mimetype="application/json"
        )


def create_qr_code(doc, method):
    """Create QR Code after inserting Sales Inv"""

    # If QR Code field not present, do nothing
    if not hasattr(doc, 'custom_qr_code'):
        return

    fields = frappe.get_meta('Employee').fields

    for field in fields:
        if field.fieldname == 'custom_qr_code' and field.fieldtype == 'Attach Image':
            # Creating QR code for the Sales Invoice
            ''' TLV conversion for
            1. Seller's Name
            2. VAT Number
            3. Time Stamp
            4. Invoice Amount
            5. VAT Amount
            '''
            tlv_array = []

            company_name = "Company: " + frappe.db.get_value('Company', doc.company, 'company_name')
            if not company_name:
                frappe.throw(_('Company name missing for {} in the company document'.format(doc.company)))

            tag = bytes([1]).hex()
            length = bytes([len(company_name.encode('utf-8'))]).hex()
            value = company_name.encode('utf-8').hex()
            tlv_array.append(''.join([tag, length, value]))

            user_name = "Employee_Code: " + str(doc.name)
            if not user_name:
                frappe.throw(_('Employee name missing for {} in the document'))

            tag = bytes([1]).hex()
            length = bytes([len(user_name.encode('utf-8'))]).hex()
            value = user_name.encode('utf-8').hex()
            tlv_array.append(''.join([tag, length, value]))

            full_name = "Full_Name: " + str(doc.first_name + "  " + doc.last_name)
            tag = bytes([1]).hex()
            length = bytes([len(full_name.encode('utf-8'))]).hex()
            value = full_name.encode('utf-8').hex()
            tlv_array.append(''.join([tag, length, value]))

            full_name = "User_id: " + str(doc.user_id)
            tag = bytes([1]).hex()
            length = bytes([len(full_name.encode('utf-8'))]).hex()
            value = full_name.encode('utf-8').hex()
            tlv_array.append(''.join([tag, length, value]))

            api_url = "API: " + frappe.utils.get_host_name() + "/api/"


            if not api_url:
                frappe.throw(_('API URL is missing for {} in the document'))

            tag = bytes([1]).hex()
            length = bytes([len(api_url.encode('utf-8'))]).hex()
            value = api_url.encode('utf-8').hex()
            tlv_array.append(''.join([tag, length, value]))

            tlv_buff = ''.join(tlv_array)

            base64_string = b64encode(bytes.fromhex(tlv_buff)).decode()


            qr_image = io.BytesIO()
            url = qr_create(base64_string, error='L')
            url.png(qr_image, scale=2, quiet_zone=1)

            filename = f"QR-CODE-{doc.name}.png".replace(os.path.sep, "__")
            print(filename)

            _file = frappe.get_doc({
                "doctype": "File",
                "file_name": filename,
                "content": qr_image.getvalue(),
                "is_private": 0
            })

            _file.save()

            doc.db_set('image', _file.file_url)
            # doc.db_set('custom_qr_data', base64_string)

            doc.notify_update()

            break


from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_stock_entry(source_name, filters=None):
    import json

    if isinstance(source_name, str):
        source_name = json.loads(source_name)

    if isinstance(filters, str):
        filters = json.loads(filters)

    items = []


    if filters:
        docs = frappe.get_list(
            "Stocker Stock Entries",
            filters=filters,
            fields=["name", "item_code", "warehouse", "uom", "qty", "barcode", "shelf"]
        )
        for d in docs:
            items.append(d)
    else:
        for name in source_name:
            doc = frappe.get_doc("Stocker Stock Entries", name)
            items.append({
                "item_code": doc.item_code,
                "warehouse": doc.warehouse,
                "uom": doc.uom,
                "qty": doc.qty,
                "barcode": getattr(doc, "barcode", None),
                "shelf": getattr(doc, "shelf", None),
            })

    return items
