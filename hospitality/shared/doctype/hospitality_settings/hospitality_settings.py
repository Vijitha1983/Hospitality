import frappe
from frappe.model.document import Document


class HospitalitySettings(Document):
    pass


def get_settings():
    return frappe.get_single("Hospitality Settings")


@frappe.whitelist()
def test_notification():
    settings = get_settings()
    if not settings.booking_confirmation_email_template:
        return "No email template configured. Set one in Hospitality Settings."
    frappe.sendmail(
        recipients=[frappe.session.user],
        subject="[Hospitality] Notification Test",
        message="This is a test notification from Hospitality Settings. Email is configured correctly.",
    )
    return "Test email sent to your account."
