from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from core import auth
from core.database import get_db, User
from . import schemas
from . import models

router = APIRouter()

@router.get("/clients", response_model=List[schemas.ClientResponse])
async def get_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Get all clients for the current user"""
    clients = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.user_id == current_user.id
    ).order_by(models.AdTrafficClient.created_at.desc()).all()
    
    return clients

@router.post("/clients", response_model=schemas.ClientResponse)
async def create_client(
    client_data: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Create a new client"""
    client = models.AdTrafficClient(
        user_id=current_user.id,
        **client_data.dict()
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return client

@router.get("/clients/{client_id}", response_model=schemas.ClientDetailResponse)
async def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Get a specific client with details"""
    client = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return client

@router.put("/clients/{client_id}", response_model=schemas.ClientResponse)
async def update_client(
    client_id: str,
    client_data: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Update a client"""
    client = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    for field, value in client_data.dict(exclude_unset=True).items():
        setattr(client, field, value)
    
    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)
    
    return client

@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Delete a client"""
    client = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    
    return {"message": "Client deleted successfully"}

@router.post("/clients/{client_id}/connect-facebook")
async def connect_facebook(
    client_id: str,
    facebook_data: schemas.FacebookConnect,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Connect Facebook account to client"""
    client = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # In production, you would validate the access token with Facebook
    # and exchange it for a long-lived token
    client.facebook_page_id = facebook_data.page_id
    client.facebook_page_name = facebook_data.page_name
    client.facebook_access_token = facebook_data.access_token
    
    db.commit()
    
    return {"message": "Facebook connected successfully"}

@router.post("/clients/{client_id}/connect-instagram")
async def connect_instagram(
    client_id: str,
    instagram_data: schemas.InstagramConnect,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Connect Instagram account to client"""
    client = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Instagram Business accounts are connected through Facebook
    client.instagram_account_id = instagram_data.account_id
    client.instagram_username = instagram_data.username
    
    db.commit()
    
    return {"message": "Instagram connected successfully"} 