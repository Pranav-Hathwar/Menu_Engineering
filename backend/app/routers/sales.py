"""
app/routers/sales.py

Provides CRUD API endpoints for SalesData.
These routes are protected, requiring the user to be authenticated.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.sales import SalesData
from app.schemas.sales import SalesDataCreate, SalesDataResponse
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter()

@router.post("/", response_model=SalesDataResponse, status_code=status.HTTP_201_CREATED)
def create_sales_record(
    sale: SalesDataCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Insert a new sales record."""
    db_sale = SalesData(**sale.model_dump())
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.get("/", response_model=List[SalesDataResponse])
def get_all_sales(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch all sales records with optional pagination."""
    sales = db.query(SalesData).offset(skip).limit(limit).all()
    return sales

@router.get("/{sale_id}", response_model=SalesDataResponse)
def get_sale(
    sale_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch a specific sales record by ID."""
    sale = db.query(SalesData).filter(SalesData.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sales record not found")
    return sale

@router.put("/{sale_id}", response_model=SalesDataResponse)
def update_sale(
    sale_id: int, 
    sale_update: SalesDataCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a specific sales record."""
    sale = db.query(SalesData).filter(SalesData.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sales record not found")
    
    for key, value in sale_update.model_dump().items():
        setattr(sale, key, value)
    
    db.commit()
    db.refresh(sale)
    return sale

@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sale(
    sale_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific sales record."""
    sale = db.query(SalesData).filter(SalesData.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sales record not found")
    
    db.delete(sale)
    db.commit()
    return None
