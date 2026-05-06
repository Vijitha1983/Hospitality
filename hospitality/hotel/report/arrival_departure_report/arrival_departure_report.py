import frappe


def execute(filters=None):
    filters = filters or {}
    report_date = filters.get("report_date")
    report_type = filters.get("report_type", "Both")
    room_type = filters.get("room_type")

    columns = [
        {"label": "Type", "fieldname": "movement_type", "fieldtype": "Data", "width": 90},
        {"label": "Booking", "fieldname": "booking", "fieldtype": "Link", "options": "Hotel Booking", "width": 130},
        {"label": "Guest", "fieldname": "guest_name", "fieldtype": "Data", "width": 160},
        {"label": "Room", "fieldname": "room", "fieldtype": "Link", "options": "Room", "width": 90},
        {"label": "Room Type", "fieldname": "room_type", "fieldtype": "Link", "options": "Room Type", "width": 120},
        {"label": "Check-In", "fieldname": "check_in_date", "fieldtype": "Date", "width": 100},
        {"label": "Check-Out", "fieldname": "check_out_date", "fieldtype": "Date", "width": 100},
        {"label": "Nights", "fieldname": "no_of_nights", "fieldtype": "Int", "width": 70},
        {"label": "Pax", "fieldname": "num_adults", "fieldtype": "Int", "width": 60},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
        {"label": "Rate/Night", "fieldname": "rate_per_night", "fieldtype": "Currency", "width": 110},
        {"label": "Source", "fieldname": "booking_source", "fieldtype": "Data", "width": 100},
        {"label": "Special Req.", "fieldname": "special_requests", "fieldtype": "Data", "width": 150},
    ]

    rt_cond = ""
    values_arr = [report_date, report_date]
    if room_type:
        rt_cond = "AND r.room_type = %s"
        values_arr.append(room_type)

    arrivals = []
    departures = []

    if report_type in ("Both", "Arrivals Only"):
        arrivals = frappe.db.sql(f"""
            SELECT b.name AS booking,
                   g.full_name AS guest_name,
                   b.room,
                   r.room_type,
                   b.check_in_date,
                   b.check_out_date,
                   b.num_nights AS no_of_nights,
                   b.num_adults,
                   b.status,
                   b.nightly_rate AS rate_per_night,
                   b.booking_source,
                   b.special_requests
            FROM `tabHotel Booking` b
            LEFT JOIN `tabGuest` g ON g.name = b.guest
            LEFT JOIN `tabRoom` r ON r.name = b.room
            WHERE b.check_in_date = %s
              AND b.status IN ('Confirmed', 'Checked In')
              {rt_cond}
            ORDER BY b.check_in_date
        """, values_arr[:1] + ([room_type] if room_type else []), as_dict=True)
        for row in arrivals:
            row["movement_type"] = "Arrival"

    if report_type in ("Both", "Departures Only"):
        departures = frappe.db.sql(f"""
            SELECT b.name AS booking,
                   g.full_name AS guest_name,
                   b.room,
                   r.room_type,
                   b.check_in_date,
                   b.check_out_date,
                   b.num_nights AS no_of_nights,
                   b.num_adults,
                   b.status,
                   b.nightly_rate AS rate_per_night,
                   b.booking_source,
                   b.special_requests
            FROM `tabHotel Booking` b
            LEFT JOIN `tabGuest` g ON g.name = b.guest
            LEFT JOIN `tabRoom` r ON r.name = b.room
            WHERE b.check_out_date = %s
              AND b.status IN ('Checked In', 'Checked Out')
              {rt_cond}
            ORDER BY b.check_out_date
        """, [report_date] + ([room_type] if room_type else []), as_dict=True)
        for row in departures:
            row["movement_type"] = "Departure"

    data = arrivals + departures
    data.sort(key=lambda x: (x["movement_type"], x["booking"]))
    return columns, data
