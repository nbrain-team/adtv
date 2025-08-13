import os
import sys
import json
import csv
from typing import List, Dict
from datetime import datetime, timezone
from pathlib import Path

import boto3
from dotenv import load_dotenv

from core.database import SessionLocal, CustomerServiceCommunication, Base, engine
from core import pinecone_manager, processor
from facebook_automation.models import FacebookClient  # Ensure model registration for relationships

VECTORIZE = os.getenv("VECTORIZE", "0").lower() in {"1", "true", "yes", "y"}
SUPPORTED_TEXT_EXTS = {".txt", ".pdf", ".docx"}
SUPPORTED_META_EXTS = {".json", ".csv"}
DOWNLOAD_DIR = Path(__file__).parent.parent / "uploads" / "customer_service"
DEFAULT_STATE_FILE = DOWNLOAD_DIR / ".processed_stems.txt"


def ensure_dirs():
	DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
	DEFAULT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


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
			with file_path.open("r", encoding="utf-8", errors="ignore") as f:
				reader = csv.DictReader(f)
				for row in reader:
					return row
			return {}
	except Exception:
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


def build_stem_map(keys: List[str]) -> Dict[str, Dict[str, str]]:
	"""Return mapping: stem -> {ext: s3_key}"""
	stem_map: Dict[str, Dict[str, str]] = {}
	for key in keys:
		filename = key.split("/")[-1]
		stem = Path(filename).stem
		ext = Path(filename).suffix.lower()
		if stem not in stem_map:
			stem_map[stem] = {}
		stem_map[stem][ext] = key
	return stem_map


def load_processed_stems(state_file: Path) -> set:
	processed = set()
	if state_file.exists():
		for line in state_file.read_text(encoding="utf-8", errors="ignore").splitlines():
			name = line.strip()
			if name:
				processed.add(name)
	return processed


def append_processed_stem(state_file: Path, stem: str) -> None:
	with state_file.open("a", encoding="utf-8") as f:
		f.write(stem + "\n")
		f.flush()
		os.fsync(f.fileno())


def process_stem(bucket: str, stem: str, files: Dict[str, str]) -> bool:
	"""Process a single stem: download related files, import and upsert.
	Returns True if imported, False if skipped/no content.
	"""
	# Download files for this stem
	downloaded: Dict[str, Path] = {}
	for ext, s3_key in files.items():
		local_path = DOWNLOAD_DIR / f"{stem}{ext}"
		download_object(bucket, s3_key, local_path)
		downloaded[ext] = local_path

	# Prefer text file; else flatten JSON
	text_file = None
	for ext in SUPPORTED_TEXT_EXTS:
		if ext in downloaded:
			text_file = downloaded[ext]
			break

	# Merge side metadata
	meta = {}
	for ext in SUPPORTED_META_EXTS:
		if ext in downloaded:
			meta.update(parse_metadata(downloaded[ext]))

	content = ""
	source_name = None
	if text_file:
		content = read_text_from_file(text_file, text_file.name)
		source_name = text_file.name
	else:
		json_side = downloaded.get(".json")
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
		return False

	# Map fields
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

	# Insert DB record
	db = SessionLocal()
	try:
		record = CustomerServiceCommunication(
			title=title,
			content=content,
			category=category,
			status=status,
			channel=channel,
			tags=tags,
			podio_item_id=podio_item_id,
			source_file=source_name or stem,
			author=author,
			created_at=created_at or datetime.now(timezone.utc)
		)
		db.add(record)
		db.commit()
		db.refresh(record)
	finally:
		db.close()

	# Upsert to Pinecone
	chunks = [content]
	metadata = {
		"source": record.source_file,
		"doc_type": "customer_service",
		"created_at": record.created_at.astimezone(timezone.utc).isoformat() if record.created_at else None,
		"category": category,
		"status": status,
		"tags": tags,
	}
	if VECTORIZE:
		meta_sanitized = dict(metadata)
		if meta_sanitized.get("category") is None:
			meta_sanitized["category"] = ""
		if meta_sanitized.get("status") is None:
			meta_sanitized["status"] = ""
		if meta_sanitized.get("tags") is None:
			meta_sanitized["tags"] = []
		meta_sanitized["tags"] = [str(t) for t in meta_sanitized.get("tags", [])]
		pinecone_manager.upsert_chunks(chunks, meta_sanitized)
	return True


def main():
	load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / "adtv-backend.env")
	ensure_dirs()
	Base.metadata.create_all(bind=engine)

	bucket = os.getenv("PODIO_S3_BUCKET", "podio-export")
	prefix = os.getenv("PODIO_S3_PREFIX", "output/")
	chunk_size = int(os.getenv("CHUNK_SIZE", "10") or 10)
	auto_yes = os.getenv("AUTO_CONTINUE", "").lower() in {"1", "true", "yes", "y"} or ("--yes" in sys.argv or "-y" in sys.argv)
	state_file_env = os.getenv("PROCESS_STATE_FILE", "")
	state_file = Path(state_file_env) if state_file_env else DEFAULT_STATE_FILE

	print(f"Listing S3 objects from s3://{bucket}/{prefix} ...", flush=True)
	keys = list_objects(bucket, prefix)
	stem_map = build_stem_map(keys)
	stems_sorted = sorted(stem_map.keys())
	print(f"Found {len(stems_sorted)} stems total", flush=True)

	processed = load_processed_stems(state_file)
	remaining_stems = [s for s in stems_sorted if s not in processed]
	if not remaining_stems:
		print("All stems have already been processed. Nothing to do.")
		return
	print(f"Remaining stems to process: {len(remaining_stems)}", flush=True)

	processed_total = 0
	for offset in range(0, len(remaining_stems), chunk_size):
		chunk = remaining_stems[offset: offset + chunk_size]
		print(f"\n=== Processing chunk {offset // chunk_size + 1} — stems {offset}..{offset + len(chunk) - 1} (size {len(chunk)}) ===", flush=True)

		imported_in_chunk = 0
		for i, stem in enumerate(chunk, 1):
			files = stem_map.get(stem, {})
			ok = process_stem(bucket, stem, files)
			if ok:
				append_processed_stem(state_file, stem)
				processed_total += 1
				imported_in_chunk += 1
			if i % 10 == 0 or i == len(chunk):
				print(f"  - Imported {i}/{len(chunk)} stems in this chunk...", flush=True)

		print(f"Chunk imported: {imported_in_chunk}, cumulative imported this run: {processed_total}", flush=True)

		if offset + chunk_size >= len(remaining_stems):
			break
		if auto_yes:
			continue
		try:
			answer = input("Continue with next chunk? [y/N]: ").strip().lower()
		except EOFError:
			answer = ""
		if answer not in {"y", "yes"}:
			print("Stopping on user request.", flush=True)
			break

	print(f"\nDone. Total imported this run: {processed_total}. You can rerun later to resume.")


if __name__ == "__main__":
	main() 