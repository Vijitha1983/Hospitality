import frappe


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    outlet = filters.get("outlet")

    columns = [
        {"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 200},
        {"label": "Outlet", "fieldname": "outlet", "fieldtype": "Data", "width": 130},
        {"label": "Total Received", "fieldname": "total_received", "fieldtype": "Float", "width": 120},
        {"label": "Total Sales", "fieldname": "total_sales", "fieldtype": "Float", "width": 110},
        {"label": "Theoretical Closing", "fieldname": "theoretical_closing", "fieldtype": "Float", "width": 140},
        {"label": "Actual Closing", "fieldname": "actual_closing", "fieldtype": "Float", "width": 120},
        {"label": "Variance", "fieldname": "variance", "fieldtype": "Float", "width": 100},
        {"label": "Variance %", "fieldname": "variance_pct", "fieldtype": "Percent", "width": 100},
    ]

    outlet_cond = ""
    values = [from_date, to_date]
    if outlet:
        outlet_cond = "AND lse.outlet = %s"
        values.append(outlet)

    data = frappe.db.sql(f"""
        SELECT
            lsi.item,
            lse.outlet,
            SUM(lsi.received_qty) AS total_received,
            SUM(lsi.sales_qty) AS total_sales,
            SUM(lsi.opening_qty) + SUM(lsi.received_qty) - SUM(lsi.sales_qty) AS theoretical_closing,
            SUM(lsi.closing_qty) AS actual_closing,
            SUM(lsi.variance) AS variance
        FROM `tabLiquor Stock Item` lsi
        JOIN `tabLiquor Stock Entry` lse ON lse.name = lsi.parent
        WHERE lse.docstatus = 1
          AND lse.entry_date BETWEEN %s AND %s
          {outlet_cond}
        GROUP BY lsi.item, lse.outlet
        ORDER BY ABS(SUM(lsi.variance)) DESC
    """, values, as_dict=True)

    for row in data:
        if row["theoretical_closing"]:
            row["variance_pct"] = round((row["variance"] or 0) / row["theoretical_closing"] * 100, 2)
        else:
            row["variance_pct"] = 0

    return columns, data
