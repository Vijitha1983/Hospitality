frappe.ui.form.on("Guest", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("View Bookings"), () => {
                frappe.set_route("List", "Hotel Booking", { guest: frm.doc.name });
            });
            frm.add_custom_button(__("View Folio History"), () => {
                frappe.set_route("List", "Guest Folio", { guest: frm.doc.name });
            });
        }
    },

    is_blacklisted(frm) {
        if (frm.doc.is_blacklisted && !frm.doc.blacklist_reason) {
            frappe.msgprint(__("Please provide a reason for blacklisting this guest."));
        }
    },
});
