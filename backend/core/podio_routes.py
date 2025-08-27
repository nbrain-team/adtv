from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from .podio_client import (
    ping_all_from_env,
    get_access_token_for_app,
    list_app_items_basic,
)
from . import auth
import os, json


router = APIRouter(prefix="/api/podio", tags=["podio"])


@router.get("/ping_all", response_model=Dict[str, Any])
async def ping_all(current_user=Depends(auth.get_current_active_user)):
    """Ping all Podio apps defined in PODIO_APP_TOKENS_JSON to verify connectivity."""
    return ping_all_from_env()


@router.get("/clients", response_model=Dict[str, Any])
async def list_clients(
    current_user=Depends(auth.get_current_active_user),
    q: str | None = None,
    app_name: str | None = "Clients",
    app_id: int | None = None,
):
    """Return a flattened list of client items (id, title, app_id, app_name) across configured apps."""
    raw = os.getenv("PODIO_APP_TOKENS_JSON", "{}")
    apps_raw = os.getenv("PODIO_APPS_JSON", "[]")
    try:
        tokens: Dict[str, str] = json.loads(raw)
        apps: List[Dict[str, Any]] = json.loads(apps_raw)
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid Podio env configuration")

    # Map app_id -> name
    app_id_to_name = {int(a.get("app_id")): a.get("name") for a in apps if a.get("app_id")}

    # Determine which apps to query: default to Clients app only
    app_ids_to_query: List[int] = []
    if app_id:
        app_ids_to_query = [int(app_id)]
    else:
        # Filter by provided app_name (default "Clients")
        for a in apps:
            try:
                if app_name and str(a.get("name")).lower() != str(app_name).lower():
                    continue
                if a.get("app_id"):
                    app_ids_to_query.append(int(a.get("app_id")))
            except Exception:
                continue

    items: List[Dict[str, Any]] = []
    for app_id_str, app_token in tokens.items():
        app_id_int = int(app_id_str)
        if app_ids_to_query and app_id_int not in app_ids_to_query:
            continue
        app_display_name = app_id_to_name.get(app_id_int) or str(app_id_int)
        try:
            at = get_access_token_for_app(app_id_int, app_token)
            try:
                listing = list_app_items_basic(app_id_int, at, limit=200, offset=0, query=q)
            except TypeError:
                listing = list_app_items_basic(app_id_int, at, limit=200, offset=0)
            for it in listing.get("items", []):
                item_id = it.get("item_id")
                title = it.get("title") or (it.get("app_item_id_formatted") or str(item_id))
                rec = {
                    "id": item_id,
                    "title": title,
                    "client_id": it.get("app_item_id_formatted") or item_id,
                    "app_id": app_id_int,
                    "app_name": app_display_name,
                }
                if q:
                    qt = str(q).lower()
                    if qt not in str(title).lower() and qt not in str(rec["client_id"]).lower():
                        continue
                items.append(rec)
        except Exception as e:
            # Continue collecting others, but include a note entry indicating failure
            items.append({
                "id": None,
                "title": f"[Error listing {app_display_name}] {e}",
                "app_id": app_id_int,
                "app_name": app_display_name,
                "error": True,
            })

    # Basic dedup by (app_id, title)
    seen = set()
    unique: List[Dict[str, Any]] = []
    for it in items:
        key = (it.get("app_id"), it.get("id") or it.get("title"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(it)

    return {"items": unique}


