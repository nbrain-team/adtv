import json
import os
from typing import Dict, Any, Optional

import requests


PODIO_BASE_URL = os.getenv("PODIO_BASE_URL", "https://api.podio.com")
PODIO_OAUTH_BASE_URL = os.getenv("PODIO_OAUTH_BASE_URL", "https://podio.com")
PODIO_CLIENT_ID = os.getenv("PODIO_CLIENT_ID")
PODIO_CLIENT_SECRET = os.getenv("PODIO_CLIENT_SECRET")


def _post_oauth_token_app(app_id: int | str, app_token: str) -> str:
    # OAuth token exchange must use podio.com (not api.podio.com)
    url = f"{PODIO_OAUTH_BASE_URL}/oauth/token"
    data = {
        "grant_type": "app",
        "app_id": str(app_id),
        "app_token": app_token,
    }
    # Podio requires client_id/client_secret for app grant
    if PODIO_CLIENT_ID:
        data["client_id"] = PODIO_CLIENT_ID
    if PODIO_CLIENT_SECRET:
        data["client_secret"] = PODIO_CLIENT_SECRET
    resp = requests.post(url, data=data, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    return body.get("access_token")


def _get_headers(access_token: str) -> Dict[str, str]:
    return {
        "Authorization": f"OAuth2 {access_token}",
        "Accept": "application/json",
    }


def get_app_info(app_id: int | str, app_token: str) -> Dict[str, Any]:
    """Authenticate with app token and fetch basic app info."""
    access_token = _post_oauth_token_app(app_id, app_token)
    url = f"{PODIO_BASE_URL}/app/{app_id}"
    resp = requests.get(url, headers=_get_headers(access_token), timeout=30)
    resp.raise_for_status()
    return resp.json()


def ping_app(app_id: int | str, app_token: str) -> Dict[str, Any]:
    try:
        info = get_app_info(app_id, app_token)
        return {
            "app_id": int(app_id),
            "ok": True,
            "name": info.get("config", {}).get("name") or info.get("name"),
            "url": info.get("url"),
        }
    except Exception as e:
        return {"app_id": int(app_id), "ok": False, "error": str(e)}


def ping_all_from_env() -> Dict[str, Any]:
    """Iterate over PODIO_APP_TOKENS_JSON env and ping each app."""
    raw = os.getenv("PODIO_APP_TOKENS_JSON", "{}")
    try:
        tokens: Dict[str, str] = json.loads(raw)
    except Exception:
        return {"ok": False, "error": "Invalid PODIO_APP_TOKENS_JSON"}

    results = []
    for app_id_str, app_token in tokens.items():
        results.append(ping_app(app_id_str, app_token))

    summary = {
        "total": len(results),
        "successful": sum(1 for r in results if r.get("ok")),
        "failed": [r for r in results if not r.get("ok")],
    }
    return {"ok": all(r.get("ok") for r in results), "results": results, "summary": summary}


def get_access_token_for_app(app_id: int | str, app_token: str) -> str:
    return _post_oauth_token_app(app_id, app_token)


def list_app_items_basic(app_id: int | str, access_token: str, *, limit: int = 200, offset: int = 0) -> Dict[str, Any]:
    """Return items for an app using Podio filter API. Returns raw JSON."""
    url = f"{PODIO_BASE_URL}/item/app/{app_id}/filter/"
    payload = {
        "limit": limit,
        "offset": offset,
        # No filters -> return recent items
        "sort_by": "created_on",
        "sort_desc": True,
    }
    resp = requests.post(url, headers={**_get_headers(access_token), "Content-Type": "application/json"}, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_item(item_id: int | str, access_token: str) -> Dict[str, Any]:
    url = f"{PODIO_BASE_URL}/item/{item_id}"
    resp = requests.get(url, headers=_get_headers(access_token), timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_item_comments(item_id: int | str, access_token: str, *, limit: int = 50) -> Dict[str, Any]:
    url = f"{PODIO_BASE_URL}/comment/item/{item_id}/"
    params = {"limit": limit}
    resp = requests.get(url, headers=_get_headers(access_token), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


