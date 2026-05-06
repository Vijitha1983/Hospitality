frappe.ui.form.on("Dining Table", {
    refresh(frm) {
        frm.set_query("section", () => ({
            filters: { outlet: frm.doc.outlet }
        }));

        if (frm.doc.current_order) {
            frm.add_custom_button(__("View Current Order"), () => {
                frappe.set_route("Form", "Restaurant Order", frm.doc.current_order);
            }).addClass("btn-primary");
        }

        if (!frm.is_new() && frm.doc.current_status === "Dirty") {
            frm.add_custom_button(__("Mark Clean"), () => {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: { doctype: "Dining Table", name: frm.doc.name, fieldname: "current_status", value: "Available" },
                    callback() { frm.reload_doc(); }
                });
            }).addClass("btn-success");
        }

        const colors = { Available: "green", Occupied: "red", Reserved: "orange", Dirty: "grey", Blocked: "darkred" };
        const status = frm.doc.current_status;
        if (status && colors[status]) {
            frm.dashboard.set_headline_alert(
                `<div class="alert" style="background:${colors[status]};color:white;font-weight:bold;">${status}</div>`
            );
        }
    }
});
