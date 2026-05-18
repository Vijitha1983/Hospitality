import frappe
from frappe.utils import now_datetime, today, flt


@frappe.whitelist()
def get_outlets():
    return frappe.get_all("Outlet",
        filters={"outlet_type": ["in", ["Restaurant", "Cafe", "Room Service"]], "is_active": 1},
        fields=["name", "outlet_name", "outlet_type", "pos_profile", "default_warehouse", "tax_template"])


@frappe.whitelist()
def get_tables(outlet):
    return frappe.get_all("Dining Table",
        filters={"outlet": outlet, "is_active": 1},
        fields=["name", "table_number", "seating_capacity", "current_status", "current_order", "pos_x", "pos_y"],
        order_by="table_number")


@frappe.whitelist()
def get_menu_categories(outlet):
    items = frappe.db.sql("""
        SELECT DISTINCT category FROM `tabMenu Item`
        WHERE outlet = %s AND is_active = 1
        ORDER BY category
    """, outlet, as_dict=True)
    return [r.category for r in items if r.category]


@frappe.whitelist()
def get_menu_items(outlet, category=None):
    filters = {"outlet": outlet, "is_active": 1}
    if category:
        filters["category"] = category
    return frappe.get_all("Menu Item",
        filters=filters,
        fields=["name", "item_name", "category", "selling_price", "food_cost",
                "kitchen_station", "description", "image", "is_available"],
        order_by="item_name")


@frappe.whitelist()
def get_active_order(table):
    order = frappe.db.get_value("Restaurant Order",
        {"table": table, "status": ["in", ["Open", "KOT Sent", "Partially Served"]]},
        ["name", "status", "sub_total", "tax_amount", "total_amount", "num_covers"],
        as_dict=True)
    if not order:
        return None
    order["items"] = frappe.get_all("KOT Item",
        filters={"parent": order.name},
        fields=["name", "menu_item", "item_name", "qty", "rate", "amount", "status", "special_instructions"])
    return order


@frappe.whitelist()
def new_order(outlet, table, covers=1):
    existing = frappe.db.get_value("Restaurant Order",
        {"table": table, "status": ["in", ["Open", "KOT Sent", "Partially Served"]]}, "name")
    if existing:
        return existing
    order = frappe.get_doc({
        "doctype": "Restaurant Order",
        "outlet": outlet,
        "table": table,
        "num_covers": covers,
        "order_time": now_datetime(),
        "status": "Open",
        "items": [],
    })
    order.insert(ignore_permissions=True)
    frappe.db.commit()
    return order.name


@frappe.whitelist()
def add_item(order, menu_item, qty=1, special_instructions=""):
    doc = frappe.get_doc("Restaurant Order", order)
    mi = frappe.get_doc("Menu Item", menu_item)
    # Check if item already exists (non-KOT-sent)
    for row in doc.items:
        if row.menu_item == menu_item and row.status == "Pending":
            row.qty += flt(qty)
            row.amount = row.qty * row.rate
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            return order
    doc.append("items", {
        "menu_item": menu_item,
        "item_name": mi.item_name,
        "qty": flt(qty),
        "rate": mi.selling_price or 0,
        "amount": flt(qty) * (mi.selling_price or 0),
        "special_instructions": special_instructions,
        "status": "Pending",
    })
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return order


@frappe.whitelist()
def remove_item(order, row_name):
    doc = frappe.get_doc("Restaurant Order", order)
    doc.items = [r for r in doc.items if r.name != row_name]
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return order


@frappe.whitelist()
def update_qty(order, row_name, qty):
    doc = frappe.get_doc("Restaurant Order", order)
    for row in doc.items:
        if row.name == row_name:
            if flt(qty) <= 0:
                doc.items.remove(row)
            else:
                row.qty = flt(qty)
                row.amount = row.qty * row.rate
            break
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return order


@frappe.whitelist()
def fire_kot(order):
    doc = frappe.get_doc("Restaurant Order", order)
    if doc.docstatus == 0:
        doc.submit()
        frappe.db.commit()
    return {"status": "ok", "order": order}


@frappe.whitelist()
def process_payment(order, amount, payment_method, tip=0):
    doc = frappe.get_doc("Restaurant Order", order)
    if doc.docstatus != 1:
        frappe.throw("Order must be submitted (KOT fired) before billing.")

    outlet = frappe.get_doc("Outlet", doc.outlet)
    pos_profile = outlet.pos_profile
    if not pos_profile:
        frappe.throw(f"No POS Profile on Outlet {doc.outlet}")

    customer = frappe.db.get_value("POS Profile", pos_profile, "customer") or "Walk-in Customer"

    invoice = frappe.get_doc({
        "doctype": "POS Invoice",
        "pos_profile": pos_profile,
        "customer": customer,
        "posting_date": today(),
        "items": [
            {
                "item_code": frappe.db.get_value("Menu Item", i.menu_item, "item_code") or i.menu_item,
                "item_name": i.item_name,
                "qty": i.qty,
                "rate": i.rate,
                "amount": i.amount,
            }
            for i in doc.items if i.status != "Void"
        ],
        "payments": [
            {"mode_of_payment": payment_method, "amount": flt(amount) + flt(tip)}
        ],
    })
    invoice.insert(ignore_permissions=True)
    invoice.submit()

    doc.db_set("pos_invoice", invoice.name)
    doc.db_set("status", "Billed")

    # Free the table
    frappe.db.set_value("Dining Table", doc.table, "current_status", "Dirty")
    frappe.db.set_value("Dining Table", doc.table, "current_order", None)
    frappe.db.commit()

    return {"invoice": invoice.name, "status": "billed"}


@frappe.whitelist()
def get_payment_modes():
    return frappe.get_all("Mode of Payment", fields=["name", "type"], order_by="name")


@frappe.whitelist()
def void_order(order, reason=""):
    doc = frappe.get_doc("Restaurant Order", order)
    if doc.docstatus == 1:
        doc.cancel()
    else:
        doc.delete()
    frappe.db.set_value("Dining Table", doc.table, "current_status", "Available")
    frappe.db.set_value("Dining Table", doc.table, "current_order", None)
    frappe.db.commit()
    return {"status": "voided"}
