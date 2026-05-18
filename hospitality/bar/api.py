"""
Bar API — called by the Windows Bar POS PyQt6 app.
All functions return plain dicts / lists (JSON-serialisable).
"""
import frappe
from frappe.utils import now_datetime, today, flt


# ─── Outlet & Menu ────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_outlets():
    return frappe.get_all(
        "Outlet",
        filters={"outlet_type": "Bar", "is_active": 1},
        fields=["name", "outlet_name", "pos_profile", "default_warehouse"],
    )


@frappe.whitelist()
def get_drink_categories(outlet):
    rows = frappe.db.sql("""
        SELECT DISTINCT category FROM `tabDrink Menu Item`
        WHERE outlet = %s AND is_active = 1
        ORDER BY category
    """, outlet, as_dict=True)
    return [r.category for r in rows if r.category]


@frappe.whitelist()
def get_drinks(outlet, category=None, search=None):
    filters = {"outlet": outlet, "is_active": 1}
    if category:
        filters["category"] = category
    items = frappe.get_all(
        "Drink Menu Item",
        filters=filters,
        fields=["name", "item_name", "category", "selling_price",
                "measure_ml", "description", "image", "is_happy_hour"],
        order_by="category, item_name",
    )
    if search:
        q = search.lower()
        items = [i for i in items if q in (i.item_name or "").lower()]
    return items


@frappe.whitelist()
def get_drink(drink_item):
    doc = frappe.get_doc("Drink Menu Item", drink_item)
    return {
        "name": doc.name,
        "item_name": doc.item_name,
        "category": doc.category,
        "selling_price": flt(doc.selling_price),
        "measure_ml": doc.measure_ml,
        "description": doc.description,
        "is_happy_hour": doc.is_happy_hour,
        "item_code": doc.item_code,
    }


# ─── Tabs ─────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_open_tabs(outlet):
    tabs = frappe.get_all(
        "Bar Tab",
        filters={"outlet": outlet, "status": "Open"},
        fields=["name", "tab_no", "tab_type", "guest", "guest_name",
                "total_amount", "bartender", "open_time"],
        order_by="open_time desc",
    )
    for tab in tabs:
        tab["order_count"] = frappe.db.count(
            "Bar Order",
            {"tab": tab.name, "docstatus": 1, "status": ["!=", "Cancelled"]},
        )
    return tabs


@frappe.whitelist()
def get_tab(tab):
    doc = frappe.get_doc("Bar Tab", tab)

    orders = frappe.get_all(
        "Bar Order",
        filters={"tab": tab, "docstatus": 1, "status": ["!=", "Cancelled"]},
        fields=["name", "order_time", "total_amount", "status"],
        order_by="order_time",
    )
    items = []
    for o in orders:
        order_items = frappe.get_all(
            "Bar Order Item",
            filters={"parent": o.name},
            fields=["drink_item", "qty", "rate", "amount",
                    "is_complimentary", "special_instructions"],
        )
        for i in order_items:
            i["item_name"] = frappe.db.get_value("Drink Menu Item", i.drink_item, "item_name")
        items.extend(order_items)

    return {
        "name": doc.name,
        "tab_no": doc.tab_no,
        "tab_type": doc.tab_type,
        "guest": doc.guest,
        "guest_name": doc.guest_name,
        "outlet": doc.outlet,
        "bartender": doc.bartender,
        "open_time": str(doc.open_time) if doc.open_time else None,
        "close_time": str(doc.close_time) if doc.close_time else None,
        "status": doc.status,
        "total_amount": flt(doc.total_amount),
        "pos_invoice": doc.pos_invoice,
        "items": items,
    }


@frappe.whitelist()
def open_tab(outlet, tab_type="Counter Tab", guest_name="Walk-in",
             guest=None, bartender=""):
    tab = frappe.get_doc({
        "doctype": "Bar Tab",
        "outlet": outlet,
        "tab_type": tab_type,
        "guest": guest or None,
        "guest_name": guest_name,
        "bartender": bartender,
        "open_time": now_datetime(),
        "status": "Open",
        "total_amount": 0,
    })
    tab.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"name": tab.name, "tab_no": tab.tab_no}


# ─── Orders ───────────────────────────────────────────────────────────────────

@frappe.whitelist()
def add_drink(tab, drink_item, qty=1, special_instructions="", is_complimentary=0):
    tab_doc = frappe.get_doc("Bar Tab", tab)
    if tab_doc.status != "Open":
        frappe.throw("Tab is not open.")

    di = frappe.get_doc("Drink Menu Item", drink_item)
    qty = flt(qty)
    is_compl = int(is_complimentary)
    line_amount = 0 if is_compl else qty * flt(di.selling_price or 0)

    order = frappe.get_doc({
        "doctype": "Bar Order",
        "outlet": tab_doc.outlet,
        "tab": tab,
        "order_time": now_datetime(),
        "status": "Pending",
        "items": [{
            "drink_item": drink_item,
            "qty": qty,
            "rate": flt(di.selling_price or 0),
            "amount": line_amount,
            "is_complimentary": is_compl,
            "special_instructions": special_instructions,
        }],
        "total_amount": line_amount,
    })
    order.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"order": order.name, "amount": line_amount}


@frappe.whitelist()
def add_round(tab, items):
    """
    Add multiple drinks at once (a round).
    items: JSON list of {drink_item, qty, special_instructions?, is_complimentary?}
    """
    if isinstance(items, str):
        import json
        items = json.loads(items)

    tab_doc = frappe.get_doc("Bar Tab", tab)
    if tab_doc.status != "Open":
        frappe.throw("Tab is not open.")

    line_items = []
    round_total = 0.0
    for it in items:
        di = frappe.get_doc("Drink Menu Item", it["drink_item"])
        qty = flt(it.get("qty", 1))
        is_compl = int(it.get("is_complimentary", 0))
        amount = 0 if is_compl else qty * flt(di.selling_price or 0)
        round_total += amount
        line_items.append({
            "drink_item": di.name,
            "qty": qty,
            "rate": flt(di.selling_price or 0),
            "amount": amount,
            "is_complimentary": is_compl,
            "special_instructions": it.get("special_instructions", ""),
        })

    order = frappe.get_doc({
        "doctype": "Bar Order",
        "outlet": tab_doc.outlet,
        "tab": tab,
        "order_time": now_datetime(),
        "status": "Pending",
        "items": line_items,
        "total_amount": round_total,
    })
    order.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"order": order.name, "total_amount": round_total, "items_count": len(line_items)}


@frappe.whitelist()
def fire_pending_orders(tab):
    """Submit all pending (draft) Bar Orders on this tab → creates BOT."""
    pending = frappe.get_all(
        "Bar Order",
        filters={"tab": tab, "status": "Pending", "docstatus": 0},
        fields=["name"],
    )
    fired = []
    for o in pending:
        doc = frappe.get_doc("Bar Order", o.name)
        doc.submit()
        fired.append(o.name)
    frappe.db.commit()
    return {"fired": fired, "count": len(fired)}


# ─── Settlement ───────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_tab_bill(tab):
    """Return a bill summary before settlement."""
    tab_doc = frappe.get_doc("Bar Tab", tab)
    orders = frappe.get_all(
        "Bar Order",
        filters={"tab": tab, "docstatus": 1, "status": ["!=", "Cancelled"]},
        fields=["name"],
    )
    lines = []
    subtotal = 0.0
    for o in orders:
        order_doc = frappe.get_doc("Bar Order", o.name)
        for item in order_doc.items:
            subtotal += flt(item.amount)
            lines.append({
                "item_name": frappe.db.get_value("Drink Menu Item", item.drink_item, "item_name"),
                "qty": flt(item.qty),
                "rate": flt(item.rate),
                "amount": flt(item.amount),
                "is_complimentary": item.is_complimentary,
            })
    return {
        "tab": tab,
        "guest_name": tab_doc.guest_name,
        "lines": lines,
        "subtotal": subtotal,
        "total_amount": flt(tab_doc.total_amount),
    }


@frappe.whitelist()
def settle_tab(tab, payment_method, tip=0):
    from hospitality.bar.page.bar_pos.bar_pos import close_tab_with_payment
    result = close_tab_with_payment(tab, payment_method, tip=flt(tip))
    return result


@frappe.whitelist()
def get_payment_modes():
    return frappe.get_all("Mode of Payment", fields=["name", "type"], order_by="name")


@frappe.whitelist()
def cancel_tab(tab, reason=""):
    tab_doc = frappe.get_doc("Bar Tab", tab)
    if tab_doc.status != "Open":
        frappe.throw("Tab is not open.")
    tab_doc.db_set("status", "Cancelled")
    tab_doc.db_set("close_time", now_datetime())
    frappe.db.commit()
    return {"status": "cancelled"}


# ─── Shift & Stock ────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_shift_summary(outlet, date=None):
    date = date or today()
    tabs = frappe.get_all(
        "Bar Tab",
        filters={"outlet": outlet, "status": ["in", ["Settled"]],
                 "open_time": [">=", date]},
        fields=["name", "total_amount", "bartender"],
    )
    total_revenue = sum(flt(t.total_amount) for t in tabs)
    return {
        "date": date,
        "settled_tabs": len(tabs),
        "total_revenue": total_revenue,
        "tabs": tabs,
    }


# ─── Dashboard ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_dashboard_stats(outlet):
    open_tabs = frappe.db.count("Bar Tab", {"outlet": outlet, "status": "Open"})
    settled_today = frappe.db.count(
        "Bar Tab",
        {"outlet": outlet, "status": "Settled", "open_time": [">=", today()]},
    )
    pending_bots = frappe.db.count(
        "Bar Order",
        {"outlet": outlet, "status": "Pending", "docstatus": 0},
    )
    revenue_today = frappe.db.sql("""
        SELECT IFNULL(SUM(total_amount), 0) FROM `tabBar Tab`
        WHERE outlet = %s AND status = 'Settled' AND DATE(open_time) = %s
    """, (outlet, today()))[0][0]

    return {
        "open_tabs": open_tabs,
        "settled_today": settled_today,
        "pending_bots": pending_bots,
        "revenue_today": flt(revenue_today),
    }
