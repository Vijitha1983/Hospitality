frappe.ui.form.on("Housekeeping Task", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.status === "Pending") {
            frm.add_custom_button(__("Start Task"), () => {
                frm.set_value("status", "In Progress");
                frm.set_value("start_time", frappe.datetime.now_time());
                frm.save();
            });
        }
        if (!frm.is_new() && frm.doc.status === "In Progress") {
            frm.add_custom_button(__("Mark Done"), () => {
                frm.set_value("status", "Done");
                frm.set_value("end_time", frappe.datetime.now_time());
                frm.save();
            });
        }
    }
});
