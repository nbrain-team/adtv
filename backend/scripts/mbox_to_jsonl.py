import os
import sys
import json
import gzip
import hashlib
import mailbox
from pathlib import Path
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime


STATE_FILE_DEFAULT = ".mbox_ingest_state.json"


def ensure_tzaware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_text(s: str) -> str:
    return " ".join((s or "").replace("\r", "\n").split())


def pick_body(msg) -> str:
    # Prefer text/plain; fallback to text/html stripped
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type() or ""
            if ctype.lower() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
                except Exception:
                    continue
        # Fallback any text/*
        for part in msg.walk():
            ctype = part.get_content_type() or ""
            if ctype.lower().startswith("text/"):
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
                except Exception:
                    continue
        return ""
    else:
        try:
            return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            return msg.get_payload() if isinstance(msg.get_payload(), str) else ""


def hash_id(*parts: str) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update((p or "").encode("utf-8"))
        h.update(b"\x1e")
    return h.hexdigest()


def load_state(state_path: Path) -> dict:
    if state_path.exists():
        try:
            return json.loads(state_path.read_text())
        except Exception:
            return {}
    return {}


def save_state(state_path: Path, state: dict) -> None:
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(state_path)


def parse_mbox(
    mbox_path: Path,
    out_jsonl_gz: Path,
    state_path: Path,
    months_back: int = 6,
    max_records: int | None = None,
):
    cutoff = ensure_tzaware(datetime.now(timezone.utc) - timedelta(days=30 * months_back))

    state = load_state(state_path)
    seen_checksums: set[str] = set(state.get("seen_checksums", []))
    processed_count = int(state.get("processed_count", 0))
    written_count = int(state.get("written_count", 0))

    mbox = mailbox.mbox(str(mbox_path))

    out_jsonl_gz.parent.mkdir(parents=True, exist_ok=True)
    mode = "ab" if out_jsonl_gz.exists() else "wb"
    with gzip.open(str(out_jsonl_gz), mode) as gz:
        for idx, msg in enumerate(mbox):
            processed_count += 1

            # Date filter
            raw_date = msg.get("Date")
            msg_dt = None
            if raw_date:
                try:
                    msg_dt = parsedate_to_datetime(raw_date)
                    msg_dt = ensure_tzaware(msg_dt)
                except Exception:
                    msg_dt = None
            if msg_dt and msg_dt < cutoff:
                # Older than cutoff; skip
                continue

            subject = normalize_text(msg.get("Subject") or "")
            from_ = normalize_text(msg.get("From") or "")
            to_ = normalize_text(msg.get("To") or "")
            cc_ = normalize_text(msg.get("Cc") or "")
            message_id = (msg.get("Message-Id") or msg.get("Message-ID") or "").strip()
            in_reply_to = (msg.get("In-Reply-To") or "").strip()
            references = normalize_text(msg.get("References") or "")
            thread_key = in_reply_to or references.split()[:1][0] if references else message_id

            body_text = normalize_text(pick_body(msg))
            if not body_text:
                continue

            checksum = hashlib.sha1((subject + body_text).encode("utf-8")).hexdigest()
            if checksum in seen_checksums:
                continue

            record = {
                "id": hash_id(message_id, thread_key, str(idx)),
                "text": body_text,
                "metadata": {
                    "doc_type": "email",
                    "source": "mbox",
                    "subject": subject,
                    "from": from_,
                    "to": to_,
                    "cc": cc_,
                    "message_id": message_id,
                    "thread_id": thread_key or message_id,
                    "created_at": (msg_dt or datetime.now(timezone.utc)).isoformat(),
                    "year_month": (msg_dt or datetime.now(timezone.utc)).strftime("%Y-%m"),
                },
            }

            line = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
            gz.write(line)
            written_count += 1
            seen_checksums.add(checksum)

            # Periodic state save
            if written_count % 200 == 0:
                save_state(state_path, {
                    "seen_checksums": list(seen_checksums),
                    "processed_count": processed_count,
                    "written_count": written_count,
                })

            if max_records and written_count >= max_records:
                break

    save_state(state_path, {
        "seen_checksums": list(seen_checksums),
        "processed_count": processed_count,
        "written_count": written_count,
    })
    print(f"Completed. Processed={processed_count}, Written={written_count}")


def main():
    if len(sys.argv) < 3:
        print("Usage: PYTHONPATH=. python -u backend/scripts/mbox_to_jsonl.py <mbox_path> <out_jsonl_gz> [months_back=6] [state_file]")
        sys.exit(1)
    mbox_path = Path(sys.argv[1]).expanduser()
    out_jsonl_gz = Path(sys.argv[2]).expanduser()
    months_back = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    state_file = Path(sys.argv[4]).expanduser() if len(sys.argv) > 4 else out_jsonl_gz.with_name(out_jsonl_gz.stem + STATE_FILE_DEFAULT)

    parse_mbox(mbox_path, out_jsonl_gz, state_file, months_back=months_back)


if __name__ == "__main__":
    main()


