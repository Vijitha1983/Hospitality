import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class HotelCheckIn(Document):
    def validate(self):
        booking = frappe.get_doc("Hotel Booking", self.booking)
        self.guest = booking.guest
        if booking.status != "Confirmed":
            frappe.throw(f"Booking {self.booking} is not in Confirmed status. Current status: {booking.status}")

    def on_submit(self):
        self._update_booking_status()
        self._update_room_status()
        self._create_folio()

    def _update_booking_status(self):
        frappe.db.set_value("Hotel Booking", self.booking, {
            "status": "Checked In",
            "room": self.room
        })

    def _update_room_status(self):
        room = frappe.get_doc("Room", self.room)
        room.mark_occupied(self.booking)

    def _create_folio(self):
        booking = frappe.get_doc("Hotel Booking", self.booking)
        folio = frappe.get_doc({
            "doctype": "Guest Folio",
            "booking": self.booking,
            "guest": self.guest,
            "room": self.room,
            "check_in_date": booking.check_in_date,
            "check_out_date": booking.check_out_date,
            "status": "Open",
        })
        folio.insert(ignore_permissions=True)
        self.db_set("folio", folio.name)

        folio.post_room_charge()
        frappe.msgprint(f"Guest Folio {folio.name} created.", indicator="green", alert=True)
