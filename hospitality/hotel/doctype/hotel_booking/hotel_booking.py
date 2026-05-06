import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, getdate


class HotelBooking(Document):
    def before_insert(self):
        self.booking_no = self.name

    def validate(self):
        self._validate_dates()
        self._set_num_nights()
        self._set_nightly_rate()
        self._check_availability()

    def _validate_dates(self):
        if getdate(self.check_in_date) >= getdate(self.check_out_date):
            frappe.throw("Check-out date must be after check-in date.")
        if getdate(self.check_in_date) < getdate(frappe.utils.today()):
            if self.status == "Enquiry":
                frappe.msgprint("Check-in date is in the past.", indicator="orange", alert=True)

    def _set_num_nights(self):
        if self.check_in_date and self.check_out_date:
            self.num_nights = date_diff(self.check_out_date, self.check_in_date)

    def _set_nightly_rate(self):
        if self.rate_plan:
            rate_plan = frappe.get_doc("Rate Plan", self.rate_plan)
            rate = rate_plan.get_rate_for_room_type(self.room_type)
            if rate:
                self.nightly_rate = rate
                return
        if self.room_type:
            self.nightly_rate = frappe.db.get_value("Room Type", self.room_type, "base_rate") or 0

    def _check_availability(self):
        if not self.room:
            return
        conflict = frappe.db.sql("""
            SELECT name FROM `tabHotel Booking`
            WHERE room = %s
              AND name != %s
              AND status IN ('Confirmed', 'Checked In')
              AND check_in_date < %s
              AND check_out_date > %s
        """, (self.room, self.name, self.check_out_date, self.check_in_date))
        if conflict:
            frappe.throw(f"Room {self.room} is already booked for the selected dates. Conflicting booking: {conflict[0][0]}")

    def on_submit(self):
        if self.room:
            room = frappe.get_doc("Room", self.room)
            room.mark_occupied(self.name)

    def on_cancel(self):
        if self.room:
            room = frappe.get_doc("Room", self.room)
            room.mark_vacant_dirty()
        self.status = "Cancelled"


@frappe.whitelist()
def get_available_rooms(room_type, check_in_date, check_out_date):
    booked_rooms = frappe.db.sql_list("""
        SELECT room FROM `tabHotel Booking`
        WHERE room IS NOT NULL
          AND room_type = %s
          AND status IN ('Confirmed', 'Checked In')
          AND check_in_date < %s
          AND check_out_date > %s
    """, (room_type, check_out_date, check_in_date))

    rooms = frappe.get_all("Room",
        filters={
            "room_type": room_type,
            "is_active": 1,
            "current_status": ["in", ["Vacant Clean", "Vacant Dirty"]],
            "name": ["not in", booked_rooms or ["__none__"]],
        },
        fields=["name", "room_number", "floor", "wing", "current_status"]
    )
    return rooms
