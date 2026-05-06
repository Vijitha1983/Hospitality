frappe.ui.form.on("Advance Deposit", {
    refresh(frm) {
        frm.set_query("booking", () => ({
            filters: { status: ["in", ["Confirmed", "Checked In"]] }
        }));

        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("View Payment Entry"), () => {
                frappe.set_route("List", "Payment Entry", { reference_no: frm.doc.name });
            });
        }
    },

    booking(frm) {
        if (frm.doc.booking) {
            frappe.db.get_value("Hotel Booking", frm.doc.booking, ["guest", "total_amount", "advance_paid"]).then(r => {
                if (r.message) {
                    frm.set_value("guest", r.message.guest);
                    const balance = (r.message.total_amount || 0) - (r.message.advance_paid || 0);
                    frm.set_df_property("amount", "description", `Balance due: ${format_currency(balance)}`);
                }
            });
        }
    }
});
