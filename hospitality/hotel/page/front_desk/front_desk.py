import frappe
from frappe.utils import today, now_datetime, flt, date_diff


@frappe.whitelist()
def get_dashboard_stats():
    arrivals = frappe.db.count("Hotel Booking",
        {"check_in_date": today(), "status": ["in", ["Confirmed", "Checked In"]]})
    departures = frappe.db.count("Hotel Booking",
        {"check_out_date": today(), "status": "Checked In"})
    occupied = frappe.db.count("Room", {"status": "Occupied"})
    vacant_clean = frappe.db.count("Room", {"status": "Vacant Clean"})
    vacant_dirty = frappe.db.count("Room", {"status": "Vacant Dirty"})
    out_of_order = frappe.db.count("Room", {"status": "Out of Order"})
    total = frappe.db.count("Room", {"is_active": 1})
    occupancy_pct = round(occupied / total * 100, 1) if total else 0
    return {
        "arrivals": arrivals,
        "departures": departures,
        "occupied": occupied,
        "vacant_clean": vacant_clean,
        "vacant_dirty": vacant_dirty,
        "out_of_order": out_of_order,
        "total": total,
        "occupancy_pct": occupancy_pct,
    }


@frappe.whitelist()
def get_room_grid():
    rooms = frappe.get_all("Room",
        filters={"is_active": 1},
        fields=["name", "room_number", "room_type", "floor", "status",
                "max_occupancy", "nightly_rate"],
        order_by="floor, room_number")

    for room in rooms:
        booking = frappe.db.get_value("Hotel Booking",
            {"room": room.name, "status": "Checked In"},
            ["name", "guest", "check_in_date", "check_out_date", "num_adults"],
            as_dict=True)
        if booking:
            room["current_booking"] = booking.name
            guest_name = frappe.db.get_value("Guest", booking.guest, "full_name") if booking.guest else ""
            room["guest_name"] = guest_name
            room["check_out_date"] = booking.check_out_date
            nights_left = date_diff(booking.check_out_date, today())
            room["nights_remaining"] = nights_left
        else:
            room["current_booking"] = None
            room["guest_name"] = None
            room["check_out_date"] = None
            room["nights_remaining"] = None
    return rooms


@frappe.whitelist()
def get_today_arrivals():
    return frappe.db.sql("""
        SELECT b.name, b.guest, g.full_name AS guest_name,
               g.mobile_no, g.nationality,
               b.room, r.room_type, b.check_in_date, b.check_out_date,
               b.num_nights, b.num_adults, b.status,
               b.advance_paid, b.nightly_rate, b.booking_source,
               b.special_requests
        FROM `tabHotel Booking` b
        LEFT JOIN `tabGuest` g ON g.name = b.guest
        LEFT JOIN `tabRoom` r ON r.name = b.room
        WHERE b.check_in_date = %s
          AND b.status IN ('Confirmed', 'Checked In')
        ORDER BY b.check_in_date
    """, today(), as_dict=True)


@frappe.whitelist()
def get_today_departures():
    return frappe.db.sql("""
        SELECT b.name, b.guest, g.full_name AS guest_name,
               g.mobile_no, b.room, r.room_type,
               b.check_in_date, b.check_out_date,
               b.num_nights, b.nightly_rate, b.status,
               f.name AS folio, f.total_charges, f.advance_paid, f.net_payable
        FROM `tabHotel Booking` b
        LEFT JOIN `tabGuest` g ON g.name = b.guest
        LEFT JOIN `tabRoom` r ON r.name = b.room
        LEFT JOIN `tabGuest Folio` f ON f.booking = b.name AND f.docstatus != 2
        WHERE b.check_out_date = %s
          AND b.status = 'Checked In'
        ORDER BY b.check_out_date
    """, today(), as_dict=True)


@frappe.whitelist()
def get_folio_details(booking):
    folio = frappe.db.get_value("Guest Folio",
        {"booking": booking, "status": "Open"},
        ["name", "total_charges", "advance_paid", "net_payable"],
        as_dict=True)
    if not folio:
        return None
    folio["postings"] = frappe.get_all("Folio Posting",
        filters={"parent": folio.name},
        fields=["posting_date", "charge_type", "description", "qty", "rate", "amount"],
        order_by="posting_date desc",
        limit=20)
    return folio


@frappe.whitelist()
def quick_checkin(booking):
    booking_doc = frappe.get_doc("Hotel Booking", booking)
    if booking_doc.status != "Confirmed":
        frappe.throw(f"Booking status is '{booking_doc.status}'. Only Confirmed bookings can be checked in.")

    checkin = frappe.get_doc({
        "doctype": "Hotel Check-in",
        "booking": booking,
        "guest": booking_doc.guest,
        "room": booking_doc.room,
        "check_in_datetime": now_datetime(),
        "actual_check_in_date": today(),
    })
    checkin.insert(ignore_permissions=True)
    checkin.submit()
    frappe.db.commit()
    return {"checkin": checkin.name, "status": "checked_in"}


@frappe.whitelist()
def quick_checkout(booking, payment_method="Cash"):
    booking_doc = frappe.get_doc("Hotel Booking", booking)
    if booking_doc.status != "Checked In":
        frappe.throw("Guest is not checked in.")

    folio = frappe.db.get_value("Guest Folio",
        {"booking": booking, "status": "Open"}, "name")
    if not folio:
        frappe.throw("No open folio found for this booking.")

    checkout = frappe.get_doc({
        "doctype": "Hotel Check-out",
        "booking": booking,
        "guest": booking_doc.guest,
        "room": booking_doc.room,
        "folio": folio,
        "check_out_datetime": now_datetime(),
        "actual_check_out_date": today(),
        "settlement_mode": payment_method,
    })
    checkout.insert(ignore_permissions=True)
    checkout.submit()
    frappe.db.commit()
    return {"checkout": checkout.name, "status": "checked_out"}


@frappe.whitelist()
def post_folio_charge(booking, charge_type, description, amount, qty=1):
    folio_name = frappe.db.get_value("Guest Folio",
        {"booking": booking, "status": "Open"}, "name")
    if not folio_name:
        frappe.throw("No open folio for this booking.")
    folio = frappe.get_doc("Guest Folio", folio_name)
    folio.post_charge(
        charge_type=charge_type,
        description=description,
        qty=flt(qty),
        rate=flt(amount) / flt(qty),
    )
    return {"folio": folio_name, "status": "posted"}


@frappe.whitelist()
def get_charge_types():
    return frappe.get_all("Charge Type",
        filters={"is_active": 1},
        fields=["name", "charge_name", "charge_category"],
        order_by="charge_name")


@frappe.whitelist()
def update_room_status(room, status):
    allowed = ("Vacant Clean", "Vacant Dirty", "Out of Order", "Maintenance")
    if status not in allowed:
        frappe.throw(f"Invalid status. Allowed: {', '.join(allowed)}")
    frappe.db.set_value("Room", room, "status", status)
    frappe.db.commit()
    return {"room": room, "status": status}
