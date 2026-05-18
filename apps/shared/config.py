"""
Server configuration — edit these before running any app.
Credentials: generate API Key + API Secret from ERPNext > User > API Access.
"""
import os

SERVER_URL = os.getenv("FRAPPE_URL", "http://localhost:8000")
API_KEY    = os.getenv("FRAPPE_API_KEY", "your_api_key_here")
API_SECRET = os.getenv("FRAPPE_API_SECRET", "your_api_secret_here")

# Defaults loaded on first run (user can override in each app's settings dialog)
DEFAULT_HOTEL_OUTLET      = os.getenv("HOTEL_OUTLET", "")
DEFAULT_RESTAURANT_OUTLET = os.getenv("RESTAURANT_OUTLET", "")
DEFAULT_BAR_OUTLET        = os.getenv("BAR_OUTLET", "")
