frappe.ui.form.on("Guest Folio", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.status === "Open") {
            frm.add_custom_button(__("Add Charge"), () => {
                const d = new frappe.ui.Dialog({
                    title: __("Add Folio Charge"),
                    fields: [
                        { fieldtype: "Link", fieldname: "charge_type", label: __("Charge Type"), options: "Charge Type", reqd: 1 },
                        { fieldtype: "Data", fieldname: "description", label: __("Description"), reqd: 1 },
                        { fieldtype: "Link", fieldname: "outlet", label: __("Outlet"), options: "Outlet" },
                        { fieldtype: "Float", fieldname: "qty", label: __("Qty"), default: 1 },
                        { fieldtype: "Currency", fieldname: "rate", label: __("Rate"), reqd: 1 },
                    ],
                    primary_action_label: __("Post"),
                    primary_action(values) {
                        frappe.call({
                            method: "hospitality.hotel.doctype.guest_folio.guest_folio.post_charge_api",
                            args: { folio: frm.doc.name, ...values },
                            callback() { d.hide(); frm.reload_doc(); }
                        });
                    }
                });
                d.show();
            });
        }
    }
});
