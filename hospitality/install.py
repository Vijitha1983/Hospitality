import frappe


def after_install():
    _create_default_roles()
    _seed_charge_types()
    _create_default_hospitality_settings()
    frappe.db.commit()
    print("Hospitality app installed successfully.")


def _create_default_roles():
    roles = [
        "Hotel Manager", "Hotel User",
        "Restaurant Manager", "Restaurant User",
        "Bar Manager", "Bar User",
        "Housekeeping User", "Kitchen User", "Bartender",
    ]
    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)


def _seed_charge_types():
    defaults = [
        {"charge_name": "Room Rent", "charge_category": "Room", "is_taxable": 1},
        {"charge_name": "Food & Beverage", "charge_category": "Food and Beverage", "is_taxable": 1},
        {"charge_name": "Bar & Beverages", "charge_category": "Food and Beverage", "is_taxable": 1},
        {"charge_name": "Laundry", "charge_category": "Laundry", "is_taxable": 1},
        {"charge_name": "Minibar", "charge_category": "Minibar", "is_taxable": 1},
        {"charge_name": "Telephone", "charge_category": "Telephone", "is_taxable": 0},
        {"charge_name": "Transport", "charge_category": "Transport", "is_taxable": 1},
        {"charge_name": "Spa & Wellness", "charge_category": "Spa", "is_taxable": 1},
        {"charge_name": "Banquet", "charge_category": "Miscellaneous", "is_taxable": 1},
        {"charge_name": "Miscellaneous", "charge_category": "Miscellaneous", "is_taxable": 0},
    ]
    for ct in defaults:
        if not frappe.db.exists("Charge Type", ct["charge_name"]):
            doc = frappe.get_doc({"doctype": "Charge Type", "is_active": 1, **ct})
            doc.insert(ignore_permissions=True)


def _create_default_hospitality_settings():
    if not frappe.db.exists("Hospitality Settings", "Hospitality Settings"):
        settings = frappe.get_doc({
            "doctype": "Hospitality Settings",
            "hotel_name": "My Hotel",
            "check_in_time": "14:00:00",
            "check_out_time": "12:00:00",
            "advance_deposit_pct": 30,
            "loyalty_silver_threshold": 500,
            "loyalty_gold_threshold": 2000,
            "loyalty_platinum_threshold": 5000,
        })
        settings.insert(ignore_permissions=True)
