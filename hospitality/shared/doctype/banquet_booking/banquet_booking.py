import frappe
from frappe.model.document import Document
from frappe.utils import flt


class BanquetBooking(Document):
    def validate(self):
        self._check_venue_availability()
        self._calculate_totals()

    def _check_venue_availability(self):
        if self.status == "Cancelled":
            return
        conflict = frappe.db.sql("""
            SELECT name FROM `tabBanquet Booking`
            WHERE venue = %s AND name != %s
              AND status IN ('Tentative', 'Confirmed')
              AND event_date = %s
              AND (
                (start_time < %s AND end_time > %s) OR
                (start_time < %s AND end_time > %s) OR
                (start_time >= %s AND end_time <= %s)
              )
        """, (
            self.venue, self.name, self.event_date,
            self.end_time, self.start_time,
            self.end_time, self.start_time,
            self.start_time, self.end_time,
        ))
        if conflict:
            frappe.throw(f"Venue {self.venue} is already booked during this time slot. Conflicting booking: {conflict[0][0]}")

    def _calculate_totals(self):
        total = sum(flt(row.amount) for row in (self.package_items or []))
        self.total_amount = total
        self.balance_due = total - flt(self.advance_paid)

    def on_submit(self):
        if self.status not in ("Confirmed", "Completed"):
            frappe.throw("Only Confirmed or Completed bookings can be submitted.")

    def on_cancel(self):
        self.status = "Cancelled"
