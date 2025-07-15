from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr
from datetime import datetime

from . import auth
from .database import get_db, User

router = APIRouter()

# Pydantic models
class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    website_url: Optional[str] = None
    email: Optional[EmailStr] = None  # Added for admin updates

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    website_url: Optional[str]
    role: str
    permissions: Dict[str, bool]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool

class UserPermissionsUpdate(BaseModel):
    permissions: Dict[str, bool]
    role: Optional[str] = None

# Routes
@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(auth.get_current_active_user)
):
    """Get current user's profile"""
    return current_user

@router.put("/profile")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    # Update fields if provided
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name
    if profile_data.company is not None:
        current_user.company = profile_data.company
    if profile_data.website_url is not None:
        current_user.website_url = profile_data.website_url
    
    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully"}

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific user details (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.put("/users/{user_id}/permissions")
async def update_user_permissions(
    user_id: str,
    permissions_data: UserPermissionsUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user permissions and role (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update permissions
    user.permissions = permissions_data.permissions
    
    # Update role if provided
    if permissions_data.role:
        user.role = permissions_data.role
        
        # If user is becoming admin, ensure they have campaigns permission
        if permissions_data.role == "admin" and user.permissions:
            user.permissions["campaigns"] = True
    
    db.commit()
    return {"message": "User permissions updated successfully"}

@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Toggle user active status (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deactivating yourself
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    user.is_active = not user.is_active
    db.commit()
    
    return {"message": f"User {'activated' if user.is_active else 'deactivated'} successfully"}

@router.put("/users/{user_id}/profile")
async def update_user_profile_admin(
    user_id: str,
    profile_data: UserProfileUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update another user's profile (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields if provided
    if profile_data.first_name is not None:
        user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        user.last_name = profile_data.last_name
    if profile_data.company is not None:
        user.company = profile_data.company
    if profile_data.website_url is not None:
        user.website_url = profile_data.website_url
    
    # Special handling for email updates
    if hasattr(profile_data, 'email') and profile_data.email:
        # Check if email is already taken by another user
        existing_user = db.query(User).filter(User.email == profile_data.email, User.id != user_id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = profile_data.email
    
    db.commit()
    db.refresh(user)
    
    return {"message": "User profile updated successfully"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Prevent deleting yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete the user and all related data (cascade delete should handle related records)
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"} 