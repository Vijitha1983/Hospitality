frappe.ui.form.on("Outlet", {
    refresh(frm) {
        frm.set_query("cost_centre", () => ({
            filters: { company: frm.doc.property }
        }));
        frm.set_query("default_warehouse", () => ({
            filters: { company: frm.doc.property }
        }));
    }
});
