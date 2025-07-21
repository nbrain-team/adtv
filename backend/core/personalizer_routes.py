from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import base64

from .database import get_db, User
from .personalizer_models import PersonalizerProject
from . import auth

router = APIRouter()

@router.post("/projects")
async def save_project(
    name: str = Form(...),
    template_used: str = Form(...),
    generation_goal: str = Form(""),
    csv_headers: str = Form(...),  # JSON string
    row_count: int = Form(...),
    generated_csv: str = Form(...),  # Base64 encoded CSV content
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save a completed personalizer project"""
    
    # Create project record
    project = PersonalizerProject(
        name=name,
        user_id=current_user.id,
        template_used=template_used,
        generation_goal=generation_goal,
        csv_headers=json.loads(csv_headers),
        row_count=row_count,
        status="completed"
    )
    
    # For now, store the CSV content as base64 in the URL field
    # In production, you'd upload to S3 or similar
    project.generated_csv_url = f"data:text/csv;base64,{generated_csv}"
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return {"id": project.id, "message": "Project saved successfully"}

@router.get("/projects")
async def get_projects(
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all projects for the current user"""
    projects = db.query(PersonalizerProject).filter(
        PersonalizerProject.user_id == current_user.id
    ).order_by(PersonalizerProject.created_at.desc()).all()
    
    return projects

@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific project"""
    project = db.query(PersonalizerProject).filter(
        PersonalizerProject.id == project_id,
        PersonalizerProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    project = db.query(PersonalizerProject).filter(
        PersonalizerProject.id == project_id,
        PersonalizerProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"} 