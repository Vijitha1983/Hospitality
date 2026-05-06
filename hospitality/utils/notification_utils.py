import frappe


def send_booking_confirmation(booking_name):
    booking = frappe.get_doc("Hotel Booking", booking_name)
    guest = frappe.get_doc("Guest", booking.guest)
    template_name = frappe.db.get_single_value("Hospitality Settings", "booking_confirmation_template")
    if not template_name or not guest.email:
        return

    template = frappe.get_doc("Email Template", template_name)
    context = {
        "guest_name": guest.full_name,
        "booking_no": booking.booking_no or booking.name,
        "check_in_date": booking.check_in_date,
        "check_out_date": booking.check_out_date,
        "room_type": booking.room_type,
        "num_nights": booking.num_nights,
    }
    frappe.sendmail(
        recipients=[guest.email],
        subject=frappe.render_template(template.subject, context),
        message=frappe.render_template(template.response, context),
    )


def send_reservation_confirmation(reservation_name):
    res = frappe.get_doc("Table Reservation", reservation_name)
    if not res.email:
        return
    frappe.sendmail(
        recipients=[res.email],
        subject=f"Table Reservation Confirmed — {res.reservation_no}",
        message=f"""
        Dear {res.guest_name},<br><br>
        Your table reservation has been confirmed.<br>
        Date: {res.reservation_date} at {res.reservation_time}<br>
        Covers: {res.num_covers}<br>
        Reservation No: {res.reservation_no}<br><br>
        Thank you for choosing us.
        """,
    )


def send_kot_ready_notification(kot_name):
    kot = frappe.get_doc("KOT", kot_name)
    steward = frappe.db.get_value("Restaurant Order", kot.restaurant_order, "steward")
    if not steward:
        return
    employee_email = frappe.db.get_value("Employee", steward, "company_email") or \
                     frappe.db.get_value("Employee", steward, "personal_email")
    if employee_email:
        frappe.sendmail(
            recipients=[employee_email],
            subject=f"KOT Ready — {kot.kot_no} | Table {kot.table}",
            message=f"KOT {kot.kot_no} for Table {kot.table} is ready for service.",
        )
