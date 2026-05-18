"""
Hotel front-desk API — called by the Windows Hotel Desk PyQt6 app.
All functions return plain dicts / lists (JSON-serialisable).
"""
import frappe
from frappe.utils import today, now_datetime, date_diff, flt


# ─── Guest ────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def search_guests(query):
    return frappe.get_all(
        "Guest",
        filters=[["guest_name", "like", f"%{query}%"]],
        fields=["name", "guest_name", "mobile_no", "email", "nationality", "id_type", "id_number"],
        limit=20,
    )


@frappe.whitelist()
def get_guest(guest):
    doc = frappe.get_doc("Guest", guest)
    return {
        "name": doc.name,
        "guest_name": doc.guest_name,
        "mobile_no": doc.mobile_no,
        "email": doc.email,
        "nationality": doc.nationality,
        "id_type": doc.id_type,
        "id_number": doc.id_number,
        "loyalty_points": doc.loyalty_points if hasattr(doc, "loyalty_points") else 0,
    }


@frappe.whitelist()
def create_guest(guest_name, mobile_no="", email="", nationality="", id_type="", id_number=""):
    doc = frappe.get_doc({
        "doctype": "Guest",
        "guest_name": guest_name,
        "mobile_no": mobile_no,
        "email": email,
        "nationality": nationality,
        "id_type": id_type,
        "id_number": id_number,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"name": doc.name, "guest_name": doc.guest_name}


# ─── Availability ─────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_available_rooms(check_in_date, check_out_date, room_type=None):
    """Returns rooms that have no overlapping confirmed/checked-in bookings."""
    filters = {"status": "Available"}
    if room_type:
        filters["room_type"] = room_type

    rooms = frappe.get_all(
        "Room",
        filters=filters,
        fields=["name", "room_number", "room_type", "floor", "view_type", "max_occupancy"],
    )

    booked = frappe.db.sql("""
        SELECT DISTINCT room FROM `tabHotel Booking`
        WHERE status IN ('Confirmed', 'Checked In')
          AND room IS NOT NULL
          AND check_in_date < %s
          AND check_out_date > %s
    """, (check_out_date, check_in_date), as_list=True)

    booked_rooms = {r[0] for r in booked}
    available = [r for r in rooms if r.name not in booked_rooms]

    for r in available:
        r["nights"] = date_diff(check_out_date, check_in_date)

    return available


@frappe.whitelist()
def get_room_types():
    return frappe.get_all(
        "Room Type",
        fields=["name", "type_name", "base_rate", "max_occupancy", "description"],
    )


@frappe.whitelist()
def get_rate_plans():
    return frappe.get_all(
        "Rate Plan",
        filters={"is_active": 1},
        fields=["name", "plan_name", "plan_type", "base_rate_multiplier"],
    )


# ─── Booking ──────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_booking(guest, room_type, check_in_date, check_out_date,
                   num_adults=1, num_children=0, rate_plan=None,
                   room=None, company=None, special_requests=""):
    company = company or frappe.defaults.get_user_default("Company")
    doc = frappe.get_doc({
        "doctype": "Hotel Booking",
        "guest": guest,
        "room_type": room_type,
        "room": room,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "num_adults": int(num_adults),
        "num_children": int(num_children),
        "rate_plan": rate_plan,
        "company": company,
        "special_requests": special_requests,
        "status": "Confirmed",
    })
    doc.insert(ignore_permissions=True)
    doc.submit()
    frappe.db.commit()
    return {"name": doc.name, "booking_no": doc.booking_no, "status": doc.status}


@frappe.whitelist()
def get_booking(booking):
    doc = frappe.get_doc("Hotel Booking", booking)
    return doc.as_dict()


@frappe.whitelist()
def search_bookings(query="", status=None, date=None):
    filters = {}
    if status:
        filters["status"] = status
    if date:
        filters["check_in_date"] = date
    if query:
        return frappe.db.sql("""
            SELECT b.name, b.booking_no, b.guest, b.guest_name_display,
                   b.room_type, b.room, b.check_in_date, b.check_out_date, b.status
            FROM `tabHotel Booking` b
            WHERE (b.booking_no LIKE %s OR b.guest LIKE %s OR b.guest_name_display LIKE %s)
              AND b.docstatus = 1
            ORDER BY b.check_in_date DESC LIMIT 30
        """, (f"%{query}%", f"%{query}%", f"%{query}%"), as_dict=True)
    filters["docstatus"] = 1
    return frappe.get_all(
        "Hotel Booking", filters=filters,
        fields=["name", "booking_no", "guest", "room_type", "room",
                "check_in_date", "check_out_date", "status", "nightly_rate"],
        order_by="check_in_date desc", limit=50,
    )


@frappe.whitelist()
def get_arrivals(date=None):
    date = date or today()
    return frappe.get_all(
        "Hotel Booking",
        filters={"check_in_date": date, "status": "Confirmed", "docstatus": 1},
        fields=["name", "booking_no", "guest", "room_type", "room",
                "num_adults", "num_children", "nightly_rate", "special_requests"],
        order_by="name",
    )


@frappe.whitelist()
def get_departures(date=None):
    date = date or today()
    return frappe.get_all(
        "Hotel Booking",
        filters={"check_out_date": date, "status": "Checked In", "docstatus": 1},
        fields=["name", "booking_no", "guest", "room", "room_type", "check_in_date"],
        order_by="name",
    )


# ─── Check-in ─────────────────────────────────────────────────────────────────

@frappe.whitelist()
def perform_check_in(booking, room=None, num_adults=None, num_children=None,
                     id_verified=1, advance_collected=0):
    booking_doc = frappe.get_doc("Hotel Booking", booking)
    room = room or booking_doc.room
    if not room:
        frappe.throw("A room must be assigned before check-in.")

    check_in = frappe.get_doc({
        "doctype": "Hotel Check-in",
        "booking": booking,
        "guest": booking_doc.guest,
        "room": room,
        "check_in_datetime": now_datetime(),
        "id_verified": int(id_verified),
        "num_adults": int(num_adults or booking_doc.num_adults),
        "num_children": int(num_children or booking_doc.num_children or 0),
        "advance_collected": flt(advance_collected),
    })
    check_in.insert(ignore_permissions=True)
    check_in.submit()
    frappe.db.commit()

    return {
        "check_in": check_in.name,
        "folio": check_in.folio,
        "room": room,
        "guest": booking_doc.guest,
    }


# ─── Folio ────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_folio(folio):
    doc = frappe.get_doc("Guest Folio", folio)
    return {
        "name": doc.name,
        "guest": doc.guest,
        "guest_name": doc.guest_name,
        "room": doc.room,
        "check_in": str(doc.check_in) if doc.check_in else None,
        "check_out": str(doc.check_out) if doc.check_out else None,
        "status": doc.status,
        "total_charges": flt(doc.total_charges),
        "total_payments": flt(doc.total_payments),
        "balance_due": flt(doc.balance_due),
        "postings": [
            {
                "posting_date": str(p.posting_date),
                "description": p.description,
                "charge_type": p.charge_type,
                "posting_type": p.posting_type,
                "amount": flt(p.amount),
            }
            for p in (doc.postings or [])
        ],
    }


@frappe.whitelist()
def get_folio_by_room(room):
    folio = frappe.db.get_value(
        "Guest Folio", {"room": room, "status": "Open"}, "name"
    )
    if not folio:
        frappe.throw(f"No open folio found for room {room}.")
    return get_folio(folio)


@frappe.whitelist()
def post_folio_charge(folio, charge_type, description, qty=1, rate=0):
    doc = frappe.get_doc("Guest Folio", folio)
    doc.post_charge(
        charge_type=charge_type,
        description=description,
        qty=flt(qty),
        rate=flt(rate),
    )
    frappe.db.commit()
    return {"balance_due": flt(doc.balance_due)}


@frappe.whitelist()
def get_charge_types():
    return frappe.get_all(
        "Charge Type",
        filters={"is_active": 1},
        fields=["name", "charge_name", "charge_category", "is_taxable"],
        order_by="charge_category, charge_name",
    )


# ─── Check-out ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def perform_check_out(check_in, payment_method, amount=None, tip=0):
    check_in_doc = frappe.get_doc("Hotel Check-in", check_in)

    checkout = frappe.get_doc({
        "doctype": "Hotel Check-out",
        "check_in": check_in,
        "booking": check_in_doc.booking,
        "guest": check_in_doc.guest,
        "folio": check_in_doc.folio,
        "check_out_datetime": now_datetime(),
        "payment_method": payment_method,
        "amount_received": flt(amount),
        "tip": flt(tip),
    })
    checkout.insert(ignore_permissions=True)
    checkout.submit()
    frappe.db.commit()
    return {"checkout": checkout.name, "pos_invoice": checkout.pos_invoice}


# ─── Dashboard ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_dashboard_stats():
    occupied = frappe.db.count("Room", {"status": "Occupied"})
    available = frappe.db.count("Room", {"status": "Available"})
    total = frappe.db.count("Room")
    arrivals_today = frappe.db.count(
        "Hotel Booking",
        {"check_in_date": today(), "status": "Confirmed", "docstatus": 1}
    )
    departures_today = frappe.db.count(
        "Hotel Booking",
        {"check_out_date": today(), "status": "Checked In", "docstatus": 1}
    )
    return {
        "total_rooms": total,
        "occupied": occupied,
        "available": available,
        "occupancy_pct": round((occupied / total * 100) if total else 0, 1),
        "arrivals_today": arrivals_today,
        "departures_today": departures_today,
    }
