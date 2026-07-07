"""Email auto-ingestion endpoints: status + manual "check inbox now"."""

from fastapi import APIRouter, Depends

from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.email_ingest_service import ingest_status, poll_inbox_once

router = APIRouter()


@router.get("/status")
def get_ingest_status(current_user: User = Depends(get_current_user)):
    return ingest_status()


@router.post("/run")
def run_ingest_now(current_user: User = Depends(get_current_user)):
    """Poll the report inbox immediately instead of waiting for the scheduler."""
    return poll_inbox_once()
