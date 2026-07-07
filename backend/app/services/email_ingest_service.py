"""IMAP inbox poller that auto-ingests POS daily-report emails.

Flow: the POS emails its end-of-day report (CSV/Excel/JSON attachment) to the
inbox configured in ``INGEST_EMAIL``. A background thread polls that inbox
every ``INGEST_POLL_MINUTES`` and pushes each attachment through the exact
same ``process_upload`` pipeline the manual Upload page uses — so header
discovery, date parsing, cleaning, and the duplicate-file guard all apply.
A re-sent report is skipped as a duplicate, which makes polling idempotent.

Fetching a message marks it \\Seen, so each email is only processed once;
failures are recorded in the status (visible on the Upload page) rather than
retried forever.
"""

from __future__ import annotations

import email
import email.utils
import imaplib
import logging
import threading
import time
from datetime import datetime, timezone
from email.header import decode_header

from fastapi import HTTPException

from app.config import settings
from app.database import SessionLocal
from app.models.user import User
from app.services.upload_service import process_upload

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json"}

_status_lock = threading.Lock()
_status = {
    "last_check": None,
    "last_result": "Not checked yet.",
    "emails_processed": 0,
    "files_ingested": 0,
    "duplicates_skipped": 0,
}
_poller_started = False


def _is_configured() -> bool:
    """A real inbox is set — not blank and not the .env placeholder text."""
    email_id = (settings.INGEST_EMAIL or "").strip()
    password = (settings.INGEST_EMAIL_PASSWORD or "").strip()
    if not email_id or not password or "@" not in email_id:
        return False
    return not (email_id.upper().startswith("PUT-") or password.upper().startswith("PUT-"))


def ingest_status() -> dict:
    with _status_lock:
        snapshot = dict(_status)
    return {
        "enabled": settings.INGEST_ENABLED,
        "configured": _is_configured(),
        "inbox": settings.INGEST_EMAIL if _is_configured() else "(not set — add INGEST_EMAIL to backend/.env)",
        "restaurant_name": settings.INGEST_RESTAURANT_NAME,
        "poll_minutes": settings.INGEST_POLL_MINUTES,
        **snapshot,
    }


def poll_inbox_once() -> dict:
    """Check the inbox for unread emails and ingest their report attachments."""
    if not _is_configured():
        detail = (
            "Inbox not configured. Set INGEST_EMAIL and INGEST_EMAIL_PASSWORD "
            "in backend/.env, then restart the backend."
        )
        _record_status(detail)
        return {"ok": False, "detail": detail, "details": []}

    emails_seen = ingested = skipped = failed = 0
    details: list[str] = []

    try:
        mailbox = imaplib.IMAP4_SSL(settings.INGEST_IMAP_HOST, settings.INGEST_IMAP_PORT)
        try:
            mailbox.login(settings.INGEST_EMAIL, settings.INGEST_EMAIL_PASSWORD)
            mailbox.select("INBOX")
            _, data = mailbox.search(None, "UNSEEN")
            for message_id in data[0].split():
                _, message_data = mailbox.fetch(message_id, "(RFC822)")
                message = email.message_from_bytes(message_data[0][1])
                outcome = ingest_email_message(message)
                emails_seen += 1
                ingested += outcome["ingested"]
                skipped += outcome["skipped"]
                failed += outcome["failed"]
                details.extend(outcome["details"])
        finally:
            try:
                mailbox.logout()
            except Exception:  # pragma: no cover - best-effort cleanup
                pass
    except Exception as exc:
        logger.exception("Email ingestion poll failed")
        detail = f"Inbox check failed: {exc}"
        _record_status(detail)
        return {"ok": False, "detail": detail, "details": details}

    summary = (
        f"Checked inbox: {emails_seen} new email(s), {ingested} file(s) ingested, "
        f"{skipped} duplicate(s) skipped, {failed} failed."
    )
    _record_status(summary, emails_seen, ingested, skipped)
    logger.info(summary)
    return {"ok": True, "detail": summary, "details": details}


def ingest_email_message(message, session_factory=None) -> dict:
    """Ingest one parsed email message. Separated out so tests can drive it."""
    session_factory = session_factory or SessionLocal
    sender = email.utils.parseaddr(message.get("From", ""))[1].lower()

    allowed = [s.strip().lower() for s in settings.INGEST_ALLOWED_SENDERS.split(",") if s.strip()]
    if allowed and sender not in allowed:
        return _outcome(details=[f"Ignored email from {sender}: sender not in INGEST_ALLOWED_SENDERS."])

    attachments = extract_report_attachments(message)
    if not attachments:
        return _outcome(details=[f"Email from {sender} had no CSV/Excel/JSON attachment — ignored."])

    # The email's own sent date is a strong hint for reports whose files carry
    # no date column — a daily report emailed at closing covers that same day.
    email_date = None
    try:
        sent = email.utils.parsedate_to_datetime(message.get("Date", ""))
        if sent is not None:
            email_date = sent.date()
    except (TypeError, ValueError):
        email_date = None

    ingested = skipped = failed = 0
    details: list[str] = []
    db = session_factory()
    try:
        owner = _resolve_owner(db)
        for filename, blob in attachments:
            try:
                result = process_upload(
                    blob,
                    filename,
                    db,
                    restaurant_name=settings.INGEST_RESTAURANT_NAME,
                    owner_id=owner.id,
                    date_hint=email_date,
                )
                ingested += 1
                details.append(f"Ingested {filename}: {result['rows_ingested']} rows, revenue {result['total_revenue']}.")
            except HTTPException as exc:
                db.rollback()
                if exc.status_code == 409:
                    skipped += 1
                    details.append(f"Skipped {filename}: identical file already ingested.")
                else:
                    failed += 1
                    details.append(f"Failed {filename}: {exc.detail}")
            except Exception as exc:  # keep one bad attachment from killing the batch
                db.rollback()
                failed += 1
                logger.exception("Ingesting attachment %s failed", filename)
                details.append(f"Failed {filename}: {exc}")
    finally:
        db.close()

    return _outcome(ingested, skipped, failed, details)


def extract_report_attachments(message) -> list[tuple[str, bytes]]:
    attachments = []
    for part in message.walk():
        filename = part.get_filename()
        if not filename:
            continue
        decoded = _decode_header_value(filename)
        extension = decoded.lower().rsplit(".", 1)[-1] if "." in decoded else ""
        if extension not in ALLOWED_EXTENSIONS:
            continue
        payload = part.get_payload(decode=True)
        if payload:
            attachments.append((decoded, payload))
    return attachments


def start_background_poller() -> None:
    """Start the daemon polling thread once (no-op unless INGEST_ENABLED)."""
    global _poller_started
    if _poller_started or not settings.INGEST_ENABLED:
        return
    _poller_started = True

    def _loop():
        while True:
            try:
                poll_inbox_once()
            except Exception:  # pragma: no cover - loop must never die
                logger.exception("Email ingestion loop error")
            time.sleep(max(60, settings.INGEST_POLL_MINUTES * 60))

    threading.Thread(target=_loop, daemon=True, name="email-ingest-poller").start()
    logger.info(
        "Email ingestion poller started: inbox=%s every %s min",
        settings.INGEST_EMAIL or "(unset)",
        settings.INGEST_POLL_MINUTES,
    )


def _resolve_owner(db) -> User:
    if settings.INGEST_OWNER_EMAIL:
        owner = (
            db.query(User)
            .filter(User.email == settings.INGEST_OWNER_EMAIL.strip().lower())
            .first()
        )
        if owner:
            return owner
        logger.warning("INGEST_OWNER_EMAIL %s not found; falling back to first user", settings.INGEST_OWNER_EMAIL)
    owner = db.query(User).order_by(User.id.asc()).first()
    if owner is None:
        raise RuntimeError("No MenuMind account exists yet — register a user before enabling ingestion.")
    return owner


def _decode_header_value(value: str) -> str:
    parts = decode_header(value)
    decoded = ""
    for text, charset in parts:
        decoded += text.decode(charset or "utf-8", errors="replace") if isinstance(text, bytes) else text
    return decoded.strip()


def _outcome(ingested: int = 0, skipped: int = 0, failed: int = 0, details: list[str] | None = None) -> dict:
    return {"ingested": ingested, "skipped": skipped, "failed": failed, "details": details or []}


def _record_status(result: str, emails: int = 0, ingested: int = 0, skipped: int = 0) -> None:
    with _status_lock:
        _status["last_check"] = datetime.now(timezone.utc).isoformat()
        _status["last_result"] = result
        _status["emails_processed"] += emails
        _status["files_ingested"] += ingested
        _status["duplicates_skipped"] += skipped
