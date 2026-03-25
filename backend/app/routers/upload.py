"""
app/routers/upload.py

Exposes the file upload endpoint.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.upload_service import process_upload
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter()

@router.post("")
@router.post("/")
async def upload_sales_data(
    restaurant_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts CSV or Excel files and a restaurant name, cleans them, and maps logically.
    """
    contents = await file.read()
    result = process_upload(contents, file.filename, db, restaurant_name)
    return result
