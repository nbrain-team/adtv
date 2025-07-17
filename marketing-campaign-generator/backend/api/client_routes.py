"""
Client Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models.database import Client
from . import schemas

router = APIRouter(prefix="/clients", tags=["clients"])

# Mock clients for testing
MOCK_CLIENTS = [
    {
        "id": str(uuid.uuid4()),
        "name": "John Smith",
        "company": "TechStart Solutions",
        "industry": "Technology",
        "website": "https://techstart.com",
        "description": "A cutting-edge software development company specializing in AI and cloud solutions",
        "brand_voice": "Professional, innovative, forward-thinking",
        "target_audience": {"age": "25-45", "interests": ["technology", "innovation", "business"]},
        "keywords": ["AI", "cloud computing", "software development", "digital transformation"],
        "social_accounts": {"linkedin": "@techstart", "twitter": "@techstartsol"}
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Sarah Johnson",
        "company": "Green Earth Organics",
        "industry": "Health & Wellness",
        "website": "https://greenearthorganics.com",
        "description": "Premium organic food and wellness products for health-conscious consumers",
        "brand_voice": "Friendly, authentic, health-focused",
        "target_audience": {"age": "30-55", "interests": ["health", "organic food", "sustainability"]},
        "keywords": ["organic", "sustainable", "wellness", "healthy living"],
        "social_accounts": {"instagram": "@greenearth", "facebook": "GreenEarthOrganics"}
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Michael Chen",
        "company": "FinanceFlow Pro",
        "industry": "Financial Services",
        "website": "https://financeflowpro.com",
        "description": "Modern financial planning and investment management for the digital age",
        "brand_voice": "Trustworthy, expert, accessible",
        "target_audience": {"age": "25-60", "interests": ["investing", "financial planning", "wealth management"]},
        "keywords": ["investment", "financial planning", "wealth", "retirement"],
        "social_accounts": {"linkedin": "@financeflowpro", "twitter": "@financeflow"}
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Emily Rodriguez",
        "company": "FitLife Studios",
        "industry": "Fitness & Recreation",
        "website": "https://fitlifestudios.com",
        "description": "Boutique fitness studios offering personalized training and group classes",
        "brand_voice": "Energetic, motivational, inclusive",
        "target_audience": {"age": "20-45", "interests": ["fitness", "health", "wellness", "community"]},
        "keywords": ["fitness", "personal training", "group classes", "wellness"],
        "social_accounts": {"instagram": "@fitlifestudios", "facebook": "FitLifeStudios"}
    },
    {
        "id": str(uuid.uuid4()),
        "name": "David Thompson",
        "company": "NextGen Real Estate",
        "industry": "Real Estate",
        "website": "https://nextgenrealestate.com",
        "description": "Technology-driven real estate services for modern buyers and sellers",
        "brand_voice": "Professional, knowledgeable, tech-savvy",
        "target_audience": {"age": "25-65", "interests": ["real estate", "home buying", "investment properties"]},
        "keywords": ["real estate", "homes", "property", "investment"],
        "social_accounts": {"linkedin": "@nextgenre", "instagram": "@nextgenrealestate"}
    }
]

@router.get("/", response_model=List[schemas.ClientResponse])
async def list_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all clients - returns mock data for testing"""
    
    # For now, return mock clients
    # In production, query from database:
    # clients = db.query(Client).offset(skip).limit(limit).all()
    
    return MOCK_CLIENTS[skip:skip + limit]

@router.get("/{client_id}", response_model=schemas.ClientResponse)
async def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific client"""
    
    # For mock data
    client = next((c for c in MOCK_CLIENTS if c["id"] == client_id), None)
    if client:
        return client
    
    # In production:
    # client = db.query(Client).filter(Client.id == client_id).first()
    # if not client:
    #     raise HTTPException(status_code=404, detail="Client not found")
    # return client
    
    raise HTTPException(status_code=404, detail="Client not found")

@router.post("/", response_model=schemas.ClientResponse)
async def create_client(
    client_data: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new client"""
    
    # For mock implementation, just return the data with an ID
    new_client = {
        "id": str(uuid.uuid4()),
        **client_data.dict(),
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
    
    # Add to mock clients
    MOCK_CLIENTS.append(new_client)
    
    return new_client

@router.put("/{client_id}", response_model=schemas.ClientResponse)
async def update_client(
    client_id: str,
    client_data: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a client"""
    
    # Find mock client
    client_index = next((i for i, c in enumerate(MOCK_CLIENTS) if c["id"] == client_id), None)
    
    if client_index is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Update only provided fields
    update_data = client_data.dict(exclude_unset=True)
    MOCK_CLIENTS[client_index].update(update_data)
    
    return MOCK_CLIENTS[client_index]

@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a client"""
    
    # Find and remove from mock clients
    client_index = next((i for i, c in enumerate(MOCK_CLIENTS) if c["id"] == client_id), None)
    
    if client_index is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    MOCK_CLIENTS.pop(client_index)
    
    return {"message": "Client deleted successfully"} 