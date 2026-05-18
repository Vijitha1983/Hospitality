import frappe
from frappe.utils import now_datetime, today, flt


@frappe.whitelist()
def get_bar_outlets():
    return frappe.get_all("Outlet",
        filters={"outlet_type": "Bar", "is_active": 1},
        fields=["name", "outlet_name", "pos_profile", "default_warehouse"])


@frappe.whitelist()
def get_open_tabs(outlet):
    tabs = frappe.get_all("Bar Tab",
        filters={"outlet": outlet, "status": "Open"},
        fields=["name", "tab_no", "tab_type", "guest", "guest_name", "total_amount",
                "bartender", "open_time"],
        order_by="open_time desc")
    for tab in tabs:
        tab["order_count"] = frappe.db.count("Bar Order",
            {"tab": tab.name, "docstatus": 1, "status": ["!=", "Cancelled"]})
    return tabs


@frappe.whitelist()
def get_drink_categories(outlet):
    rows = frappe.db.sql("""
        SELECT DISTINCT category FROM `tabDrink Menu Item`
        WHERE outlet = %s AND is_active = 1
        ORDER BY category
    """, outlet, as_dict=True)
    return [r.category for r in rows if r.category]


@frappe.whitelist()
def get_drink_items(outlet, category=None):
    filters = {"outlet": outlet, "is_active": 1}
    if category:
        filters["category"] = category
    return frappe.get_all("Drink Menu Item",
        filters=filters,
        fields=["name", "item_name", "category", "selling_price", "measure_ml",
                "description", "image", "is_happy_hour"],
        order_by="item_name")


@frappe.whitelist()
def open_tab(outlet, tab_type="Counter Tab", guest_name="Walk-in", guest=None):
    tab = frappe.get_doc({
        "doctype": "Bar Tab",
        "outlet": outlet,
        "tab_type": tab_type,
        "guest": guest or None,
        "guest_name": guest_name,
        "open_time": now_datetime(),
        "status": "Open",
        "total_amount": 0,
    })
    tab.insert(ignore_permissions=True)
    frappe.db.commit()
    return tab.name


@frappe.whitelist()
def get_tab_items(tab):
    orders = frappe.get_all("Bar Order",
        filters={"tab": tab, "docstatus": 1, "status": ["!=", "Cancelled"]},
        fields=["name", "total_amount", "status"])
    items = []
    for o in orders:
        order_items = frappe.get_all("Bar Order Item",
            filters={"parent": o.name},
            fields=["drink_item", "qty", "rate", "amount", "is_complimentary", "special_instructions"])
        items.extend(order_items)
    return items


@frappe.whitelist()
def add_drink_to_tab(tab, drink_item, qty=1, special_instructions="", is_complimentary=0):
    tab_doc = frappe.get_doc("Bar Tab", tab)
    if tab_doc.status != "Open":
        frappe.throw("Tab is not open.")

    outlet = tab_doc.outlet
    di = frappe.get_doc("Drink Menu Item", drink_item)

    # Create a new Bar Order for this drink
    order = frappe.get_doc({
        "doctype": "Bar Order",
        "outlet": outlet,
        "tab": tab,
        "order_time": now_datetime(),
        "status": "Pending",
        "items": [{
            "drink_item": drink_item,
            "qty": flt(qty),
            "rate": di.selling_price or 0,
            "amount": 0 if is_complimentary else flt(qty) * (di.selling_price or 0),
            "is_complimentary": is_complimentary,
            "special_instructions": special_instructions,
        }],
        "total_amount": 0 if is_complimentary else flt(qty) * (di.selling_price or 0),
    })
    order.insert(ignore_permissions=True)
    frappe.db.commit()
    return order.name


@frappe.whitelist()
def fire_bot(tab):
    pending_orders = frappe.get_all("Bar Order",
        filters={"tab": tab, "status": "Pending", "docstatus": 0},
        fields=["name"])
    fired = []
    for o in pending_orders:
        doc = frappe.get_doc("Bar Order", o.name)
        doc.submit()
        fired.append(o.name)
    frappe.db.commit()
    return {"fired": fired}


@frappe.whitelist()
def close_tab_with_payment(tab, payment_method, tip=0):
    tab_doc = frappe.get_doc("Bar Tab", tab)
    if tab_doc.status != "Open":
        frappe.throw("Tab is already closed.")

    # Fire any still-pending orders first
    fire_bot(tab)

    outlet = frappe.get_doc("Outlet", tab_doc.outlet)
    pos_profile = outlet.pos_profile
    if not pos_profile:
        frappe.throw(f"No POS Profile on outlet {tab_doc.outlet}.")

    customer = frappe.db.get_value("POS Profile", pos_profile, "customer") or "Walk-in Customer"

    orders = frappe.get_all("Bar Order",
        filters={"tab": tab, "docstatus": 1, "status": ["!=", "Cancelled"]},
        fields=["name"])

    line_items = []
    for o in orders:
        order_doc = frappe.get_doc("Bar Order", o.name)
        for item in order_doc.items:
            item_code = frappe.db.get_value("Drink Menu Item", item.drink_item, "item_code")
            if item_code:
                line_items.append({
                    "item_code": item_code,
                    "item_name": frappe.db.get_value("Drink Menu Item", item.drink_item, "item_name"),
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount,
                })

    if not line_items:
        frappe.throw("No billable items on this tab.")

    total = tab_doc.total_amount + flt(tip)
    invoice = frappe.get_doc({
        "doctype": "POS Invoice",
        "pos_profile": pos_profile,
        "customer": customer,
        "posting_date": today(),
        "items": line_items,
        "payments": [{"mode_of_payment": payment_method, "amount": total}],
    })
    invoice.insert(ignore_permissions=True)
    invoice.submit()

    tab_doc.db_set("pos_invoice", invoice.name)
    tab_doc.db_set("status", "Settled")
    tab_doc.db_set("close_time", now_datetime())
    frappe.db.commit()

    return {"invoice": invoice.name, "status": "settled"}


@frappe.whitelist()
def get_payment_modes():
    return frappe.get_all("Mode of Payment", fields=["name", "type"], order_by="name")


@frappe.whitelist()
def cancel_tab(tab, reason=""):
    tab_doc = frappe.get_doc("Bar Tab", tab)
    tab_doc.db_set("status", "Cancelled")
    frappe.db.commit()
    return {"status": "cancelled"}
