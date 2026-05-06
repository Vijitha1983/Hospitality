import frappe
from frappe.model.document import Document


class AdvanceDeposit(Document):
    def validate(self):
        booking = frappe.get_doc("Hotel Booking", self.booking)
        self.guest = booking.guest

    def on_submit(self):
        self._create_payment_entry()
        self._update_booking_advance()

    def _create_payment_entry(self):
        from hospitality.utils.folio_utils import create_advance_payment_entry
        pe = create_advance_payment_entry(self)
        self.db_set("payment_entry", pe.name)

    def _update_booking_advance(self):
        current = frappe.db.get_value("Hotel Booking", self.booking, "advance_paid") or 0
        frappe.db.set_value("Hotel Booking", self.booking, "advance_paid", current + self.amount)
