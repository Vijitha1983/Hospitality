import frappe
from frappe.model.document import Document
from frappe.utils import today


class HousekeepingTask(Document):
    def on_update(self):
        if self.status == "Done" or self.status == "Inspected":
            room = frappe.get_doc("Room", self.room)
            room.mark_clean()

        if self.status == "Failed" and self.task_type == "Inspection":
            new_task = frappe.get_doc({
                "doctype": "Housekeeping Task",
                "task_date": today(),
                "room": self.room,
                "task_type": "Daily Clean",
                "assigned_to": self.assigned_to,
                "supervisor": self.supervisor,
                "status": "Pending",
                "remarks": f"Re-clean after failed inspection {self.name}",
            })
            new_task.insert(ignore_permissions=True)
            frappe.msgprint(f"Re-clean task {new_task.name} created.", indicator="orange", alert=True)


def auto_create_daily_tasks():
    occupied_rooms = frappe.get_all("Room",
        filters={"current_status": "Occupied", "is_active": 1},
        fields=["name", "assigned_hk"])
    for room in occupied_rooms:
        if frappe.db.exists("Housekeeping Task", {"room": room.name, "task_date": today(), "task_type": "Daily Clean"}):
            continue
        frappe.get_doc({
            "doctype": "Housekeeping Task",
            "task_date": today(),
            "room": room.name,
            "task_type": "Daily Clean",
            "assigned_to": room.assigned_hk or frappe.db.get_single_value("Hospitality Settings", "default_hk_staff"),
            "status": "Pending",
        }).insert(ignore_permissions=True)
