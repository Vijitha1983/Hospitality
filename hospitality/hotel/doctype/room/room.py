import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class Room(Document):
    def validate(self):
        if self.current_status == "Out of Order":
            self._create_maintenance_log()

    def mark_clean(self):
        self.db_set("current_status", "Vacant Clean")
        self.db_set("last_cleaned", now_datetime())

    def mark_occupied(self, booking):
        self.db_set("current_status", "Occupied")
        self.db_set("current_booking", booking)

    def mark_vacant_dirty(self):
        self.db_set("current_status", "Vacant Dirty")
        self.db_set("current_booking", None)

    def _create_maintenance_log(self):
        if not frappe.db.exists("Asset", {"asset_name": f"Room {self.room_number}"}):
            return
        asset = frappe.db.get_value("Asset", {"asset_name": f"Room {self.room_number}"}, "name")
        if asset:
            log = frappe.get_doc({
                "doctype": "Asset Maintenance Log",
                "asset": asset,
                "maintenance_status": "Planned",
                "description": f"Room {self.room_number} marked Out of Order",
                "completion_date": frappe.utils.today(),
            })
            log.insert(ignore_permissions=True)
