import frappe
from frappe.utils import date_diff, getdate


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    room_type = filters.get("room_type")

    columns = [
        {"label": "Room Type", "fieldname": "room_type", "fieldtype": "Data", "width": 140},
        {"label": "Total Rooms", "fieldname": "total_rooms", "fieldtype": "Int", "width": 100},
        {"label": "Occupied Nights", "fieldname": "occupied_nights", "fieldtype": "Int", "width": 120},
        {"label": "Available Nights", "fieldname": "available_nights", "fieldtype": "Int", "width": 120},
        {"label": "Occupancy %", "fieldname": "occupancy_pct", "fieldtype": "Percent", "width": 110},
        {"label": "Revenue", "fieldname": "revenue", "fieldtype": "Currency", "width": 130},
        {"label": "RevPAR", "fieldname": "revpar", "fieldtype": "Currency", "width": 110},
    ]

    days = date_diff(to_date, from_date) + 1

    room_filters = {}
    if room_type:
        room_filters["room_type"] = room_type

    rooms = frappe.get_all("Room", filters=room_filters, fields=["name", "room_type"])
    room_type_map = {}
    for r in rooms:
        room_type_map.setdefault(r["room_type"], []).append(r["name"])

    booking_cond = ""
    if room_type:
        rt_rooms = [r["name"] for r in rooms]
        if not rt_rooms:
            return columns, []
        room_list = ", ".join(f"'{r}'" for r in rt_rooms)
        booking_cond = f"AND b.room IN ({room_list})"

    bookings = frappe.db.sql(f"""
        SELECT b.room, b.check_in_date, b.check_out_date,
               b.rate_per_night, b.no_of_nights,
               r.room_type
        FROM `tabHotel Booking` b
        JOIN `tabRoom` r ON r.name = b.room
        WHERE b.status IN ('Checked In', 'Checked Out')
          AND b.check_in_date <= %s AND b.check_out_date >= %s
          {booking_cond}
    """, (to_date, from_date), as_dict=True)

    rt_stats = {}
    for rt, rms in room_type_map.items():
        rt_stats[rt] = {"total_rooms": len(rms), "occupied_nights": 0, "revenue": 0}

    for bk in bookings:
        rt = bk["room_type"]
        if rt not in rt_stats:
            continue
        overlap_start = max(getdate(bk["check_in_date"]), getdate(from_date))
        overlap_end = min(getdate(bk["check_out_date"]), getdate(to_date))
        nights = date_diff(overlap_end, overlap_start)
        if nights > 0:
            rt_stats[rt]["occupied_nights"] += nights
            rt_stats[rt]["revenue"] += nights * (bk["rate_per_night"] or 0)

    data = []
    for rt, stats in rt_stats.items():
        available = stats["total_rooms"] * days
        occ_pct = (stats["occupied_nights"] / available * 100) if available else 0
        revpar = (stats["revenue"] / available) if available else 0
        data.append({
            "room_type": rt,
            "total_rooms": stats["total_rooms"],
            "occupied_nights": stats["occupied_nights"],
            "available_nights": available,
            "occupancy_pct": round(occ_pct, 2),
            "revenue": stats["revenue"],
            "revpar": round(revpar, 2),
        })

    return columns, data
