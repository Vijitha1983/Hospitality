frappe.ui.form.on("Banquet Booking", {
    refresh(frm) {
        frm.set_query("venue", () => ({
            filters: { outlet_type: "Banquet", is_active: 1 }
        }));
        frm.set_query("guest", () => ({}));

        if (!frm.is_new() && frm.doc.status === "Tentative") {
            frm.add_custom_button(__("Confirm Booking"), () => {
                frm.set_value("status", "Confirmed");
                frm.save();
            }).addClass("btn-success");
        }

        if (!frm.is_new() && ["Confirmed", "Completed"].includes(frm.doc.status) && frm.doc.docstatus !== 1) {
            frm.add_custom_button(__("Submit & Invoice"), () => {
                frm.savesubmit();
            }, __("Actions"));
        }

        if (frm.doc.docstatus === 1 && !frm.doc.sales_invoice) {
            frm.add_custom_button(__("Create Sales Invoice"), () => {
                frappe.call({
                    method: "hospitality.shared.doctype.banquet_booking.banquet_booking.create_invoice",
                    args: { booking: frm.doc.name },
                    callback(r) { if (r.message) frm.reload_doc(); }
                });
            }, __("Actions"));
        }
    },

    guest(frm) {
        if (frm.doc.guest) {
            frappe.db.get_value("Guest", frm.doc.guest, ["full_name", "mobile_no", "email"]).then(r => {
                if (r.message) {
                    frm.set_value("contact_name", r.message.full_name);
                    frm.set_value("contact_phone", r.message.mobile_no);
                    frm.set_value("contact_email", r.message.email);
                }
            });
        }
    }
});

frappe.ui.form.on("Banquet Package Item", {
    qty(frm, cdt, cdn) { frm.trigger("_calc_line", cdt, cdn); },
    rate(frm, cdt, cdn) { frm.trigger("_calc_line", cdt, cdn); },
    _calc_line(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", (row.qty || 0) * (row.rate || 0));
        frm.trigger("_calc_total");
    },
    _calc_total(frm) {
        let total = 0;
        (frm.doc.package_items || []).forEach(r => { total += r.amount || 0; });
        frm.set_value("total_amount", total);
        frm.set_value("balance_due", total - (frm.doc.advance_paid || 0));
    }
});
