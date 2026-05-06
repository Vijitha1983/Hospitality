frappe.ui.form.on("KOT", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.status === "Pending") {
            frm.add_custom_button(__("Start Preparation"), () => {
                frm.set_value("status", "In Preparation");
                frm.save();
            });
        }
        if (!frm.is_new() && frm.doc.status === "In Preparation") {
            frm.add_custom_button(__("Mark Ready"), () => {
                frm.set_value("status", "Ready");
                frm.save();
            });
        }
    }
});
