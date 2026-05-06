import frappe
from frappe.model.document import Document


class FolioPosting(Document):
    def validate(self):
        self.amount = (self.qty or 0) * (self.rate or 0)
        if self.is_complimentary and not self.authorised_by:
            frappe.throw("Authorised By is required for complimentary postings.")
