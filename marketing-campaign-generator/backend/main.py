"""
Marketing Campaign Generator API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .core.database import init_db
from .api import campaign_routes, client_routes

# Create FastAPI app
app = FastAPI(
    title="Marketing Campaign Generator API",
    description="AI-powered marketing campaign content generation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(campaign_routes.router, prefix="/api")
app.include_router(client_routes.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

@app.get("/")
async def root():
    return {
        "message": "Marketing Campaign Generator API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 