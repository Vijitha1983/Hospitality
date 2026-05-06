frappe.ui.form.on("Rate Plan", {
    refresh(frm) {
        frm.set_query("company", () => ({}));
    }
});

frappe.ui.form.on("Rate Plan Room Rate", {
    room_type(frm, cdt, cdn) {
        // room_type selected — rate may be populated from room type default
    },
    rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.weekend_rate) {
            frappe.model.set_value(cdt, cdn, "weekend_rate", row.rate);
        }
    }
});
