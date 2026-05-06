frappe.ui.form.on("Food Menu", {
    refresh(frm) {
        frm.set_query("outlet", () => ({
            filters: { is_active: 1 }
        }));

        if (!frm.is_new() && frm.doc.is_active) {
            frm.add_custom_button(__("Preview Menu"), () => {
                frappe.set_route("List", "Menu Item", { food_menu: frm.doc.name, is_active: 1 });
            });
        }
    }
});
