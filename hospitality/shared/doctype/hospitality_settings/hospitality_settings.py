import frappe
from frappe.model.document import Document


class HospitalitySettings(Document):
    pass


def get_settings():
    return frappe.get_single("Hospitality Settings")
