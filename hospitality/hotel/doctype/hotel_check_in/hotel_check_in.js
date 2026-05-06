frappe.ui.form.on("Hotel Check-in", {
    booking(frm) {
        if (frm.doc.booking) {
            frappe.db.get_doc("Hotel Booking", frm.doc.booking).then(doc => {
                frm.set_value("guest", doc.guest);
                frm.set_value("room", doc.room || "");
            });
        }
    },

    refresh(frm) {
        frm.set_query("room", () => ({
            filters: {
                current_status: ["in", ["Vacant Clean", "Vacant Dirty"]],
                is_active: 1
            }
        }));
    }
});
