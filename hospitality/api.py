import frappe
from frappe import _
from frappe.utils import now_datetime, today


# ─── KDS (Kitchen Display System) ─────────────────────────────────────────────

@frappe.whitelist(allow_guest=False)
def get_pending_kots(kitchen_station=None):
    """Return all open KOTs for a given kitchen station (or all stations)."""
    filters = {"status": ["in", ["Open", "In Progress"]]}
    if kitchen_station:
        filters["kitchen_station"] = kitchen_station
    kots = frappe.get_all(
        "KOT",
        filters=filters,
        fields=["name", "kitchen_station", "table_no", "status", "creation", "order"],
        order_by="creation asc",
    )
    for kot in kots:
        kot["items"] = frappe.get_all(
            "KOT Item",
            filters={"parent": kot["name"]},
            fields=["menu_item", "item_name", "qty", "special_instructions"],
        )
    return kots


@frappe.whitelist(allow_guest=False)
def update_kot_status(kot_name, status):
    """Update a KOT status (In Progress / Ready). Called by kitchen display."""
    allowed = ("In Progress", "Ready")
    if status not in allowed:
        frappe.throw(_(f"Status must be one of: {', '.join(allowed)}"))
    frappe.db.set_value("KOT", kot_name, "status", status)
    frappe.db.commit()
    # Trigger order status sync
    kot_doc = frappe.get_doc("KOT", kot_name)
    order = kot_doc.order
    if order:
        _sync_order_status(order)
    return {"status": "ok", "kot": kot_name, "new_status": status}


def _sync_order_status(order_name):
    kots = frappe.get_all(
        "KOT",
        filters={"order": order_name},
        fields=["status"],
    )
    statuses = {k["status"] for k in kots}
    if statuses == {"Ready"}:
        frappe.db.set_value("Restaurant Order", order_name, "status", "Served")
    elif "Ready" in statuses:
        frappe.db.set_value("Restaurant Order", order_name, "status", "Partially Served")
    frappe.db.commit()


# ─── Bar Display System ────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=False)
def get_pending_bots(bar_station=None):
    """Return all open BOTs for a given bar station."""
    filters = {"status": ["in", ["Open", "In Progress"]]}
    if bar_station:
        filters["bar_station"] = bar_station
    bots = frappe.get_all(
        "BOT",
        filters=filters,
        fields=["name", "bar_station", "tab_name", "status", "creation"],
        order_by="creation asc",
    )
    for bot in bots:
        bot["items"] = frappe.get_all(
            "BOT Item",
            filters={"parent": bot["name"]},
            fields=["drink_item", "qty", "special_instructions"],
        )
    return bots


@frappe.whitelist(allow_guest=False)
def update_bot_status(bot_name, status):
    """Update a BOT status. Called by bar display."""
    allowed = ("In Progress", "Ready", "Served")
    if status not in allowed:
        frappe.throw(_(f"Status must be one of: {', '.join(allowed)}"))
    frappe.db.set_value("BOT", bot_name, "status", status)
    frappe.db.commit()
    return {"status": "ok", "bot": bot_name, "new_status": status}


# ─── Mobile Ordering ───────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=False)
def get_menu(outlet):
    """Return active menu items for an outlet grouped by category."""
    items = frappe.get_all(
        "Menu Item",
        filters={"outlet": outlet, "is_active": 1},
        fields=["name", "item_name", "category", "selling_price", "description", "image"],
        order_by="category, item_name",
    )
    grouped = {}
    for item in items:
        cat = item.get("category") or "Other"
        grouped.setdefault(cat, []).append(item)
    return grouped


@frappe.whitelist(allow_guest=False)
def get_drink_menu(outlet):
    """Return active drink menu for a bar outlet grouped by category."""
    items = frappe.get_all(
        "Drink Menu Item",
        filters={"outlet": outlet, "is_active": 1},
        fields=["name", "item_name", "category", "selling_price", "description", "image"],
        order_by="category, item_name",
    )
    grouped = {}
    for item in items:
        cat = item.get("category") or "Other"
        grouped.setdefault(cat, []).append(item)
    return grouped


@frappe.whitelist(allow_guest=False)
def place_restaurant_order(outlet, table_no, items, guest=None, notes=None):
    """
    Create a Restaurant Order from mobile POS.
    items: JSON list of {menu_item, qty, special_instructions}
    """
    if isinstance(items, str):
        import json
        items = json.loads(items)

    order = frappe.get_doc({
        "doctype": "Restaurant Order",
        "outlet": outlet,
        "table_no": table_no,
        "guest": guest,
        "order_notes": notes,
        "status": "Draft",
        "items": [
            {
                "menu_item": i["menu_item"],
                "qty": i.get("qty", 1),
                "special_instructions": i.get("special_instructions", ""),
            }
            for i in items
        ],
    })
    order.insert(ignore_permissions=True)
    return {"order": order.name, "status": "created"}


@frappe.whitelist(allow_guest=False)
def place_bar_order(outlet, bar_station, items, tab_name=None, guest=None):
    """
    Create a Bar Order from mobile / tab POS.
    items: JSON list of {drink_item, qty, special_instructions}
    """
    if isinstance(items, str):
        import json
        items = json.loads(items)

    order = frappe.get_doc({
        "doctype": "Bar Order",
        "outlet": outlet,
        "bar_station": bar_station,
        "tab_name": tab_name,
        "guest": guest,
        "status": "Draft",
        "items": [
            {
                "drink_item": i["drink_item"],
                "qty": i.get("qty", 1),
                "special_instructions": i.get("special_instructions", ""),
            }
            for i in items
        ],
    })
    order.insert(ignore_permissions=True)
    return {"order": order.name, "status": "created"}


# ─── Channel Manager Webhook ───────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def channel_manager_webhook():
    """
    Receives booking payloads from OTA channel managers (Booking.com, Expedia, etc.)
    Expected JSON body: {channel, room_type, check_in, check_out, guest_name, guest_email, rate, ref_no}
    """
    import json
    from frappe.utils import getdate

    payload = frappe.local.request.get_json(silent=True) or {}

    required = ("channel", "room_type", "check_in", "check_out", "guest_name", "rate")
    missing = [f for f in required if not payload.get(f)]
    if missing:
        frappe.response.http_status_code = 400
        return {"error": f"Missing fields: {', '.join(missing)}"}

    # Find or create Guest
    guest_name = payload["guest_name"]
    guest_email = payload.get("guest_email", "")
    existing_guest = frappe.db.get_value("Guest", {"email": guest_email}, "name") if guest_email else None

    if not existing_guest:
        guest_doc = frappe.get_doc({
            "doctype": "Guest",
            "full_name": guest_name,
            "email": guest_email,
            "source": payload.get("channel", "OTA"),
        })
        guest_doc.insert(ignore_permissions=True)
        existing_guest = guest_doc.name

    # Find an available room of the requested type
    room_type = payload["room_type"]
    check_in = payload["check_in"]
    check_out = payload["check_out"]

    available = frappe.db.sql("""
        SELECT name FROM `tabRoom`
        WHERE room_type = %s AND status = 'Vacant Clean'
          AND name NOT IN (
            SELECT room FROM `tabHotel Booking`
            WHERE status IN ('Confirmed', 'Checked In')
              AND check_in_date < %s AND check_out_date > %s
          )
        LIMIT 1
    """, (room_type, check_out, check_in), as_dict=True)

    if not available:
        frappe.response.http_status_code = 409
        return {"error": f"No available rooms of type {room_type} for the requested dates"}

    room = available[0]["name"]

    booking = frappe.get_doc({
        "doctype": "Hotel Booking",
        "guest": existing_guest,
        "room": room,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "rate_per_night": payload["rate"],
        "status": "Confirmed",
        "booking_source": payload.get("channel", "OTA"),
        "channel_ref_no": payload.get("ref_no", ""),
    })
    booking.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "booking": booking.name,
        "room": room,
        "guest": existing_guest,
        "status": "confirmed",
    }


# ─── Availability API ──────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=False)
def get_room_availability(check_in_date, check_out_date, room_type=None):
    """Return available rooms for date range, optionally filtered by room type."""
    filters = {"status": "Vacant Clean"}
    if room_type:
        filters["room_type"] = room_type

    rooms = frappe.get_all(
        "Room",
        filters=filters,
        fields=["name", "room_type", "floor", "max_occupancy"],
    )

    booked_rooms = frappe.db.sql_list("""
        SELECT DISTINCT room FROM `tabHotel Booking`
        WHERE status IN ('Confirmed', 'Checked In')
          AND check_in_date < %s AND check_out_date > %s
    """, (check_out_date, check_in_date))

    available = [r for r in rooms if r["name"] not in booked_rooms]
    return available


@frappe.whitelist(allow_guest=False)
def get_folio_balance(booking_name):
    """Return current folio balance for a booking."""
    folio = frappe.db.get_value(
        "Guest Folio",
        {"booking": booking_name, "docstatus": ["!=", 2]},
        ["name", "total_charges", "total_payments", "balance"],
        as_dict=True,
    )
    if not folio:
        return {"error": "No active folio found for this booking"}
    return folio


@frappe.whitelist(allow_guest=False)
def get_table_status(outlet):
    """Return table occupancy status for a restaurant outlet."""
    orders = frappe.get_all(
        "Restaurant Order",
        filters={"outlet": outlet, "status": ["in", ["Draft", "In Progress", "Partially Served"]]},
        fields=["table_no", "status", "name"],
    )
    table_map = {}
    for o in orders:
        table_map[o["table_no"]] = {"status": o["status"], "order": o["name"]}
    return table_map
