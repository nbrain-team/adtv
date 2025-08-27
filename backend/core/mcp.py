import os
import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from . import pinecone_manager
from .database import SessionLocal, CustomerServiceCommunication
from . import podio_client


def _as_match(text: str, source: str, extra_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a match-like dict compatible with llm_handler expectations."""
    metadata = {"text": text, "source": source}
    if extra_meta:
        metadata.update(extra_meta)
    # We only require metadata; llm_handler uses metadata.text and metadata.source
    return {"metadata": metadata}


def _query_pinecone_general(
    query: str,
    top_k: int,
    file_names: Optional[List[str]],
    doc_type: Optional[str],
    prioritize_recent: bool,
) -> List[Dict[str, Any]]:
    return pinecone_manager.query_index(
        query,
        top_k=top_k,
        file_names=file_names,
        doc_type=doc_type,
        prioritize_recent=prioritize_recent,
    ) or []


def _query_customer_service_pinecone(
    query: str,
    top_k: int,
    prioritize_recent: bool,
) -> List[Dict[str, Any]]:
    return pinecone_manager.query_index(
        query,
        top_k=top_k,
        doc_type="customer_service",
        prioritize_recent=prioritize_recent,
    ) or []


def _query_podio_from_db(query: str, limit: int = 10, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lightweight Podio connector using locally imported Podio communications.
    Pulls from CustomerServiceCommunication where channel == 'Podio' or podio_item_id is set
    and does a simple ILIKE match on content/title. Returns recent-first matches.
    """
    results: List[Dict[str, Any]] = []
    with SessionLocal() as db:  # type: Session
        like = f"%{query}%"
        q = db.query(CustomerServiceCommunication)
        # Scope to Podio-originated content
        q = q.filter(
            (
                (CustomerServiceCommunication.channel == "Podio")
                | (CustomerServiceCommunication.podio_item_id.isnot(None))
            )
        )
        # Optional multi-tenant scoping when available
        if user_id:
            q = q.filter(CustomerServiceCommunication.user_id == user_id)
        # Fuzzy search
        q = q.filter(
            (
                CustomerServiceCommunication.content.ilike(like)
            )
            | (
                CustomerServiceCommunication.title.ilike(like)
            )
        )
        q = q.order_by(CustomerServiceCommunication.created_at.desc()).limit(limit)
        for r in q.all():
            src = f"Podio:{(r.author or '').strip()}:{r.id}"
            extra = {
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "category": r.category,
                "status": r.status,
                "tags": r.tags or [],
            }
            results.append(_as_match(r.content or "", src, extra))
    return results


def retrieve_context(
    query: str,
    *,
    file_names: Optional[List[str]] = None,
    doc_type: Optional[str] = None,
    prioritize_recent: bool = False,
    top_k: int = 5,
    include_sources: Optional[List[str]] = None,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    MCP-style orchestrator that aggregates context from multiple connectors.

    Returns a list of match-like dicts with { metadata: { text, source, ... } }.
    """
    connectors = include_sources or ["pinecone", "customer_service", "podio"]

    matches: List[Dict[str, Any]] = []

    # Pinecone (general or filtered)
    if "pinecone" in connectors:
        matches.extend(
            _query_pinecone_general(
                query=query,
                top_k=top_k,
                file_names=file_names,
                doc_type=doc_type,
                prioritize_recent=prioritize_recent,
            )
        )

    # Pinecone for customer service emails/imports (including Podio-imported messages)
    if "customer_service" in connectors:
        matches.extend(
            _query_customer_service_pinecone(
                query=query, top_k=top_k, prioritize_recent=prioritize_recent
            )
        )

    # Direct Podio via local DB mirror
    if "podio" in connectors:
        try:
            matches.extend(_query_podio_from_db(query=query, limit=top_k, user_id=user_id))
        except Exception:
            # Fail-closed: if DB connector fails, continue with other sources
            pass

    return matches


def retrieve_context_for_client(
    query: str,
    *,
    podio_item_id: Optional[int] = None,
    podio_app_id: Optional[int] = None,
    top_k: int = 5,
    include_sources: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve context with a hard bias toward a specific Podio item (client) by pulling
    its item fields and recent comments, then append general matches as needed.
    """
    matches: List[Dict[str, Any]] = []

    # Pull Podio item details/comments if provided and env is configured
    if podio_item_id:
        try:
            raw_tokens = os.getenv("PODIO_APP_TOKENS_JSON", "{}")
            tokens = json.loads(raw_tokens)
            # Prefer the provided app_id to obtain the correct app-scoped token
            access_token = None
            if podio_app_id and str(podio_app_id) in tokens:
                access_token = podio_client.get_access_token_for_app(int(podio_app_id), tokens[str(podio_app_id)])
            else:
                # Fallback: iterate over all app tokens to find one that can fetch the item
                for app_id_str, app_token in tokens.items():
                    try:
                        access_token = podio_client.get_access_token_for_app(int(app_id_str), app_token)
                        if access_token:
                            break
                    except Exception:
                        continue
            if access_token:
                item = podio_client.get_item(podio_item_id, access_token)
                fields_text = json.dumps(item.get("fields", []))
                title = item.get("title") or f"Podio Item {podio_item_id}"
                matches.append(_as_match(fields_text, f"PodioItem:{title}"))
                comments = podio_client.get_item_comments(podio_item_id, access_token)
                for c in comments.get("comments", [])[:top_k]:
                    text = (c.get("value", {}) or {}).get("value") or c.get("rich_value") or c.get("plain_value") or ""
                    if text:
                        matches.append(_as_match(text, f"PodioComment:{title}"))
        except Exception:
            pass

    # Fallback/additional general retrieval
    matches.extend(retrieve_context(query, include_sources=include_sources, top_k=top_k))
    return matches


