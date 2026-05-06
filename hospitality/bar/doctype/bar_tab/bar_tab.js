frappe.ui.form.on("Bar Tab", {
    refresh(frm) {
        frm.set_query("table", () => ({
            filters: { outlet: frm.doc.outlet }
        }));

        if (!frm.is_new() && frm.doc.status === "Open") {
            frm.add_custom_button(__("New Bar Order"), () => {
                frappe.new_doc("Bar Order", { tab: frm.doc.name, outlet: frm.doc.outlet });
            }, __("Actions"));

            frm.add_custom_button(__("View Orders"), () => {
                frappe.set_route("List", "Bar Order", { tab: frm.doc.name });
            }, __("Actions"));

            frm.add_custom_button(__("Close Tab & Bill"), () => {
                frappe.confirm(
                    `Close tab and generate POS Invoice for ${frappe.format(frm.doc.total_amount, { fieldtype: "Currency" })}?`,
                    () => {
                        frappe.call({
                            method: "hospitality.bar.doctype.bar_tab.bar_tab.close_and_bill",
                            args: { tab: frm.doc.name },
                            callback(r) { if (r.message) frm.reload_doc(); }
                        });
                    }
                );
            }, __("Actions"));
        }

        if (frm.doc.status === "Open") {
            frm.dashboard.set_headline_alert(
                `<div class="alert alert-warning">Tab is OPEN — Total: ${frappe.format(frm.doc.total_amount, { fieldtype: "Currency" })}</div>`
            );
        }
    },

    tab_type(frm) {
        frm.set_df_property("table", "reqd", frm.doc.tab_type === "Table Tab");
    }
});
