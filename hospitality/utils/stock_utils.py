import frappe
from frappe.utils import today, now_datetime


def create_material_issue(items, warehouse, company, reference_doc, reference_type):
    """
    Create a Stock Entry (Material Issue) for consumed ingredients.
    items: list of dicts with {item_code, qty, uom}
    """
    if not items:
        return None

    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Issue",
        "posting_date": today(),
        "posting_time": now_datetime().strftime("%H:%M:%S"),
        "company": company,
        "from_warehouse": warehouse,
        "remarks": f"Auto-issued for {reference_type} {reference_doc}",
    })

    for item in items:
        se.append("items", {
            "item_code": item["item_code"],
            "qty": item["qty"],
            "uom": item.get("uom", "Nos"),
            "s_warehouse": warehouse,
        })

    se.insert(ignore_permissions=True)
    se.submit()
    return se


def get_bom_items(bom_name, qty=1):
    """
    Explode a BOM and return items with quantities scaled to qty.
    """
    bom_items = frappe.get_all(
        "BOM Item",
        filters={"parent": bom_name},
        fields=["item_code", "qty", "uom", "stock_qty"]
    )
    result = []
    for item in bom_items:
        result.append({
            "item_code": item.item_code,
            "qty": item.stock_qty * qty,
            "uom": item.uom,
        })
    return result


def check_par_level_and_create_po(outlet, items):
    """
    Check if any item is below par level and create a draft Purchase Order.
    items: list of dicts {item_code, closing_qty, par_level, supplier}
    """
    po_items = [i for i in items if (i.get("closing_qty") or 0) < (i.get("par_level") or 0)]
    if not po_items:
        return None

    settings = frappe.get_single("Hospitality Settings")
    po = frappe.get_doc({
        "doctype": "Purchase Order",
        "company": settings.company,
        "transaction_date": today(),
        "schedule_date": frappe.utils.add_days(today(), 2),
        "remarks": f"Auto-generated: par level breach for outlet {outlet}",
    })

    supplier = po_items[0].get("supplier") or frappe.db.get_value("Item Default",
        {"parent": po_items[0]["item_code"]}, "default_supplier")

    po.supplier = supplier or frappe.throw("No supplier configured for reorder items.")

    for item in po_items:
        reorder_qty = (item.get("par_level") or 0) - (item.get("closing_qty") or 0)
        po.append("items", {
            "item_code": item["item_code"],
            "qty": reorder_qty,
            "schedule_date": frappe.utils.add_days(today(), 2),
        })

    po.insert(ignore_permissions=True)
    frappe.msgprint(f"Draft Purchase Order {po.name} created for below-par items.", indicator="orange")
    return po
