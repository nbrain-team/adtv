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
async def list_clients(current_user=Depends(auth.get_current_active_user)):
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

    items: List[Dict[str, Any]] = []
    for app_id_str, app_token in tokens.items():
        app_id = int(app_id_str)
        app_name = app_id_to_name.get(app_id) or str(app_id)
        try:
            at = get_access_token_for_app(app_id, app_token)
            listing = list_app_items_basic(app_id, at, limit=200, offset=0)
            for it in listing.get("items", []):
                item_id = it.get("item_id")
                title = it.get("title") or (it.get("app_item_id_formatted") or str(item_id))
                items.append({
                    "id": item_id,
                    "title": title,
                    "app_id": app_id,
                    "app_name": app_name,
                })
        except Exception as e:
            # Continue collecting others, but include a note entry indicating failure
            items.append({
                "id": None,
                "title": f"[Error listing {app_name}] {e}",
                "app_id": app_id,
                "app_name": app_name,
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


