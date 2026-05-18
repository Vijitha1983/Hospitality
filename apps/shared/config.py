"""
App configuration defaults — override with environment variables.

Authentication is username/password (session-based).
Credentials are saved per-app in ~/.hospitality/credentials.json by the login window.
"""
import os

# Default server URL shown in the login dialog (user can change it)
DEFAULT_SERVER_URL = os.getenv("FRAPPE_URL", "https://")

# Pre-select an outlet after login (leave empty to show outlet picker)
DEFAULT_RESTAURANT_OUTLET = os.getenv("RESTAURANT_OUTLET", "")
DEFAULT_BAR_OUTLET        = os.getenv("BAR_OUTLET", "")
