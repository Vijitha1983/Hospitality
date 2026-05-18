import frappe


def after_install():
    _create_roles()
    _create_hospitality_settings()
    frappe.db.commit()


def _create_roles():
    roles = [
        ("Hotel Manager", 1),
        ("Hotel Receptionist", 1),
        ("Restaurant Manager", 1),
        ("Restaurant Cashier", 1),
        ("Bar Manager", 1),
        ("Bartender", 1),
        ("Housekeeping Staff", 0),
    ]
    for role_name, desk_access in roles:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": desk_access,
            }).insert(ignore_permissions=True)


def _create_hospitality_settings():
    if not frappe.db.exists("Hospitality Settings", "Hospitality Settings"):
        doc = frappe.new_doc("Hospitality Settings")
        doc.checkin_time = "14:00:00"
        doc.checkout_time = "12:00:00"
        doc.flags.ignore_mandatory = True
        doc.insert(ignore_permissions=True)
