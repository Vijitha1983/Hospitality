frappe.ui.form.on("Excise Register", {
    refresh(frm) {
        frm.set_query("outlet", () => ({
            filters: { outlet_type: "Bar", is_active: 1 }
        }));

        if (!frm.is_new() && frm.doc.docstatus === 1 && !frm.doc.is_submitted) {
            frm.add_custom_button(__("Final Lock Submission"), () => {
                frappe.confirm(
                    "This will permanently lock the Excise Register. This cannot be undone. Proceed?",
                    () => {
                        frappe.call({
                            method: "frappe.client.set_value",
                            args: {
                                doctype: "Excise Register", name: frm.doc.name,
                                fieldname: { is_submitted: 1, submitted_by: frappe.session.user }
                            },
                            callback() { frm.reload_doc(); }
                        });
                    }
                );
            }).addClass("btn-danger");
        }
    }
});

frappe.ui.form.on("Excise Sales Line", {
    qty_bottles(frm, cdt, cdn) { frm.trigger("_calc_line", cdt, cdn); },
    rate(frm, cdt, cdn) { frm.trigger("_calc_line", cdt, cdn); },
    _calc_line(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "value", (row.qty_bottles || 0) * (row.rate || 0));
    }
});
