import os
import io
import json
import csv
from typing import List, Tuple
from datetime import datetime, timezone
from pathlib import Path

import boto3
from dotenv import load_dotenv

from core.database import SessionLocal, CustomerServiceCommunication, Base, engine
from core import pinecone_manager, processor

SUPPORTED_TEXT_EXTS = {".txt", ".pdf", ".docx"}
SUPPORTED_META_EXTS = {".json", ".csv"}

DOWNLOAD_DIR = Path(__file__).parent.parent / "uploads" / "customer_service"


def ensure_dirs():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_s3_client():
    session = boto3.session.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-2"),
    )
    return session.client("s3")


def list_objects(bucket: str, prefix: str) -> List[str]:
    s3 = get_s3_client()
    keys: List[str] = []
    continuation_token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
        resp = s3.list_objects_v2(**kwargs)
        for item in resp.get("Contents", []):
            key = item["Key"]
            if key.endswith("/"):
                continue
            keys.append(key)
        if resp.get("IsTruncated"):
            continuation_token = resp.get("NextContinuationToken")
        else:
            break
    return keys


def download_object(bucket: str, key: str, dest_path: Path) -> None:
    s3 = get_s3_client()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(bucket, key, str(dest_path))


def read_text_from_file(file_path: Path, original_name: str) -> str:
    ext = file_path.suffix.lower()
    if ext in {".txt"}:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    if ext in {".pdf", ".docx"}:
        chunks = processor.process_file(str(file_path), original_name)
        return "\n".join(chunks)
    return ""


def parse_metadata(file_path: Path) -> dict:
    try:
        if file_path.suffix.lower() == ".json":
            return json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
        if file_path.suffix.lower() == ".csv":
            # very light CSV flatten: return first row
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    return row
            return {}
    except Exception:
        return {}
    return {}


def flatten_json_to_text(data: dict, prefix: str = "") -> List[str]:
    lines: List[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                lines.extend(flatten_json_to_text(v, key))
            else:
                try:
                    v_str = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                except Exception:
                    v_str = str(v)
                lines.append(f"{key}: {v_str}")
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            key = f"{prefix}[{idx}]"
            if isinstance(item, (dict, list)):
                lines.extend(flatten_json_to_text(item, key))
            else:
                lines.append(f"{key}: {item}")
    return lines


def main():
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / "adtv-backend.env")
    ensure_dirs()

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    bucket = os.getenv("PODIO_S3_BUCKET", "podio-export")
    prefix = os.getenv("PODIO_S3_PREFIX", "output/")
    max_items = int(os.getenv("MAX_ITEMS", "0") or 0)

    print(f"Listing S3 objects from s3://{bucket}/{prefix} ...")
    keys = list_objects(bucket, prefix)
    print(f"Found {len(keys)} objects")

    # Group by basename without extension to attach metadata if exists
    by_stem: dict[str, dict[str, Path]] = {}
    count = 0
    for key in keys:
        filename = key.split("/")[-1]
        stem = Path(filename).stem
        ext = Path(filename).suffix.lower()
        local_path = DOWNLOAD_DIR / filename
        download_object(bucket, key, local_path)
        if stem not in by_stem:
            by_stem[stem] = {}
        by_stem[stem][ext] = local_path
        count += 1
        if max_items and count >= max_items:
            break

    db = SessionLocal()
    imported = 0
    for stem, files in by_stem.items():
        # Primary text file
        text_file = None
        for ext in SUPPORTED_TEXT_EXTS:
            if ext in files:
                text_file = files[ext]
                break

        # Optional side metadata
        meta = {}
        for ext in SUPPORTED_META_EXTS:
            if ext in files:
                meta.update(parse_metadata(files[ext]))

        content = ""
        source_name = None
        if text_file:
            content = read_text_from_file(text_file, text_file.name)
            source_name = text_file.name
        else:
            # Build content from JSON if available
            json_side = files.get(".json")
            if json_side and json_side.exists():
                try:
                    data = json.loads(json_side.read_text(encoding="utf-8", errors="ignore"))
                    flat_lines = flatten_json_to_text(data)
                    content = "\n".join(flat_lines)
                    source_name = json_side.name
                except Exception:
                    content = ""
                    source_name = json_side.name

        if not content.strip():
            continue

        # Map simple fields
        title = (meta.get("title") or meta.get("app") or stem)
        category = meta.get("category")
        status = meta.get("status") or meta.get("state")
        channel = meta.get("channel") or "Podio"
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        author = meta.get("author") or meta.get("created_by")
        podio_item_id = str(meta.get("item_id") or meta.get("podio_id") or "") or None

        created_at = None
        for k in ["created_at", "createdOn", "date", "created_at_iso", "created_on"]:
            if k in meta:
                try:
                    created_at = datetime.fromisoformat(str(meta[k]).replace('Z', '+00:00'))
                except Exception:
                    created_at = None
                break

        record = CustomerServiceCommunication(
            title=title,
            content=content,
            category=category,
            status=status,
            channel=channel,
            tags=tags,
            podio_item_id=podio_item_id,
            source_file=source_name or (text_file.name if text_file else stem),
            author=author,
            created_at=created_at or datetime.now(timezone.utc)
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        chunks = [content]
        metadata = {
            "source": record.source_file,
            "doc_type": "customer_service",
            "created_at": (record.created_at.astimezone(timezone.utc).isoformat() if record.created_at else None),
            "category": category,
            "status": status,
            "tags": tags,
        }
        pinecone_manager.upsert_chunks(chunks, metadata)
        imported += 1
        if imported % 25 == 0:
            print(f"Upserted {imported} records ...")

    db.close()
    print(f"Done. Imported {imported} items.")


if __name__ == "__main__":
    main() 