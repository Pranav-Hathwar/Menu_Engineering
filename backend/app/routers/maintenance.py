"""Data-retention endpoints.

Policy: keep the current + previous month. Older data is only removed after
the owner explicitly confirms (the frontend shows an OK dialog and only then
calls the DELETE endpoint).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.analytics import RetentionStatus
from app.services.auth_service import get_current_user
from app.services.report_service import get_retention_status, purge_old_months

router = APIRouter()


@router.get("/retention", response_model=RetentionStatus)
def retention_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_retention_status(db, owner_id=current_user.id)


@router.delete("/retention/old-months")
def clear_old_months(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return purge_old_months(db, owner_id=current_user.id)
