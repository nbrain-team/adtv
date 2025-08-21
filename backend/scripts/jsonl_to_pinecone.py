import os
import sys
import json
import gzip
from typing import Iterator, Dict, Any
from pathlib import Path

# Load .env BEFORE importing core modules that read env at import time
from dotenv import load_dotenv
_repo_root = Path(__file__).resolve().parents[2]
load_dotenv(_repo_root / ".env")

from core import pinecone_manager


def iter_jsonl_gz(path: str) -> Iterator[Dict[str, Any]]:
    with gzip.open(path, "rb") as f:
        for line in f:
            line = line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            sanitized[k] = [str(x) for x in v]
        else:
            sanitized[k] = str(v)
    return sanitized


def chunk_text(text: str, max_chars: int = 3000, overlap: int = 200) -> list[str]:
    if not text:
        return []
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        # try to break on whitespace
        if end < n:
            ws = text.rfind(" ", start + int(max_chars * 0.7), end)
            if ws != -1 and ws > start:
                end = ws
        chunks.append(text[start:end].strip())
        if end == n:
            break
        start = max(0, end - overlap)
    # remove empties
    return [c for c in chunks if c]


def upsert_jsonl_gz(path: str):
    count = 0
    for idx, rec in enumerate(iter_jsonl_gz(path), start=1):
        text = (rec.get("text") or "").strip()
        meta = sanitize_metadata(rec.get("metadata") or {})
        if not text:
            continue
        texts = chunk_text(text, max_chars=3000, overlap=200)
        if not texts:
            continue
        pinecone_manager.upsert_chunks(texts, meta)
        count += len(texts)
        if count % 200 == 0:
            print(f"Upserted {count} chunks...")
    print(f"Upserted {count} chunks to Pinecone from {path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: PYTHONPATH=. python -u backend/scripts/jsonl_to_pinecone.py <jsonl_gz_path>")
        sys.exit(1)
    path = sys.argv[1]
    upsert_jsonl_gz(path)


if __name__ == "__main__":
    main()


