frappe.ui.form.on("BOT", {
    refresh(frm) {
        if (frm.doc.status === "Pending") {
            frm.add_custom_button(__("Start Preparation"), () => {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: { doctype: "BOT", name: frm.doc.name, fieldname: "status", value: "In Preparation" },
                    callback() { frm.reload_doc(); }
                });
            }).addClass("btn-warning");
        }

        if (frm.doc.status === "In Preparation") {
            frm.add_custom_button(__("Mark Ready"), () => {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: { doctype: "BOT", name: frm.doc.name, fieldname: "status", value: "Ready" },
                    callback() { frm.reload_doc(); }
                });
            }).addClass("btn-success");
        }

        if (frm.doc.status === "Ready") {
            frm.add_custom_button(__("Mark Served"), () => {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: {
                        doctype: "BOT", name: frm.doc.name,
                        fieldname: { status: "Served", ready_at: frappe.datetime.now_datetime() }
                    },
                    callback() { frm.reload_doc(); }
                });
            }).addClass("btn-primary");
        }
    }
});
