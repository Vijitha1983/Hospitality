# Hospitality — ERPNext Hotel, Restaurant & Bar Management

A full-featured custom Frappe application built on **ERPNext v15**, covering Hotel, Restaurant, and Bar operations in a single integrated system.

---

## Modules

| Module | DocTypes | Description |
|--------|----------|-------------|
| **Hotel** | Room Type, Room, Rate Plan, Hotel Booking, Hotel Check-in, Hotel Check-out, Guest Folio, Folio Posting, Advance Deposit, Housekeeping Task | Full PMS — reservations, check-in/out, folio billing, housekeeping |
| **Restaurant** | Dining Table, Table Section, Table Reservation, Food Menu, Menu Item, Restaurant Order, KOT, KOT Item | Table management, order taking, kitchen printing, POS billing |
| **Bar** | Bar Tab, Bar Order, Drink Menu Item, Cocktail Recipe, BOT, Liquor Stock Entry, Excise Register, Bar Shift Report | Tab management, BOT (Bar Order Ticket), excise compliance, shift reporting |
| **Shared** | Guest, Outlet, Charge Type, Hospitality Settings | Common master data and configuration |

---

## Client Apps (in `/apps`)

Three native apps connect to ERPNext via REST API:

| App | Platform | Users | Run |
|-----|----------|-------|-----|
| **Hotel Desk** | Windows (PyQt6) | Receptionists | `python apps/hotel_desk/main.py` |
| **Restaurant POS** | Windows (PyQt6) | Cashiers & Managers | `python apps/restaurant_pos/main.py` |
| **Table Order** | Android / Tablet (Kivy) | Waiters | `python apps/table_order/main.py` |

### Architecture

```
ERPNext / Frappe Server
├── hospitality/hotel/api.py         ← Hotel REST API
├── hospitality/restaurant/api.py    ← Restaurant REST API
└── hospitality/bar/api.py           ← Bar REST API
          ↑  HTTP (token auth)
apps/shared/frappe_client.py         ← Shared REST client
├── apps/hotel_desk/                 ← PyQt6 Windows app
├── apps/restaurant_pos/             ← PyQt6 Windows app
└── apps/table_order/                ← Kivy mobile app
```

---

## Features

### Hotel
- Room availability search with date-range conflict checking
- Multi-rate-plan pricing (Rack, Corporate, OTA, etc.)
- Guest folio with real-time charge posting (room, F&B, minibar, laundry, etc.)
- Nightly room charge auto-posting via scheduler
- Advance deposit collection and tracking
- Housekeeping task auto-generation (daily scheduler)
- Occupancy, Revenue, and Arrival/Departure reports

### Restaurant
- Table grid with real-time status (Available / Occupied / Reserved)
- Multi-station KOT (Hot Kitchen, Cold Kitchen, Bar, etc.)
- Room service integration — posts charges directly to guest folio
- BOM-based stock consumption on order submit
- Food cost report
- Restaurant POS page + Table Order page (in-browser)

### Bar
- Tab-based ordering (Counter Tab, Table Tab, Room Tab)
- BOT (Bar Order Ticket) for barista/bar workflow
- Happy hour pricing (auto-triggered by scheduler)
- Cocktail recipe management with ingredient tracking
- Liquor stock entry with par-level alerts
- Excise register (daily auto-compiled)
- Bar shift report with variance analysis
- Bar POS page (in-browser)

---

## Installation

### Prerequisites
- Frappe Bench with ERPNext v15
- Python 3.11+

### Frappe App

```bash
# Get the app
cd /path/to/bench
bench get-app https://github.com/Vijitha1983/Hospitality.git

# Install on a site
bench --site your.site.com install-app hospitality

# Migrate
bench --site your.site.com migrate
```

### Client Apps (Windows)

```bash
cd apps
pip install -r requirements.txt
```

Edit `apps/shared/config.py` with your server details:

```python
SERVER_URL = "http://your-erpnext-server:8000"
API_KEY    = "generate_from_erpnext_user_settings"
API_SECRET = "generate_from_erpnext_user_settings"
```

> **API credentials:** In ERPNext, go to **User → API Access** and generate an API Key + Secret for the service account.

Run the apps:

```bash
python apps/hotel_desk/main.py
python apps/restaurant_pos/main.py
python apps/table_order/main.py   # requires kivy
```

### Table Order App — Android packaging

```bash
pip install buildozer
cd apps/table_order
buildozer android debug
```

---

## ERPNext Integration

All modules integrate natively with ERPNext:

| ERPNext Module | Usage |
|----------------|-------|
| **Accounting** | POS Invoices, Sales Invoices, payment entries |
| **Stock** | Material issue on F&B order, liquor stock entries |
| **POS** | POS Profiles and POS Invoices for all outlets |
| **CRM** | Guest → Customer auto-creation |
| **HR** | Staff assignments (bartender, waiter, housekeeper) |

No core ERPNext DocTypes are modified — integration uses Frappe hooks and `doc_events`.

---

## Scheduled Jobs

| Frequency | Job |
|-----------|-----|
| Daily | Auto-create housekeeping tasks, post nightly room charges, compile excise register |
| Hourly | Check and apply happy hour pricing |

---

## Print Formats

| Format | DocType | Description |
|--------|---------|-------------|
| Folio Bill | Guest Folio | Full guest statement with charges/payments |
| KOT Ticket | KOT | 80mm thermal kitchen ticket |
| Bar Bill | Bar Tab | Tab summary bill |

---

## Project Structure

```
hospitality/                  ← Frappe app root
├── hospitality/              ← Python package
│   ├── hotel/                ← Hotel module
│   ├── restaurant/           ← Restaurant module
│   ├── bar/                  ← Bar module
│   ├── shared/               ← Shared DocTypes
│   ├── utils/                ← Utility functions
│   ├── hooks.py
│   └── install.py
├── apps/                     ← Native client apps
│   ├── shared/               ← Shared REST client
│   ├── hotel_desk/           ← PyQt6 Hotel Desk
│   ├── restaurant_pos/       ← PyQt6 Restaurant POS
│   └── table_order/          ← Kivy Table Order (Android)
├── setup.py
└── requirements.txt
```

---

## License

MIT — © Vijitha Rajapaksha
