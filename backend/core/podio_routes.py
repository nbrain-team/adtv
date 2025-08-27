from fastapi import APIRouter, Depends
from typing import Dict, Any

from .podio_client import ping_all_from_env
from . import auth


router = APIRouter(prefix="/api/podio", tags=["podio"])


@router.get("/ping_all", response_model=Dict[str, Any])
async def ping_all(current_user=Depends(auth.get_current_active_user)):
    """Ping all Podio apps defined in PODIO_APP_TOKENS_JSON to verify connectivity."""
    return ping_all_from_env()


