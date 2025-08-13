import os
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import Pinecone as LangchainPinecone
from typing import List, Optional
from datetime import datetime, timezone
import math

# --- Environment Setup ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL_NAME = "models/embedding-001"
EMBEDDING_DIMENSION = 768

def _get_pinecone_index():
    """Initializes and returns a Pinecone index client."""
    if not PINECONE_API_KEY or not PINECONE_INDEX_NAME or not PINECONE_ENV:
        raise ValueError("Pinecone API key, index name, or environment not set in environment.")
    
    pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
    
    # Note: We are now assuming the index exists and is configured correctly.
    # The volatile startup process should not be creating/validating indexes.
    return pc.Index(PINECONE_INDEX_NAME)

def _get_embedding_model():
    """Initializes and returns a Gemini embedding model client."""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not set in environment.")
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL_NAME,
        google_api_key=GEMINI_API_KEY
    )

def upsert_chunks(chunks: List[str], metadata: dict):
    """
    Embeds text chunks using Google Gemini and upserts them into Pinecone.
    Initializes clients on-the-fly for stability.
    """
    embeddings = _get_embedding_model()
    
    docs_with_metadata = []
    for i, chunk in enumerate(chunks):
        doc_metadata = metadata.copy()
        doc_metadata["text"] = chunk
        if "created_at" not in doc_metadata:
            doc_metadata["created_at"] = datetime.now(timezone.utc).isoformat()
        docs_with_metadata.append(doc_metadata)

    LangchainPinecone.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=docs_with_metadata,
        index_name=os.getenv("PINECONE_INDEX_NAME")
    )

def list_documents():
    """
    Lists all unique documents in the Pinecone index.
    Initializes clients on-the-fly for stability.
    """
    try:
        index = _get_pinecone_index()
        results = index.query(
            vector=[0] * EMBEDDING_DIMENSION,
            top_k=1000,
            include_metadata=True
        )
        
        seen_files = set()
        unique_documents = []
        for match in results.get('matches', []):
            file_name = match.get('metadata', {}).get('source')
            if file_name and file_name not in seen_files:
                unique_documents.append({
                    "name": file_name,
                    "type": match.get('metadata', {}).get('doc_type', 'N/A'),
                    "status": "Ready"
                })
                seen_files.add(file_name)
        return unique_documents
    except Exception as e:
        print(f"Error listing documents from Pinecone: {e}")
        return []

def delete_document(file_name: str):
    """
    Deletes all vectors associated with a specific file_name from the index.
    Initializes clients on-the-fly for stability.
    """
    index = _get_pinecone_index()
    index.delete(filter={"source": file_name})

def query_index(
    query: str,
    top_k: int = 10,
    file_names: List[str] = None,
    doc_type: Optional[str] = None,
    prioritize_recent: bool = False,
    recency_half_life_days: int = 180
):
    """
    Queries the index with a question and returns the most relevant text chunks
    and their source documents. Supports optional filtering by doc_type and
    an optional recency boost that favors newer content.
    """
    index = _get_pinecone_index()
    embeddings = _get_embedding_model()
    
    query_embedding = embeddings.embed_query(query)
    
    # Build filter
    filter_metadata = None
    if file_names:
        filter_metadata = {"source": {"$in": file_names}}
    if doc_type:
        if filter_metadata is None:
            filter_metadata = {"doc_type": doc_type}
        else:
            filter_metadata["doc_type"] = doc_type

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter_metadata
    )
    matches = results.get('matches', [])

    if not prioritize_recent or not matches:
        return matches

    # Recency boost: exponential decay by age in days; newer gets higher boost
    now = datetime.now(timezone.utc)
    half_life = max(1, recency_half_life_days)
    lambda_decay = math.log(2) / (half_life)

    def parse_date(meta_value):
        try:
            # Accept ISO strings; fallback to naive datetime parsed as UTC
            if isinstance(meta_value, str):
                return datetime.fromisoformat(meta_value.replace('Z', '+00:00'))
            return meta_value
        except Exception:
            return None

    boosted = []
    for m in matches:
        score = m.get('score', 0.0)
        meta = m.get('metadata', {}) or {}
        dt = parse_date(meta.get('created_at') or meta.get('updated_at'))
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_days = max(0.0, (now - dt).total_seconds() / 86400.0)
            recency = math.exp(-lambda_decay * age_days)
        else:
            recency = 1.0
        boosted.append((score * (0.7 + 0.3 * recency), m))

    boosted.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in boosted] 