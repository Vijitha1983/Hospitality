import frappe


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    outlet = filters.get("outlet")
    category = filters.get("category")

    columns = [
        {"label": "Menu Item", "fieldname": "menu_item", "fieldtype": "Link", "options": "Menu Item", "width": 180},
        {"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 120},
        {"label": "Qty Sold", "fieldname": "qty_sold", "fieldtype": "Float", "width": 90},
        {"label": "Selling Price", "fieldname": "selling_price", "fieldtype": "Currency", "width": 120},
        {"label": "Food Cost", "fieldname": "food_cost", "fieldtype": "Currency", "width": 110},
        {"label": "Total Revenue", "fieldname": "total_revenue", "fieldtype": "Currency", "width": 130},
        {"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 120},
        {"label": "GP %", "fieldname": "gp_pct", "fieldtype": "Percent", "width": 90},
    ]

    conditions = ["ro.docstatus = 1", "ro.order_date BETWEEN %s AND %s"]
    values = [from_date, to_date]

    if outlet:
        conditions.append("ro.outlet = %s")
        values.append(outlet)
    if category:
        conditions.append("mi.category = %s")
        values.append(category)

    where = " AND ".join(conditions)

    data = frappe.db.sql(f"""
        SELECT
            roi.menu_item,
            mi.category,
            SUM(roi.qty) AS qty_sold,
            mi.selling_price,
            mi.food_cost,
            SUM(roi.qty * mi.selling_price) AS total_revenue,
            SUM(roi.qty * mi.food_cost) AS total_cost
        FROM `tabRestaurant Order Item` roi
        JOIN `tabRestaurant Order` ro ON ro.name = roi.parent
        JOIN `tabMenu Item` mi ON mi.name = roi.menu_item
        WHERE {where}
        GROUP BY roi.menu_item
        ORDER BY total_revenue DESC
    """, values, as_dict=True)

    for row in data:
        if row["total_revenue"]:
            row["gp_pct"] = round((row["total_revenue"] - (row["total_cost"] or 0)) / row["total_revenue"] * 100, 2)
        else:
            row["gp_pct"] = 0

    return columns, data
