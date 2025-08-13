from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import get_db, CustomerServiceCommunication
from . import pinecone_manager

router = APIRouter(tags=["customer-service"])

@router.get("/records", response_model=Dict[str, Any])
def list_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    channel: Optional[str] = None,
    tags: Optional[str] = None,  # comma-separated
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(CustomerServiceCommunication)

    if search:
        like = f"%{search}%"
        q = q.filter(
            (CustomerServiceCommunication.title.ilike(like)) |
            (CustomerServiceCommunication.content.ilike(like)) |
            (CustomerServiceCommunication.category.ilike(like)) |
            (CustomerServiceCommunication.status.ilike(like)) |
            (CustomerServiceCommunication.channel.ilike(like))
        )

    if category:
        q = q.filter(CustomerServiceCommunication.category == category)
    if status:
        q = q.filter(CustomerServiceCommunication.status == status)
    if channel:
        q = q.filter(CustomerServiceCommunication.channel == channel)
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        if tag_list:
            q = q.filter(CustomerServiceCommunication.tags.contains(tag_list))
    if start_date:
        try:
            dt = datetime.fromisoformat(start_date)
            q = q.filter(CustomerServiceCommunication.created_at >= dt)
        except Exception:
            pass
    if end_date:
        try:
            dt = datetime.fromisoformat(end_date)
            q = q.filter(CustomerServiceCommunication.created_at <= dt)
        except Exception:
            pass

    total = q.count()
    items = q.order_by(CustomerServiceCommunication.created_at.desc()).offset(skip).limit(limit).all()

    records = []
    for r in items:
        records.append({
            "id": r.id,
            "title": r.title,
            "category": r.category,
            "status": r.status,
            "channel": r.channel,
            "tags": r.tags,
            "podio_item_id": r.podio_item_id,
            "source_file": r.source_file,
            "author": r.author,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })

    return {"records": records, "total": total, "skip": skip, "limit": limit}

@router.get("/records/{record_id}", response_model=Dict[str, Any])
def get_record(record_id: str, db: Session = Depends(get_db)):
    r = db.query(CustomerServiceCommunication).get(record_id)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": r.id,
        "title": r.title,
        "content": r.content,
        "category": r.category,
        "status": r.status,
        "channel": r.channel,
        "tags": r.tags,
        "podio_item_id": r.podio_item_id,
        "source_file": r.source_file,
        "author": r.author,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }

@router.post("/records", response_model=Dict[str, Any])
def create_record(payload: Dict[str, Any], db: Session = Depends(get_db)):
    r = CustomerServiceCommunication(
        title=payload.get("title"),
        content=payload.get("content", ""),
        category=payload.get("category"),
        status=payload.get("status"),
        channel=payload.get("channel"),
        tags=payload.get("tags") or [],
        podio_item_id=payload.get("podio_item_id"),
        source_file=payload.get("source_file"),
        author=payload.get("author"),
    )
    db.add(r)
    db.commit()
    db.refresh(r)

    # Upsert to Pinecone
    chunks = [r.content]
    metadata = {
        "source": r.source_file or (r.title or r.id),
        "doc_type": "customer_service",
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "category": r.category,
        "status": r.status,
        "tags": r.tags or [],
    }
    try:
        pinecone_manager.upsert_chunks(chunks, metadata)
    except Exception:
        pass

    return {"id": r.id}

@router.put("/records/{record_id}", response_model=Dict[str, Any])
def update_record(record_id: str, payload: Dict[str, Any], db: Session = Depends(get_db)):
    r = db.query(CustomerServiceCommunication).get(record_id)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    for key in ["title", "content", "category", "status", "channel", "tags", "podio_item_id", "source_file", "author"]:
        if key in payload:
            setattr(r, key, payload[key])
    r.updated_at = datetime.utcnow()
    db.commit()
    return {"id": r.id}

@router.delete("/records/{record_id}")
def delete_record(record_id: str, db: Session = Depends(get_db)):
    r = db.query(CustomerServiceCommunication).get(record_id)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(r)
    db.commit()
    return {"message": "deleted"}

@router.get("/search")
def search(query: str, top_k: int = 10, prioritize_recent: bool = True):
    matches = pinecone_manager.query_index(
        query,
        top_k=top_k,
        doc_type="customer_service",
        prioritize_recent=prioritize_recent
    )
    results = []
    for m in matches:
        meta = m.get("metadata", {}) or {}
        results.append({
            "score": m.get("score"),
            "text": meta.get("text"),
            "source": meta.get("source"),
            "created_at": meta.get("created_at"),
            "category": meta.get("category"),
            "status": meta.get("status"),
            "tags": meta.get("tags"),
        })
    return {"results": results} 