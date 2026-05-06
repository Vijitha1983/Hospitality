frappe.ui.form.on("Table Reservation", {
    refresh(frm) {
        frm.set_query("table", () => ({
            filters: { outlet: frm.doc.outlet, is_active: 1 }
        }));
        frm.set_query("guest", () => ({}));

        if (!frm.is_new() && frm.doc.status === "Confirmed") {
            frm.add_custom_button(__("Seat Now"), () => {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: { doctype: "Table Reservation", name: frm.doc.name, fieldname: "status", value: "Seated" },
                    callback() { frm.reload_doc(); }
                });
            }).addClass("btn-success");

            frm.add_custom_button(__("Mark No Show"), () => {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: { doctype: "Table Reservation", name: frm.doc.name, fieldname: "status", value: "No Show" },
                    callback() { frm.reload_doc(); }
                });
            });
        }
    },

    guest(frm) {
        if (frm.doc.guest) {
            frappe.db.get_value("Guest", frm.doc.guest, ["full_name", "mobile_no", "email"]).then(r => {
                if (r.message) {
                    frm.set_value("guest_name", r.message.full_name);
                    frm.set_value("contact_phone", r.message.mobile_no);
                }
            });
        }
    }
});
