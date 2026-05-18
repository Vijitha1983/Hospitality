"""
Frappe REST client — shared by all three PyQt6/Kivy apps.

Usage:
    from shared.frappe_client import FrappeClient, login_with_password
    api = login_with_password("https://erp.example.com", "admin", "secret")
    stats = api.hotel.get_dashboard_stats()
"""
import json
import os
import pathlib
import requests

# ─── Credential persistence ───────────────────────────────────────────────────

_CRED_FILE = pathlib.Path.home() / ".hospitality" / "credentials.json"


def save_credentials(url: str, username: str, password: str, app_name: str = "default"):
    _CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if _CRED_FILE.exists():
        try:
            data = json.loads(_CRED_FILE.read_text())
        except Exception:
            data = {}
    data[app_name] = {"url": url, "username": username, "password": password}
    _CRED_FILE.write_text(json.dumps(data, indent=2))


def load_credentials(app_name: str = "default") -> dict:
    if not _CRED_FILE.exists():
        return {}
    try:
        data = json.loads(_CRED_FILE.read_text())
        return data.get(app_name, {})
    except Exception:
        return {}


def clear_credentials(app_name: str = "default"):
    if not _CRED_FILE.exists():
        return
    try:
        data = json.loads(_CRED_FILE.read_text())
        data.pop(app_name, None)
        _CRED_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


# ─── Errors ───────────────────────────────────────────────────────────────────

class APIError(Exception):
    def __init__(self, message, exc=None):
        super().__init__(message)
        self.exc = exc


# ─── Namespace helper ─────────────────────────────────────────────────────────

class _Namespace:
    def __init__(self, client, module):
        self._client = client
        self._module = module

    def _call(self, method, **kwargs):
        return self._client.call(f"hospitality.{self._module}.api.{method}", **kwargs)

    def __getattr__(self, name):
        def endpoint(**kwargs):
            return self._call(name, **kwargs)
        return endpoint


# ─── Client ───────────────────────────────────────────────────────────────────

class FrappeClient:
    """
    Frappe REST client supporting both session (username/password) and
    token (API key/secret) authentication.
    """

    def __init__(self, url: str, username: str = "", password: str = ""):
        self.url      = url.rstrip("/")
        self.username = username
        self.session  = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept":       "application/json",
        })
        self.hotel      = _Namespace(self, "hotel")
        self.restaurant = _Namespace(self, "restaurant")
        self.bar        = _Namespace(self, "bar")

        if username and password:
            self._do_login(username, password)

    def _do_login(self, username: str, password: str):
        login_url = f"{self.url}/api/method/login"
        try:
            resp = self.session.post(
                login_url,
                data={"usr": username, "pwd": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
        except requests.ConnectionError:
            raise APIError("Cannot reach the server. Check the URL.")
        except requests.Timeout:
            raise APIError("Connection timed out.")

        if resp.status_code == 200:
            body = resp.json()
            if body.get("message") == "Logged In":
                # Session cookie (sid) is now set — remove Content-Type override
                self.session.headers.update({"Content-Type": "application/json"})
                return
            raise APIError(body.get("message") or "Login failed.")
        self._raise_from_response(resp, requests.HTTPError(resp.status_code))

    # ─── Core helpers ──────────────────────────────────────────────────────────

    def call(self, method: str, **kwargs) -> dict | list:
        url = f"{self.url}/api/method/{method}"
        try:
            resp = self.session.post(url, json=kwargs, timeout=30)
            resp.raise_for_status()
        except requests.ConnectionError:
            raise APIError("Lost connection to server.")
        except requests.Timeout:
            raise APIError("Request timed out.")
        except requests.HTTPError as exc:
            self._raise_from_response(resp, exc)
        body = resp.json()
        return body.get("message", body)

    def get_doc(self, doctype: str, name: str) -> dict:
        url = f"{self.url}/api/resource/{doctype}/{requests.utils.quote(str(name))}"
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json().get("data", {})

    def get_list(self, doctype: str, fields=None, filters=None,
                 order_by="name", limit=50) -> list:
        url = f"{self.url}/api/resource/{doctype}"
        params = {
            "fields":   json.dumps(fields or ["name"]),
            "limit":    limit,
            "order_by": order_by,
        }
        if filters:
            params["filters"] = json.dumps(filters)
        resp = self.session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def ping(self) -> bool:
        try:
            resp = self.session.get(
                f"{self.url}/api/method/frappe.auth.get_logged_user", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def get_logged_user(self) -> str:
        try:
            resp = self.session.get(
                f"{self.url}/api/method/frappe.auth.get_logged_user", timeout=5)
            return resp.json().get("message", "")
        except Exception:
            return ""

    @staticmethod
    def _raise_from_response(resp, original_exc):
        try:
            body = resp.json()
            msg  = body.get("exception") or body.get("message") or str(original_exc)
            exc  = body.get("exc")
        except Exception:
            msg, exc = str(original_exc), None
        raise APIError(msg, exc=exc) from original_exc


# ─── Singleton ────────────────────────────────────────────────────────────────

_client: FrappeClient | None = None


def get_client() -> FrappeClient | None:
    return _client


def set_client(client: FrappeClient):
    global _client
    _client = client


def login_with_password(url: str, username: str, password: str) -> FrappeClient:
    global _client
    _client = FrappeClient(url=url, username=username, password=password)
    return _client
