frappe.ui.form.on("Room", {
    refresh(frm) {
        if (!frm.is_new()) {
            if (frm.doc.current_status === "Vacant Dirty") {
                frm.add_custom_button(__("Mark Clean"), () => {
                    frappe.confirm("Mark this room as Vacant Clean?", () => {
                        frappe.call({
                            method: "hospitality.hotel.doctype.room.room.mark_clean",
                            args: { room: frm.doc.name },
                            callback: () => frm.reload_doc()
                        });
                    });
                }, __("Actions"));
            }
            frm.add_custom_button(__("Housekeeping Tasks"), () => {
                frappe.set_route("List", "Housekeeping Task", { room: frm.doc.name });
            });
        }
    },

    current_status(frm) {
        if (frm.doc.current_status === "Out of Order") {
            frappe.show_alert({ message: __("Room will be flagged for maintenance."), indicator: "orange" });
        }
    }
});
