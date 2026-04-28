"""File upload endpoint."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.upload_service import process_upload

router = APIRouter()


@router.post("")
@router.post("/")
async def upload_sales_data(
    restaurant_name: str = Form(..., min_length=1, max_length=160),
    file: UploadFile = File(...),
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
    )
