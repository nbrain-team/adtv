from fastapi import FastAPI, HTTPException, Form, BackgroundTasks, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
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
from core.database import Base, get_db, engine, User, ChatSession, SessionLocal
from realtor_importer.api import router as realtor_importer_router
from core.data_lake_routes import router as data_lake_router
from core.data_lake_models import DataLakeRecord


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

# --- App Initialization ---
app = FastAPI(
    title="ADTV RAG API",
    description="API for ADTV's Retrieval-Augmented Generation platform.",
    version="0.2.2",
)

@app.on_event("startup")
def on_startup():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Application startup: Database tables checked/created.")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(
    realtor_importer_router,
    prefix="/realtor-importer",
    tags=["Realtor Importer"],
    dependencies=[Depends(auth.get_current_active_user)]
)

app.include_router(
    data_lake_router,
    prefix="/data-lake",
    tags=["Data Lake"],
    dependencies=[Depends(auth.get_current_active_user)]
)

@app.get("/")
def read_root():
    return {"status": "ADTV RAG API is running"}

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
    generation_goal: str = Form("") # Optional field for extra instructions
):
    preview_mode = is_preview.lower() == 'true'
    key_fields_list = json.loads(key_fields)
    csv_buffer = io.BytesIO(await file.read())

    # Create the generator; it will handle preview logic internally
    content_generator = generator_handler.generate_content_rows(
        csv_file=csv_buffer,
        key_fields=key_fields_list,
        core_content=core_content,
        is_preview=preview_mode,
        generation_goal=generation_goal
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
            # First, query the index to get relevant documents
            matches = pinecone_manager.query_index(req.query, top_k=5)
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