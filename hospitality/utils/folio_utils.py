import frappe
from frappe.utils import today, now_datetime


def create_sales_invoice_from_folio(folio):
    settings = frappe.get_single("Hospitality Settings")
    customer = frappe.db.get_value("Guest", folio.guest, "customer")
    if not customer:
        frappe.throw(f"No Customer linked to Guest {folio.guest}. Please check Guest master.")

    outlet = frappe.db.get_single_value("Hospitality Settings", "hotel_outlet")
    tax_template = frappe.db.get_value("Outlet", outlet, "tax_template") if outlet else None

    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": customer,
        "posting_date": today(),
        "due_date": today(),
        "company": settings.company,
        "remarks": f"Hotel Folio: {folio.name} | Booking: {folio.booking}",
    })

    if tax_template:
        si.taxes_and_charges = tax_template

    for posting in folio.postings:
        if posting.is_complimentary:
            continue
        income_account = frappe.db.get_value("Charge Type", posting.charge_type, "default_income_account")
        si.append("items", {
            "item_name": posting.description,
            "description": posting.description,
            "qty": posting.qty,
            "rate": posting.rate,
            "amount": posting.amount,
            "income_account": income_account,
        })

    if not si.items:
        frappe.throw("No billable items found in folio.")

    si.insert(ignore_permissions=True)
    si.submit()
    return si


def create_payment_entry_for_folio(folio, amount, settlement_mode):
    settings = frappe.get_single("Hospitality Settings")
    customer = frappe.db.get_value("Guest", folio.guest, "customer")

    mode_map = {
        "Cash": "Cash",
        "Credit Card": "Bank",
        "UPI": "Bank",
        "Bank Transfer": "Bank",
        "Direct Bill": "Bank",
    }
    payment_type = mode_map.get(settlement_mode, "Bank")

    pe = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Receive",
        "posting_date": today(),
        "company": settings.company,
        "party_type": "Customer",
        "party": customer,
        "paid_amount": amount,
        "received_amount": amount,
        "mode_of_payment": settlement_mode,
        "reference_no": folio.name,
        "reference_date": today(),
        "remarks": f"Settlement for Folio {folio.name}",
    })
    pe.insert(ignore_permissions=True)
    pe.submit()
    return pe


def create_advance_payment_entry(deposit):
    settings = frappe.get_single("Hospitality Settings")
    customer = frappe.db.get_value("Guest", deposit.guest, "customer")

    pe = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Receive",
        "posting_date": deposit.deposit_date,
        "company": settings.company,
        "party_type": "Customer",
        "party": customer,
        "paid_amount": deposit.amount,
        "received_amount": deposit.amount,
        "mode_of_payment": deposit.payment_mode,
        "reference_no": deposit.reference_no or deposit.name,
        "reference_date": deposit.deposit_date,
        "remarks": f"Advance deposit for Booking {deposit.booking}",
    })
    pe.insert(ignore_permissions=True)
    pe.submit()
    return pe
