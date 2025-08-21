import os
import sys
import json
import gzip
from typing import Iterator, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
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


def upsert_jsonl_gz(path: str):
    count = 0
    for idx, rec in enumerate(iter_jsonl_gz(path), start=1):
        text = (rec.get("text") or "").strip()
        meta = sanitize_metadata(rec.get("metadata") or {})
        if not text:
            continue
        # Preserve per-record metadata by upserting one chunk per call
        pinecone_manager.upsert_chunks([text], meta)
        count += 1
        if count % 200 == 0:
            print(f"Upserted {count} chunks...")
    print(f"Upserted {count} chunks to Pinecone from {path}")


def main():
    # Load local .env from repo root
    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(repo_root / ".env")

    if len(sys.argv) < 2:
        print("Usage: PYTHONPATH=. python -u backend/scripts/jsonl_to_pinecone.py <jsonl_gz_path>")
        sys.exit(1)
    path = sys.argv[1]
    upsert_jsonl_gz(path)


if __name__ == "__main__":
    main()


