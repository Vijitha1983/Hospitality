"""
Restaurant API — called by the Windows Restaurant POS and Mobile Table Order apps.
All functions return plain dicts / lists (JSON-serialisable).
"""
import frappe
from frappe.utils import now_datetime, today, flt


# ─── Outlet & Menu ────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_outlets():
    return frappe.get_all(
        "Outlet",
        filters={"outlet_type": "Restaurant", "is_active": 1},
        fields=["name", "outlet_name", "pos_profile", "default_warehouse"],
    )


@frappe.whitelist()
def get_menu_categories(outlet):
    rows = frappe.db.sql("""
        SELECT DISTINCT mi.category
        FROM `tabMenu Item` mi
        JOIN `tabFood Menu` fm ON fm.name = mi.parent
        WHERE fm.outlet = %s AND fm.is_active = 1
        ORDER BY mi.category
    """, outlet, as_dict=True)
    return [r.category for r in rows if r.category]


@frappe.whitelist()
def get_menu_items(outlet, category=None):
    filters = {"is_active": 1}
    if category:
        filters["category"] = category

    menus = frappe.get_all(
        "Food Menu",
        filters={"outlet": outlet, "is_active": 1},
        fields=["name"],
    )
    if not menus:
        return []

    menu_names = [m.name for m in menus]
    items = frappe.get_all(
        "Menu Item",
        filters={"parent": ["in", menu_names], **filters},
        fields=["name", "item_name", "category", "selling_price", "description",
                "image", "kitchen_station", "is_available", "course"],
        order_by="category, item_name",
    )
    return items


@frappe.whitelist()
def get_menu_item(menu_item):
    doc = frappe.get_doc("Menu Item", menu_item)
    return doc.as_dict()


# ─── Tables ───────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_tables(outlet, section=None):
    filters = {"outlet": outlet}
    if section:
        filters["section"] = section
    tables = frappe.get_all(
        "Dining Table",
        filters=filters,
        fields=["name", "table_number", "section", "capacity", "status", "active_order"],
        order_by="section, table_number",
    )
    return tables


@frappe.whitelist()
def get_table_sections(outlet):
    return frappe.get_all(
        "Table Section",
        filters={"outlet": outlet, "is_active": 1},
        fields=["name", "section_name"],
    )


# ─── Reservations ─────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_reservations(outlet, date=None):
    date = date or today()
    return frappe.get_all(
        "Table Reservation",
        filters={"outlet": outlet, "reservation_date": date, "status": ["!=", "Cancelled"]},
        fields=["name", "guest_name", "mobile_no", "reservation_date",
                "reservation_time", "party_size", "table", "status", "notes"],
        order_by="reservation_time",
    )


@frappe.whitelist()
def create_reservation(outlet, guest_name, reservation_date, reservation_time,
                        party_size, mobile_no="", table=None, notes=""):
    doc = frappe.get_doc({
        "doctype": "Table Reservation",
        "outlet": outlet,
        "guest_name": guest_name,
        "mobile_no": mobile_no,
        "reservation_date": reservation_date,
        "reservation_time": reservation_time,
        "party_size": int(party_size),
        "table": table,
        "notes": notes,
        "status": "Confirmed",
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"name": doc.name}


# ─── Orders ───────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_active_order(table):
    order = frappe.db.get_value(
        "Restaurant Order",
        {"table": table, "status": ["not in", ["Cancelled", "Billed", "Settled"]], "docstatus": 1},
        "name",
    )
    if not order:
        return None
    return get_order(order)


@frappe.whitelist()
def get_order(order):
    doc = frappe.get_doc("Restaurant Order", order)
    return {
        "name": doc.name,
        "order_no": doc.order_no,
        "table": doc.table,
        "outlet": doc.outlet,
        "status": doc.status,
        "order_time": str(doc.order_time) if doc.order_time else None,
        "waiter": doc.waiter,
        "covers": doc.covers,
        "sub_total": flt(doc.sub_total),
        "tax_amount": flt(doc.tax_amount),
        "total_amount": flt(doc.total_amount),
        "is_room_service": doc.is_room_service,
        "folio": doc.folio,
        "pos_invoice": doc.pos_invoice,
        "items": [
            {
                "idx": i.idx,
                "menu_item": i.menu_item,
                "item_name": i.item_name,
                "qty": flt(i.qty),
                "rate": flt(i.rate),
                "amount": flt(i.amount),
                "course": i.course,
                "status": i.status,
                "modifiers": i.modifiers,
                "special_instructions": i.special_instructions,
            }
            for i in doc.items
        ],
    }


@frappe.whitelist()
def create_order(table, outlet, items, waiter="", covers=1,
                 is_room_service=0, folio=None):
    """
    items: JSON list of {menu_item, qty, modifiers?, special_instructions?, course?}
    """
    if isinstance(items, str):
        import json
        items = json.loads(items)

    line_items = []
    for it in items:
        mi = frappe.get_doc("Menu Item", it["menu_item"])
        line_items.append({
            "menu_item": mi.name,
            "item_name": mi.item_name,
            "qty": flt(it.get("qty", 1)),
            "rate": flt(mi.selling_price or 0),
            "amount": flt(it.get("qty", 1)) * flt(mi.selling_price or 0),
            "course": it.get("course", ""),
            "modifiers": it.get("modifiers", ""),
            "special_instructions": it.get("special_instructions", ""),
            "status": "Pending",
        })

    doc = frappe.get_doc({
        "doctype": "Restaurant Order",
        "table": table,
        "outlet": outlet,
        "waiter": waiter,
        "covers": int(covers),
        "order_time": now_datetime(),
        "is_room_service": int(is_room_service),
        "folio": folio,
        "status": "Draft",
        "items": line_items,
    })
    doc.insert(ignore_permissions=True)
    doc.submit()
    frappe.db.commit()
    return {"name": doc.name, "order_no": doc.order_no, "status": doc.status}


@frappe.whitelist()
def add_items_to_order(order, items):
    """Add new items to an already-submitted order (fires new KOT)."""
    if isinstance(items, str):
        import json
        items = json.loads(items)

    doc = frappe.get_doc("Restaurant Order", order)
    if doc.docstatus != 1:
        frappe.throw("Order is not submitted.")

    new_items = []
    for it in items:
        mi = frappe.get_doc("Menu Item", it["menu_item"])
        new_items.append({
            "menu_item": mi.name,
            "item_name": mi.item_name,
            "qty": flt(it.get("qty", 1)),
            "rate": flt(mi.selling_price or 0),
            "amount": flt(it.get("qty", 1)) * flt(mi.selling_price or 0),
            "course": it.get("course", ""),
            "modifiers": it.get("modifiers", ""),
            "special_instructions": it.get("special_instructions", ""),
            "status": "Pending",
        })

    # Amend order to add items, re-fire KOT for new items only
    from hospitality.restaurant.doctype.restaurant_order.restaurant_order import RestaurantOrder
    for item in new_items:
        doc.append("items", item)
    doc.save(ignore_permissions=True)

    # Fire KOT only for the newly added items
    from frappe.utils import now_datetime as _now
    stations = {}
    for item_data in new_items:
        station = frappe.db.get_value("Menu Item", item_data["menu_item"], "kitchen_station") or "Hot Kitchen"
        stations.setdefault(station, []).append(item_data)

    for station, sitems in stations.items():
        kot = frappe.get_doc({
            "doctype": "KOT",
            "restaurant_order": doc.name,
            "table": doc.table,
            "outlet": doc.outlet,
            "kitchen_station": station,
            "fired_at": _now(),
            "status": "Pending",
            "items": sitems,
        })
        kot.insert(ignore_permissions=True)

    frappe.db.commit()
    return {"added": len(new_items)}


@frappe.whitelist()
def void_order_item(order, item_idx):
    doc = frappe.get_doc("Restaurant Order", order)
    for item in doc.items:
        if item.idx == int(item_idx):
            item.status = "Void"
            break
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "voided"}


# ─── Billing ──────────────────────────────────────────────────────────────────

@frappe.whitelist()
def generate_bill(order):
    from hospitality.restaurant.doctype.restaurant_order.restaurant_order import create_pos_invoice
    invoice = create_pos_invoice(order)
    return {"pos_invoice": invoice}


@frappe.whitelist()
def get_payment_modes():
    return frappe.get_all("Mode of Payment", fields=["name", "type"], order_by="name")


# ─── KOT status ───────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_pending_kots(outlet):
    return frappe.get_all(
        "KOT",
        filters={"outlet": outlet, "status": ["in", ["Pending", "In Progress"]]},
        fields=["name", "restaurant_order", "table", "kitchen_station", "fired_at", "status"],
        order_by="fired_at",
    )


@frappe.whitelist()
def update_kot_status(kot, status):
    allowed = {"In Progress", "Done"}
    if status not in allowed:
        frappe.throw(f"Status must be one of: {', '.join(allowed)}")
    frappe.db.set_value("KOT", kot, "status", status)
    frappe.db.commit()
    return {"status": status}


# ─── Dashboard ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_dashboard_stats(outlet):
    occupied = frappe.db.count("Dining Table", {"outlet": outlet, "status": "Occupied"})
    available = frappe.db.count("Dining Table", {"outlet": outlet, "status": "Available"})
    orders_today = frappe.db.count(
        "Restaurant Order",
        {"outlet": outlet, "docstatus": 1,
         "order_time": [">=", today()], "status": ["!=", "Cancelled"]}
    )
    pending_kots = frappe.db.count(
        "KOT", {"outlet": outlet, "status": ["in", ["Pending", "In Progress"]]}
    )
    return {
        "occupied_tables": occupied,
        "available_tables": available,
        "orders_today": orders_today,
        "pending_kots": pending_kots,
    }
