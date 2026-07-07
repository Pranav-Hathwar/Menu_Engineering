"""File upload + batch management endpoints."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.upload_service import delete_upload_batch, list_upload_batches, process_upload

router = APIRouter()


@router.post("")
@router.post("/")
async def upload_sales_data(
    restaurant_name: str = Form(..., min_length=1, max_length=160),
    file: UploadFile = File(...),
    allow_duplicate: bool = Form(False),
    report_date: Optional[date] = Form(
        None,
        description="Date the report covers; used when the file itself has no date column.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(contents) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is too large. Maximum supported size is {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    return process_upload(
        contents,
        file.filename or "upload.csv",
        db,
        restaurant_name=restaurant_name,
        owner_id=current_user.id,
        allow_duplicate=allow_duplicate,
        report_date=report_date,
    )


@router.get("/batches")
def get_batches(
    restaurant_name: Optional[str] = Query(None, description="Restaurant filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_upload_batches(db, owner_id=current_user.id, restaurant_name=restaurant_name)


@router.delete("/batches/{batch_id}")
def remove_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = delete_upload_batch(db, owner_id=current_user.id, batch_id=batch_id)
    return {"message": f"Deleted batch and {deleted} sales row(s).", "rows_deleted": deleted}
