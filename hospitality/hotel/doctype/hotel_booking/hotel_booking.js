frappe.ui.form.on("Hotel Booking", {
    refresh(frm) {
        frm.set_query("room", () => ({
            filters: { room_type: frm.doc.room_type, is_active: 1 }
        }));
        frm.set_query("rate_plan", () => ({
            filters: { is_active: 1 }
        }));

        if (!frm.is_new() && frm.doc.status === "Confirmed") {
            frm.add_custom_button(__("Check In"), () => {
                frappe.new_doc("Hotel Check-in", { booking: frm.doc.name, guest: frm.doc.guest });
            }, __("Actions"));

            frm.add_custom_button(__("Add Advance Deposit"), () => {
                frappe.new_doc("Advance Deposit", { booking: frm.doc.name, guest: frm.doc.guest });
            }, __("Actions"));
        }

        if (!frm.is_new() && frm.doc.status === "Checked In") {
            frm.add_custom_button(__("Check Out"), () => {
                frappe.new_doc("Hotel Check-out", { booking: frm.doc.name, guest: frm.doc.guest });
            }, __("Actions"));
            frm.add_custom_button(__("View Folio"), () => {
                frappe.set_route("List", "Guest Folio", { booking: frm.doc.name });
            }, __("Actions"));
        }
    },

    check_in_date(frm) { frm.trigger("_calc_nights"); },
    check_out_date(frm) { frm.trigger("_calc_nights"); },

    _calc_nights(frm) {
        if (frm.doc.check_in_date && frm.doc.check_out_date) {
            const d1 = frappe.datetime.str_to_obj(frm.doc.check_in_date);
            const d2 = frappe.datetime.str_to_obj(frm.doc.check_out_date);
            const nights = frappe.datetime.get_diff(frm.doc.check_out_date, frm.doc.check_in_date);
            frm.set_value("num_nights", nights);
        }
    },

    room_type(frm) {
        if (frm.doc.room_type && frm.doc.check_in_date && frm.doc.check_out_date) {
            frappe.call({
                method: "hospitality.hotel.doctype.hotel_booking.hotel_booking.get_available_rooms",
                args: {
                    room_type: frm.doc.room_type,
                    check_in_date: frm.doc.check_in_date,
                    check_out_date: frm.doc.check_out_date
                },
                callback(r) {
                    if (r.message && r.message.length === 0) {
                        frappe.msgprint(__("No rooms available for selected type and dates."));
                    }
                }
            });
        }
    }
});
