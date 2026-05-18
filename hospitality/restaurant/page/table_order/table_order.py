import frappe
from frappe.utils import now_datetime, flt

# Reuse restaurant_pos backend methods where possible
from hospitality.restaurant.page.restaurant_pos.restaurant_pos import (
    get_outlets,
    get_tables,
    get_menu_categories,
    get_menu_items,
    get_active_order,
    new_order,
    add_item,
    remove_item,
    update_qty,
    fire_kot,
)


@frappe.whitelist()
def get_steward_tables(outlet):
    """Returns tables with open orders for steward view."""
    tables = frappe.get_all(
        "Dining Table",
        filters={"outlet": outlet, "is_active": 1},
        fields=["name", "table_number", "seating_capacity", "current_status", "current_order"],
        order_by="table_number",
    )
    for t in tables:
        if t.current_order:
            t["order_total"] = (
                frappe.db.get_value("Restaurant Order", t.current_order, "total_amount") or 0
            )
        else:
            t["order_total"] = 0
    return tables


@frappe.whitelist()
def get_pending_items(order):
    """Items in an order that are still Pending (not yet sent to kitchen)."""
    return frappe.get_all(
        "KOT Item",
        filters={"parent": order, "status": "Pending"},
        fields=["name", "menu_item", "item_name", "qty", "rate", "amount", "special_instructions"],
    )


@frappe.whitelist()
def get_sent_items(order):
    """Items already fired to the kitchen (non-Pending, non-Void)."""
    return frappe.get_all(
        "KOT Item",
        filters={"parent": order, "status": ["in", ["In Preparation", "Ready", "Served"]]},
        fields=["name", "menu_item", "item_name", "qty", "rate", "amount", "status"],
    )


@frappe.whitelist()
def mark_served(order, row_name):
    """Steward marks an item as Served."""
    doc = frappe.get_doc("Restaurant Order", order)
    for row in doc.items:
        if row.name == row_name and row.status == "Ready":
            row.status = "Served"
            break
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "ok"}
