app_name = "hospitality"
app_title = "Hospitality"
app_publisher = "Vijitha Rajapaksha"
app_description = "ERPNext Hotel, Restaurant and Bar Management Module"
app_email = "vijitha.rajapaksha@gmail.com"
app_license = "MIT"

# ─── DocType Events ────────────────────────────────────────────────────────────
doc_events = {
    "Hotel Check-out": {
        "on_submit": [
            "hospitality.hotel.doctype.hotel_check_out.hotel_check_out.on_submit"
        ]
    },
    "Advance Deposit": {
        "on_submit": [
            "hospitality.hotel.doctype.advance_deposit.advance_deposit.on_submit"
        ]
    },
    "Guest": {
        "after_insert": [
            "hospitality.shared.doctype.guest.guest.create_customer"
        ]
    },
    "Restaurant Order": {
        "on_submit": [
            "hospitality.restaurant.doctype.restaurant_order.restaurant_order.on_submit"
        ]
    },
    "Bar Order": {
        "on_submit": [
            "hospitality.bar.doctype.bar_order.bar_order.on_submit"
        ]
    },
    "Liquor Stock Entry": {
        "on_submit": [
            "hospitality.bar.doctype.liquor_stock_entry.liquor_stock_entry.check_par_level"
        ]
    },
}

# ─── Scheduled Jobs ────────────────────────────────────────────────────────────
scheduler_events = {
    "daily": [
        "hospitality.hotel.doctype.housekeeping_task.housekeeping_task.auto_create_daily_tasks",
        "hospitality.hotel.doctype.guest_folio.guest_folio.post_nightly_room_charges",
        "hospitality.bar.doctype.excise_register.excise_register.compile_daily_register",
    ],
    "hourly": [
        "hospitality.bar.doctype.drink_menu_item.drink_menu_item.check_happy_hour",
    ],
}

# ─── App Includes ──────────────────────────────────────────────────────────────
app_include_css = "/assets/hospitality/css/hospitality.css"
app_include_js = "/assets/hospitality/js/hospitality.js"

# ─── Install / Uninstall Hooks ────────────────────────────────────────────────
after_install = "hospitality.install.after_install"

# ─── Override Whitelisted Methods ──────────────────────────────────────────────
override_whitelisted_methods = {}

# ─── Fixtures ─────────────────────────────────────────────────────────────────
fixtures = [
    "Role",
    {"dt": "Charge Type"},
    {"dt": "Print Format", "filters": [["module", "in", ["Hotel", "Restaurant", "Bar", "Shared"]]]},
    {"dt": "Workspace", "filters": [["module", "in", ["Hotel", "Restaurant", "Bar", "Shared"]]]},
]
