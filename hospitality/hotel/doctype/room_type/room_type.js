frappe.ui.form.on("Room Type", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("View Rooms"), () => {
                frappe.set_route("List", "Room", { room_type: frm.doc.name });
            });
        }
    }
});
