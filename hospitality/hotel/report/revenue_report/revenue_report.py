import frappe


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    outlet = filters.get("outlet")
    charge_type = filters.get("charge_type")

    columns = [
        {"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": "Charge Type", "fieldname": "charge_type", "fieldtype": "Data", "width": 140},
        {"label": "Outlet", "fieldname": "outlet", "fieldtype": "Data", "width": 130},
        {"label": "Transactions", "fieldname": "txn_count", "fieldtype": "Int", "width": 110},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 130},
    ]

    conditions = ["fp.posting_date BETWEEN %s AND %s"]
    values = [from_date, to_date]

    if outlet:
        conditions.append("fp.outlet = %s")
        values.append(outlet)
    if charge_type:
        conditions.append("fp.charge_type = %s")
        values.append(charge_type)

    where = " AND ".join(conditions)

    data = frappe.db.sql(f"""
        SELECT fp.posting_date, fp.charge_type, fp.outlet,
               COUNT(fp.name) AS txn_count,
               SUM(fp.amount) AS amount
        FROM `tabFolio Posting` fp
        WHERE {where}
        GROUP BY fp.posting_date, fp.charge_type, fp.outlet
        ORDER BY fp.posting_date, fp.charge_type
    """, values, as_dict=True)

    return columns, data
