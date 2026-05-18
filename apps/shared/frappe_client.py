"""
Frappe REST client — shared by all three PyQt6/Kivy apps.

Usage:
    from shared.frappe_client import FrappeClient
    api = FrappeClient()
    stats = api.hotel.get_dashboard_stats()
"""
import json
import requests
from shared import config


class APIError(Exception):
    """Raised when Frappe returns an error response."""
    def __init__(self, message, exc=None):
        super().__init__(message)
        self.exc = exc


class _Namespace:
    """Groups endpoint methods by module (hotel / restaurant / bar)."""
    def __init__(self, client, module):
        self._client = client
        self._module = module

    def _call(self, method, **kwargs):
        return self._client.call(f"hospitality.{self._module}.api.{method}", **kwargs)

    def __getattr__(self, name):
        def endpoint(**kwargs):
            return self._call(name, **kwargs)
        return endpoint


class FrappeClient:
    """
    Thin wrapper around the Frappe whitelisted-method REST API.

    Authentication uses API Key + API Secret (recommended over
    username/password for desktop apps).
    """

    def __init__(self, url=None, api_key=None, api_secret=None):
        self.url        = (url        or config.SERVER_URL).rstrip("/")
        self.api_key    = api_key    or config.API_KEY
        self.api_secret = api_secret or config.API_SECRET
        self.session    = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.api_key}:{self.api_secret}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        })

        # Module-scoped namespaces
        self.hotel      = _Namespace(self, "hotel")
        self.restaurant = _Namespace(self, "restaurant")
        self.bar        = _Namespace(self, "bar")

    # ─── Core request helpers ─────────────────────────────────────────────────

    def call(self, method: str, **kwargs) -> dict | list:
        """
        Call any whitelisted Frappe method.
        kwargs are passed as JSON body params.
        """
        url = f"{self.url}/api/method/{method}"
        try:
            resp = self.session.post(url, json=kwargs, timeout=30)
            resp.raise_for_status()
        except requests.ConnectionError:
            raise APIError("Cannot reach the server. Check your network or server URL.")
        except requests.Timeout:
            raise APIError("Request timed out.")
        except requests.HTTPError as exc:
            self._raise_from_response(resp, exc)

        body = resp.json()
        if "message" in body:
            return body["message"]
        return body

    def get_doc(self, doctype: str, name: str) -> dict:
        url = f"{self.url}/api/resource/{doctype}/{requests.utils.quote(name)}"
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json().get("data", {})

    def get_list(self, doctype: str, fields=None, filters=None,
                 order_by="name", limit=50) -> list:
        url = f"{self.url}/api/resource/{doctype}"
        params = {
            "fields": json.dumps(fields or ["name"]),
            "limit":  limit,
            "order_by": order_by,
        }
        if filters:
            params["filters"] = json.dumps(filters)
        resp = self.session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def ping(self) -> bool:
        """Return True if the server is reachable and credentials are valid."""
        try:
            resp = self.session.get(f"{self.url}/api/method/frappe.auth.get_logged_user",
                                    timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _raise_from_response(resp, original_exc):
        try:
            body   = resp.json()
            msg    = body.get("exception") or body.get("message") or str(original_exc)
            exc_kw = body.get("exc", None)
        except Exception:
            msg    = str(original_exc)
            exc_kw = None
        raise APIError(msg, exc=exc_kw) from original_exc


# ─── Convenience singleton ────────────────────────────────────────────────────

_client: FrappeClient | None = None


def get_client() -> FrappeClient:
    global _client
    if _client is None:
        _client = FrappeClient()
    return _client


def reset_client(url=None, api_key=None, api_secret=None):
    global _client
    _client = FrappeClient(url=url, api_key=api_key, api_secret=api_secret)
    return _client
