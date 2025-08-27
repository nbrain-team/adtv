from fastapi import FastAPI, HTTPException, Form, BackgroundTasks, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, AsyncGenerator
from pydantic import BaseModel, Field, EmailStr
from dotenv import load_dotenv
import os
import sys
import json
import uuid
import tempfile
import io
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import logging
from sqlalchemy import inspect, text
from datetime import datetime
from fastapi.concurrency import run_in_threadpool

from core import pinecone_manager, llm_handler, processor, auth, generator_handler
from core import mcp as mcp_orchestrator
from core.database import Base, get_db, engine, User, ChatSession, SessionLocal, TemplateAgent
from realtor_importer.api import router as realtor_importer_router
from core.data_lake_routes import router as data_lake_router
from core.data_lake_models import DataLakeRecord
from core.user_routes import router as user_router
from core.email_template_routes import router as email_template_router
from core.personalizer_routes import router as personalizer_router
from db_setup import update_db_schema, migrate_data
from ad_traffic.api import router as ad_traffic_router
from contact_enricher.api import router as contact_enricher_router
from core.campaign_routes import router as campaign_routes
from core.agreements import router as agreements_router
from facebook_automation.api import router as facebook_automation_router
from core.customer_service_routes import router as customer_service_router
from core.podio_routes import router as podio_router


load_dotenv()

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Models ---
class ChatMessage(BaseModel):
    text: str
    sender: str
    sources: Optional[List[str]] = None

class ChatHistory(BaseModel):
    chat_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    messages: List[ChatMessage]

class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationDetail(ConversationSummary):
    messages: List[ChatMessage]
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    query: str
    history: List[dict] = []
    file_names: Optional[List[str]] = None
    doc_type: Optional[str] = None
    prioritize_recent: bool = False
    use_mcp: bool = True
    include_sources: Optional[List[str]] = None  # e.g., ["pinecone", "customer_service", "podio"]
    podio_client_item_id: Optional[int] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UrlList(BaseModel):
    urls: List[str]

class GeneratorRequest(BaseModel):
    mappings: dict
    core_content: str
    tone: str
    style: str

class TemplateAgentCreate(BaseModel):
    name: str
    example_input: str
    example_output: str

class TemplateAgentResponse(BaseModel):
    id: str
    name: str
    example_input: str
    example_output: str
    prompt_template: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- App Initialization ---
app = FastAPI(
    title="ADTV RAG API",
    description="API for ADTV's Retrieval-Augmented Generation platform.",
    version="0.2.2",
)

# --- CORS Configuration (Must be first middleware) ---
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://adtv.nbrain.ai",
    "https://adtv-frontend.onrender.com",
    "*"  # Keep wildcard as fallback
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add custom middleware to ensure CORS headers on errors
@app.middleware("http")
async def catch_exceptions_middleware(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # Log the error
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(f"Request path: {request.url.path}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return a proper error response with CORS headers
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={
                "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                "Access-Control-Allow-Credentials": "true",
            }
        )

@app.on_event("startup")
def on_startup():
    # Rename ad_traffic campaigns table first to avoid conflicts
    try:
        from scripts.rename_ad_traffic_campaigns import rename_ad_traffic_campaigns
        logger.info("Checking for ad_traffic campaigns table rename...")
        rename_ad_traffic_campaigns()
        logger.info("Ad traffic campaigns table check completed.")
    except Exception as e:
        logger.warning(f"Ad traffic campaigns rename check failed: {e}")
    
    # Run ad traffic migration first
    try:
        from scripts.add_unified_ad_traffic_tables import add_unified_ad_traffic_tables
        logger.info("Running ad traffic tables migration...")
        add_unified_ad_traffic_tables()
        logger.info("Ad traffic tables migration completed.")
    except Exception as e:
        logger.warning(f"Ad traffic tables migration failed: {e}")
    
    # Update ad traffic enums
    try:
        from scripts.update_ad_traffic_enums import update_ad_traffic_enums
        logger.info("Updating ad traffic enums...")
        update_ad_traffic_enums()
        logger.info("Ad traffic enums update completed.")
    except Exception as e:
        logger.warning(f"Ad traffic enums update failed: {e}")
    
    # Fix video clips schema
    try:
        from scripts.fix_video_clips_schema import fix_video_clips_schema
        logger.info("Fixing video clips schema...")
        fix_video_clips_schema()
        logger.info("Video clips schema fix completed.")
    except Exception as e:
        logger.warning(f"Video clips schema fix failed: {e}")
    
    # Fix video URLs
    try:
        from scripts.fix_video_urls import fix_video_urls
        logger.info("Fixing video URLs...")
        fix_video_urls()
        logger.info("Video URLs fix completed.")
    except Exception as e:
        logger.warning(f"Video URLs fix failed: {e}")
    
    # Add contact enricher tables
    try:
        from scripts.add_contact_enricher_tables import add_contact_enricher_tables
        logger.info("Adding contact enricher tables...")
        add_contact_enricher_tables()
        logger.info("Contact enricher tables added.")
    except Exception as e:
        logger.warning(f"Contact enricher tables migration failed: {e}")
    
    # Add error_message field to enrichment_projects
    try:
        from scripts.add_enricher_error_field import add_error_field
        logger.info("Adding error_message field to enrichment_projects...")
        add_error_field()
        logger.info("error_message field added.")
    except Exception as e:
        logger.warning(f"Error field migration failed: {e}")
    
    # Create all tables with error handling
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Application startup: Database tables checked/created.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        # Try to create tables individually to isolate the problem
        logger.info("Attempting to create tables individually...")
        for table in Base.metadata.sorted_tables:
            try:
                table.create(bind=engine, checkfirst=True)
                logger.info(f"Created table: {table.name}")
            except Exception as table_error:
                logger.warning(f"Failed to create table {table.name}: {table_error}")
    
    # Run database migrations
    try:
        with SessionLocal() as db:
            logger.info("Running database migrations...")
            update_db_schema(db)
            migrate_data(db)
            db.commit()
            logger.info("Database migrations completed.")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
    
    # Safeguard: If server restarted during enrichment, mark campaigns as paused and reset in-flight contacts
    try:
        with SessionLocal() as db:
            from core.database import Campaign, CampaignContact
            paused_count = db.query(Campaign).filter(Campaign.status == 'enriching').update({Campaign.status: 'paused'}, synchronize_session=False)
            reset_count = db.query(CampaignContact).filter(CampaignContact.enrichment_status == 'processing').update({CampaignContact.enrichment_status: 'pending'}, synchronize_session=False)
            db.commit()
            if paused_count or reset_count:
                logger.info(f"Startup recovery: paused {paused_count} campaigns and reset {reset_count} contacts from 'processing' to 'pending'.")
    except Exception as e:
        logger.warning(f"Startup recovery step failed: {e}")
    
    # Add campaign fields
    try:
        from scripts.add_campaign_fields import add_campaign_fields
        logger.info("Adding campaign fields...")
        add_campaign_fields()
        logger.info("Campaign fields migration completed.")
    except Exception as e:
        logger.warning(f"Campaign fields migration failed: {e}")
    
    # Fix campaign foreign key constraint - skip if it hangs or fails
    logger.info("Attempting to fix campaign foreign key constraint...")
    try:
        from scripts.fix_campaign_foreign_key import fix_campaign_foreign_key
        # Comment out for now - this is causing deployment to hang
        # fix_campaign_foreign_key()
        logger.warning("Campaign foreign key fix skipped to prevent deployment hang")
    except Exception as e:
        logger.warning(f"Could not fix campaign foreign key: {e}, continuing anyway...")
    
    # Fix campaign analytics table
    logger.info("Attempting to fix campaign analytics table...")
    try:
        from scripts.fix_campaign_analytics_table import fix_campaign_analytics_table
        # Comment out for now - might cause deployment to hang
        # fix_campaign_analytics_table()
        logger.warning("Campaign analytics table fix skipped to prevent deployment hang")
    except Exception as e:
        logger.warning(f"Could not fix campaign analytics table: {e}, continuing anyway...")
    
    # Add missing columns to campaign_analytics if table exists
    logger.info("Adding missing columns to campaign_analytics...")
    try:
        from scripts.fix_campaign_analytics_missing_columns import add_missing_columns
        add_missing_columns()
        logger.info("Campaign analytics columns updated.")
    except Exception as e:
        logger.warning(f"Could not add missing columns to campaign_analytics: {e}")
    
    # Add neighborhood field to campaign_contacts
    logger.info("Adding neighborhood field to campaign_contacts...")
    try:
        from scripts.add_neighborhood_to_contacts import add_neighborhood_field
        # Comment out for now - causing deployment to hang
        # add_neighborhood_field()
        logger.warning("Neighborhood field migration skipped to prevent deployment hang")
    except Exception as e:
        logger.warning(f"Could not add neighborhood field: {e}, continuing anyway...")
    
    # Add mail merge fields to campaigns table
    logger.info("Adding mail merge fields to campaigns table...")
    try:
        from scripts.add_campaign_mail_merge_fields import add_campaign_mail_merge_fields
        add_campaign_mail_merge_fields()
        logger.info("Mail merge fields added successfully.")
    except Exception as e:
        logger.warning(f"Could not add mail merge fields: {e}, continuing anyway...")
    
    # Add campaign event fields (city, state, event_slots)
    logger.info("Adding campaign event fields...")
    try:
        from scripts.add_campaign_event_fields import add_campaign_event_fields
        add_campaign_event_fields()
        logger.info("Campaign event fields added successfully.")
    except Exception as e:
        logger.warning(f"Could not add campaign event fields: {e}, continuing anyway...")
    
    # Add agreement fields
    logger.info("Adding agreement fields...")
    try:
        from scripts.add_agreement_fields import add_agreement_fields
        add_agreement_fields()
        logger.info("Agreement fields added successfully.")
    except Exception as e:
        logger.warning(f"Could not add agreement fields: {e}, continuing anyway...")
    
    # Ensure agreements table exists
    logger.info("Ensuring agreements table exists...")
    try:
        from scripts.ensure_agreements_table import ensure_agreements_table
        ensure_agreements_table()
        logger.info("Agreements table check completed.")
    except Exception as e:
        logger.warning(f"Could not ensure agreements table: {e}, continuing anyway...")
    
    # Ensure danny@nbrain.ai has ad-traffic permission
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == "danny@nbrain.ai").first()
            if user:
                permissions = user.permissions.copy() if user.permissions else {}
                # Always set ad-traffic to True, regardless of current value
                permissions['ad-traffic'] = True
                permissions['facebook-automation'] = True  # Add facebook-automation permission
                user.permissions = permissions
                db.commit()
                logger.info(f"Set ad-traffic and facebook-automation permissions to True for danny@nbrain.ai. All permissions: {permissions}")
            else:
                logger.warning("User danny@nbrain.ai not found")
    except Exception as e:
        logger.error(f"Error updating ad-traffic permission: {e}")
    
    # Also update all admin users to have facebook-automation permission
    try:
        with SessionLocal() as db:
            admin_users = db.query(User).filter(User.role == "admin").all()
            for user in admin_users:
                permissions = user.permissions.copy() if user.permissions else {}
                permissions['facebook-automation'] = True
                user.permissions = permissions
                db.commit()
                logger.info(f"Added facebook-automation permission for admin user {user.email}")
    except Exception as e:
        logger.error(f"Error updating facebook-automation permissions: {e}")

    # Import ad_traffic_router after startup
    # from ad_traffic.api import router as ad_traffic_router
    # app.include_router(ad_traffic_router, prefix="/api/ad-traffic", tags=["ad-traffic"])

# --- Routers ---
# Note: Only include routers from modules that actually define them
# The following modules are utilities and don't have routers:
# - pinecone_manager, llm_handler, processor, auth, generator_handler
app.include_router(realtor_importer_router, prefix="/realtor-importer", tags=["realtor"])
app.include_router(data_lake_router, prefix="/api/data-lake", tags=["data-lake"])
app.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(email_template_router, prefix="/api/email-templates", tags=["email-templates"])
app.include_router(ad_traffic_router, prefix="/api/ad-traffic", tags=["ad-traffic"])
app.include_router(personalizer_router, prefix="/api/personalizer", tags=["personalizer"])
app.include_router(contact_enricher_router, prefix="/api/contact-enricher", tags=["contact-enricher"])
app.include_router(campaign_routes, prefix="/api/campaigns", tags=["campaigns"])
app.include_router(agreements_router, prefix="/api/agreements", tags=["agreements"])
app.include_router(facebook_automation_router, prefix="/api/facebook-automation", tags=["facebook-automation"])
app.include_router(customer_service_router, prefix="/api/customer-service", tags=["customer-service"])
app.include_router(podio_router)

# Mount uploads directory for static file serving
import os
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.get("/")
def read_root():
    return {"status": "ADTV RAG API is running"}

@app.get("/debug/my-permissions")
def get_my_permissions(current_user: User = Depends(auth.get_current_active_user)):
    """Debug endpoint to check current user permissions"""
    return {
        "email": current_user.email,
        "role": current_user.role,
        "permissions": current_user.permissions,
        "is_active": current_user.is_active,
        "id": current_user.id
    }

# Serve Email Template Creator help video from project root
@app.get("/api/assets/email-template-creator")
def get_email_template_creator_video():
    try:
        project_root = os.path.dirname(os.path.dirname(__file__))
        file_path = os.path.join(project_root, "Email Template Creator.mp4")
        return FileResponse(file_path, media_type="video/mp4", filename="Email Template Creator.mp4")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Help video not found: {e}")

# --- Background Processing ---
def process_and_index_files(temp_file_paths: List[str], original_file_names: List[str]):
    logger.info(f"BACKGROUND_TASK: Starting processing for {len(original_file_names)} files.")
    for i, temp_path in enumerate(temp_file_paths):
        original_name = original_file_names[i]
        logger.info(f"BACKGROUND_TASK: Processing {original_name}")
        try:
            chunks = processor.process_file(temp_path, original_name)
            if chunks:
                metadata = {"source": original_name, "doc_type": "file_upload"}
                pinecone_manager.upsert_chunks(chunks, metadata)
                logger.info(f"BACKGROUND_TASK: Successfully processed and indexed {original_name}")
            else:
                logger.warning(f"BACKGROUND_TASK: No chunks found for {original_name}. Skipping.")
        except Exception as e:
            logger.error(f"BACKGROUND_TASK_ERROR: Failed to process {original_name}. Reason: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    logger.info("BACKGROUND_TASK: File processing complete.")

def process_and_index_urls(urls: List[str]):
    logger.info(f"BACKGROUND_TASK: Starting crawling for {len(urls)} URLs.")
    for url in urls:
        logger.info(f"BACKGROUND_TASK: Processing {url}")
        try:
            chunks = processor.process_url(url)
            if chunks:
                metadata = {"source": url, "doc_type": "url_crawl"}
                pinecone_manager.upsert_chunks(chunks, metadata)
                logger.info(f"BACKGROUND_TASK: Successfully processed and indexed {url}")
            else:
                logger.warning(f"BACKGROUND_TASK: No content found for {url}. Skipping.")
        except Exception as e:
            logger.error(f"BACKGROUND_TASK_ERROR: Failed to process {url}. Reason: {e}")
    logger.info("BACKGROUND_TASK: URL crawling complete.")

# --- API Endpoints ---
@app.post("/signup", response_model=Token)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = auth.create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log current state before update
    logger.info(f"Login attempt for {user.email} - Current role: {user.role}, Current permissions: {user.permissions}")
    
    # Temporary fix: Ensure danny@nbrain.ai and danny@nbrain.com have admin permissions
    if user.email in ["danny@nbrain.ai", "danny@nbrain.com"]:
        logger.info(f"Setting admin permissions for {user.email}")
        user.role = "admin"
        user.permissions = {
            "chat": True,
            "history": True,
            "knowledge": True,
            "agents": True,
            "data-lake": True,
            "user-management": True,
            "ad-traffic": True,  # Add this permission!
            "template-manager": True,  # Add template manager permission
            "contact-enricher": True,  # Add contact enricher permission
            "campaigns": True,  # Add campaigns permission
            "facebook-automation": True,  # Add facebook automation permission
            "customer-service": True
        }
        db.commit()
        db.refresh(user)
        logger.info(f"Updated {user.email} - Role: {user.role}, Permissions: {user.permissions}")
    
    # Update last login timestamp
    user.last_login = datetime.now()
    db.commit()
    
    # Log final state
    logger.info(f"Login successful for {user.email} - Final role: {user.role}, Final permissions: {user.permissions}")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    temp_file_paths = []
    original_file_names = []
    for file in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_paths.append(temp_file.name)
            original_file_names.append(file.filename)
    background_tasks.add_task(process_and_index_files, temp_file_paths, original_file_names)
    return {"message": f"Successfully uploaded {len(files)} files. Processing has started in the background."}

@app.post("/crawl-urls")
async def crawl_urls(url_list: UrlList, background_tasks: BackgroundTasks = BackgroundTasks()):
    background_tasks.add_task(process_and_index_urls, url_list.urls)
    return {"message": f"Started crawling {len(url_list.urls)} URLs in the background."}

@app.get("/documents")
async def get_documents():
    try:
        return pinecone_manager.list_documents()
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{file_name}")
async def delete_document(file_name: str):
    try:
        pinecone_manager.delete_document(file_name)
        return {"message": f"Successfully deleted {file_name}."}
    except Exception as e:
        logger.error(f"Error deleting document {file_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generator/process")
async def generator_process(
    file: UploadFile = File(...),
    key_fields: str = Form(...),
    core_content: str = Form(...),
    is_preview: str = Form(...), # Comes in as a string 'true' or 'false'
    generation_goal: str = Form(""), # Optional field for extra instructions
    selected_templates: str = Form("[]"),  # JSON string of template IDs
    db: Session = Depends(get_db)
):
    preview_mode = is_preview.lower() == 'true'
    key_fields_list = json.loads(key_fields)
    selected_template_ids = json.loads(selected_templates)
    csv_buffer = io.BytesIO(await file.read())

    # Fetch selected templates if any
    templates = []
    if selected_template_ids:
        from core.database import EmailTemplate
        db_templates = db.query(EmailTemplate).filter(EmailTemplate.id.in_(selected_template_ids)).all()
        templates = [{
            'id': t.id,
            'name': t.name,
            'content': t.body
        } for t in db_templates]

    # Create the generator; it will handle preview logic internally
    content_generator = generator_handler.generate_content_rows(
        csv_file=csv_buffer,
        key_fields=key_fields_list,
        core_content=core_content,
        is_preview=preview_mode,
        generation_goal=generation_goal,
        templates=templates
    )

    # ALWAYS stream the response to avoid timeouts. The frontend will handle
    # closing the connection early for previews.
    async def stream_csv_content():
        try:
            # The first yield is the header
            header = await anext(content_generator)
            yield json.dumps({"type": "header", "data": header}) + "\n"

            # Yield each subsequent row
            async for row in content_generator:
                yield json.dumps({"type": "row", "data": row}) + "\n"
            
            yield json.dumps({"type": "done"}) + "\n"
            logger.info("Successfully streamed all CSV content.")

        except Exception as e:
            logger.error(f"Error during CSV stream: {e}", exc_info=True)
            error_payload = json.dumps({"type": "error", "detail": str(e)})
            yield error_payload + "\n"

    return StreamingResponse(stream_csv_content(), media_type="application/x-ndjson")

# This is a standalone function to be called from the stream
def save_chat_history_sync(
    chat_data: ChatHistory,
    db: Session,
    current_user: User
):
    """Saves a chat conversation to the database (synchronous version)."""
    try:
        first_user_message = next((msg.text for msg in chat_data.messages if msg.sender == 'user'), "New Chat")
        title = (first_user_message[:100] + '...') if len(first_user_message) > 100 else first_user_message
        messages_as_dicts = [msg.dict() for msg in chat_data.messages]

        # Check if a conversation with this ID already exists
        existing_convo = db.query(ChatSession).filter(ChatSession.id == str(chat_data.chat_id)).first()

        if existing_convo:
            # Update existing conversation
            existing_convo.messages = messages_as_dicts
            logger.info(f"Updating conversation {existing_convo.id}")
        else:
            # Create new conversation
            db_convo = ChatSession(
                id=str(chat_data.chat_id),
                title=title,
                messages=messages_as_dicts,
                user_id=current_user.id
            )
            db.add(db_convo)
            logger.info(f"Creating new conversation {db_convo.id}")
        
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save chat history: {e}", exc_info=True)
        db.rollback()


@app.get("/history", response_model=list[ConversationSummary])
async def get_all_chat_histories(db: Session = Depends(get_db), current_user: User = Depends(auth.get_current_active_user)):
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()

@app.get("/history/{conversation_id}", response_model=ConversationDetail)
async def get_chat_history(conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(auth.get_current_active_user)):
    conversation = db.query(ChatSession).filter(
        ChatSession.id == conversation_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    return conversation

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, current_user: User = Depends(auth.get_current_active_user)):
    async def stream_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        source_documents = []
        chat_id = str(uuid.uuid4()) # Generate a single ID for the entire conversation

        try:
            # First, retrieve context via MCP orchestrator (aggregates Pinecone, emails, Podio mirror)
            if req.use_mcp:
                if req.podio_client_item_id:
                    matches = mcp_orchestrator.retrieve_context_for_client(
                        query=req.query,
                        podio_item_id=req.podio_client_item_id,
                        top_k=5,
                        include_sources=req.include_sources,
                    )
                else:
                    matches = mcp_orchestrator.retrieve_context(
                        query=req.query,
                        file_names=req.file_names,
                        doc_type=req.doc_type,
                        prioritize_recent=req.prioritize_recent,
                        top_k=5,
                        include_sources=req.include_sources,
                        user_id=current_user.id,
                    )
            else:
                # Backward-compatible: direct Pinecone query
                matches = pinecone_manager.query_index(
                    req.query,
                    top_k=5,
                    file_names=req.file_names,
                    doc_type=req.doc_type,
                    prioritize_recent=req.prioritize_recent
                )
            source_documents = [{"source": m.get('metadata', {}).get('source')} for m in matches]

            # Now, stream the answer from the LLM with context
            generator = llm_handler.stream_answer(req.query, matches, req.history)
            
            async for chunk in generator:
                # The generator from llm_handler now only yields content strings
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk, 'chatId': chat_id, 'sources': source_documents})}\n\n"

            if full_response:
                history_messages = req.history + [
                    {"text": req.query, "sender": "user"},
                    {"text": full_response, "sender": "ai", "sources": [s['source'] for s in source_documents if s['source']]}
                ]
                
                pydantic_messages = [ChatMessage(**msg) for msg in history_messages]
                # Use the same chat_id generated at the start of the stream
                history_to_save = ChatHistory(chat_id=uuid.UUID(chat_id), messages=pydantic_messages)

                with SessionLocal() as db:
                    await run_in_threadpool(save_chat_history_sync, history_to_save, db, current_user)

        except Exception as e:
            logger.error(f"Error during chat stream: {e}", exc_info=True)
            error_message = json.dumps({"error": "An unexpected error occurred."})
            yield f"data: {error_message}\n\n"
        finally:
            yield "data: [DONE]\n\n"
            logger.info("Chat stream finished.")

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.post("/template-agents", response_model=TemplateAgentResponse)
async def create_template_agent(
    template_data: TemplateAgentCreate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new template agent based on example input/output"""
    
    # Generate the prompt template using AI
    prompt_generation_query = f"""Based on the following example input and output, create a prompt template that will help generate similar outputs for new inputs.

Example Input:
{template_data.example_input}

Example Output:
{template_data.example_output}

Please create a prompt template that:
1. Identifies what questions or fields need to be filled in
2. Understands the tone, style, and structure of the output
3. Can be used to generate similar outputs for new inputs

Format the template so that the user only needs to provide answers to specific questions, similar to:
Question 1?
> 

Question 2?
> 

The prompt should guide the AI to produce outputs matching the example's style and structure."""

    # Get the AI to generate the prompt template
    generator = llm_handler.stream_answer(prompt_generation_query, [], [])
    
    prompt_template = ""
    async for chunk in generator:
        prompt_template += chunk
    
    # Create the template agent
    template_agent = TemplateAgent(
        name=template_data.name,
        example_input=template_data.example_input,
        example_output=template_data.example_output,
        prompt_template=prompt_template,
        created_by=current_user.id
    )
    
    db.add(template_agent)
    db.commit()
    db.refresh(template_agent)
    
    return template_agent


@app.get("/template-agents", response_model=List[TemplateAgentResponse])
async def get_template_agents(
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all active template agents for the current user"""
    templates = db.query(TemplateAgent).filter(
        TemplateAgent.created_by == current_user.id,
        TemplateAgent.is_active == True
    ).order_by(TemplateAgent.created_at.desc()).all()
    
    return templates


@app.get("/template-agents/{template_id}", response_model=TemplateAgentResponse)
async def get_template_agent(
    template_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific template agent"""
    template = db.query(TemplateAgent).filter(
        TemplateAgent.id == template_id,
        TemplateAgent.created_by == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template agent not found")
    
    return template


@app.delete("/template-agents/{template_id}")
async def delete_template_agent(
    template_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a template agent (soft delete)"""
    template = db.query(TemplateAgent).filter(
        TemplateAgent.id == template_id,
        TemplateAgent.created_by == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template agent not found")
    
    template.is_active = False
    db.commit()
    
    return {"message": "Template agent deleted successfully"}

# Start the server when running directly
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)