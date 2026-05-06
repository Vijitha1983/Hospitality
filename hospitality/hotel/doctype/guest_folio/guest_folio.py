import frappe
from frappe.model.document import Document
from frappe.utils import today, now_datetime, date_diff


class GuestFolio(Document):
    def before_insert(self):
        self.folio_no = self.name

    def validate(self):
        self._calculate_totals()

    def _calculate_totals(self):
        total = sum(row.amount for row in self.postings if not row.is_complimentary)
        self.total_charges = total
        advance = frappe.db.get_value("Advance Deposit",
            {"booking": self.booking, "status": "Received"},
            "sum(amount)") or 0
        self.advance_paid = advance
        self.net_payable = max(0, self.total_charges - self.advance_paid)

    def post_room_charge(self):
        booking = frappe.get_doc("Hotel Booking", self.booking)
        charge_type = frappe.db.get_value("Charge Type",
            {"charge_category": "Room"}, "name")
        if not charge_type:
            frappe.throw("No Charge Type found for category 'Room'. Please create one in Charge Type master.")

        nights = date_diff(booking.check_out_date, booking.check_in_date)
        self.append("postings", {
            "posting_date": today(),
            "posting_time": now_datetime().strftime("%H:%M:%S"),
            "charge_type": charge_type,
            "description": f"Room {booking.room} — {nights} Night(s)",
            "qty": nights,
            "rate": booking.nightly_rate or 0,
            "amount": (nights) * (booking.nightly_rate or 0),
        })
        self.save(ignore_permissions=True)

    def post_charge(self, charge_type, description, qty, rate, outlet=None, reference_doc=None):
        self.append("postings", {
            "posting_date": today(),
            "posting_time": now_datetime().strftime("%H:%M:%S"),
            "charge_type": charge_type,
            "description": description,
            "outlet": outlet,
            "qty": qty,
            "rate": rate,
            "amount": qty * rate,
            "reference_doc": reference_doc,
        })
        self.save(ignore_permissions=True)

    def on_submit(self):
        self._create_sales_invoice()

    def _create_sales_invoice(self):
        from hospitality.utils.folio_utils import create_sales_invoice_from_folio
        invoice = create_sales_invoice_from_folio(self)
        self.db_set("invoice", invoice.name)
        self.db_set("status", "Settled")
        frappe.msgprint(f"Sales Invoice {invoice.name} created.", indicator="green")


def post_nightly_room_charges():
    open_folios = frappe.get_all("Guest Folio",
        filters={"status": "Open"},
        fields=["name", "booking", "room", "check_in_date", "check_out_date"])
    for folio in open_folios:
        if frappe.utils.today() < folio.check_out_date:
            doc = frappe.get_doc("Guest Folio", folio.name)
            doc.post_room_charge()
