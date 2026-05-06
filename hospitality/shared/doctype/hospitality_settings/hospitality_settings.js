frappe.ui.form.on("Hospitality Settings", {
    refresh(frm) {
        frm.set_df_property("hotel_name", "bold", 1);
        frm.add_custom_button(__("Test Notification Settings"), () => {
            frappe.call({
                method: "hospitality.shared.doctype.hospitality_settings.hospitality_settings.test_notification",
                callback(r) {
                    frappe.msgprint(r.message || "Notification test complete.");
                }
            });
        });
    }
});
