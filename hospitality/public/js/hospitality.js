/* Hospitality Module — Global Client Script */

// Extend frappe with hospitality helpers
frappe.provide("hospitality");

hospitality.format_room_status = function(status) {
    const colors = {
        "Vacant Clean": "green",
        "Vacant Dirty": "orange",
        "Occupied": "red",
        "Out of Order": "grey",
        "Maintenance": "yellow",
    };
    const color = colors[status] || "blue";
    return `<span class="indicator-pill ${color}">${status}</span>`;
};

hospitality.format_table_status = function(status) {
    const colors = {
        "Available": "green",
        "Occupied": "red",
        "Reserved": "orange",
        "Dirty": "grey",
        "Blocked": "darkgrey",
    };
    const color = colors[status] || "blue";
    return `<span class="indicator-pill ${color}">${status}</span>`;
};

hospitality.open_new_bar_order = function(tab_name, outlet) {
    frappe.new_doc("Bar Order", { tab: tab_name, outlet: outlet });
};

hospitality.open_new_restaurant_order = function(table, outlet) {
    frappe.new_doc("Restaurant Order", { table: table, outlet: outlet });
};

// Quick check-in shortcut — called from hotel booking form
hospitality.quick_checkin = function(booking_name) {
    frappe.new_doc("Hotel Check-in", { booking: booking_name });
};

// Real-time KOT refresh every 30 seconds (for kitchen screens using KOT list view)
if (frappe.get_route()[0] === "List" && frappe.get_route()[1] === "KOT") {
    setInterval(() => {
        if (cur_list) cur_list.refresh();
    }, 30000);
}
