frappe.ui.form.on("Hotel Check-out", {
    booking(frm) {
        if (frm.doc.booking) {
            frappe.db.get_doc("Hotel Booking", frm.doc.booking).then(b => {
                frm.set_value("guest", b.guest);
                frm.set_value("room", b.room);
                frappe.db.get_list("Guest Folio", {
                    filters: { booking: frm.doc.booking, status: "Open" },
                    fields: ["name"]
                }).then(rows => {
                    if (rows.length) frm.set_value("folio", rows[0].name);
                });
            });
        }
    },

    folio(frm) {
        if (frm.doc.folio) {
            frappe.db.get_doc("Guest Folio", frm.doc.folio).then(f => {
                frm.set_value("total_amount", f.total_charges);
                frm.set_value("advance_adjusted", f.advance_paid);
                frm.set_value("net_payable", f.net_payable);
            });
        }
    }
});
