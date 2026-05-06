import frappe
from frappe.model.document import Document


class HotelCheckOut(Document):
    def validate(self):
        booking = frappe.get_doc("Hotel Booking", self.booking)
        self.guest = booking.guest
        self.room = booking.room

        folio = frappe.get_doc("Guest Folio", self.folio)
        folio._calculate_totals()
        self.total_amount = folio.total_charges
        self.advance_adjusted = folio.advance_paid
        self.net_payable = folio.net_payable

    def on_submit(self):
        self._settle_folio()
        self._release_room()
        self._update_booking()

    def _settle_folio(self):
        folio = frappe.get_doc("Guest Folio", self.folio)
        folio.submit()
        self.db_set("invoice", folio.invoice)

        if self.net_payable > 0 and self.settlement_mode != "Direct Bill":
            pe = self._create_payment_entry(folio)
            self.db_set("payment_entry", pe.name)

    def _create_payment_entry(self, folio):
        from hospitality.utils.folio_utils import create_payment_entry_for_folio
        return create_payment_entry_for_folio(folio, self.net_payable, self.settlement_mode)

    def _release_room(self):
        room = frappe.get_doc("Room", self.room)
        room.mark_vacant_dirty()

    def _update_booking(self):
        frappe.db.set_value("Hotel Booking", self.booking, "status", "Checked Out")
