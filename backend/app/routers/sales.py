"""CRUD API endpoints for authenticated sales records."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sales import SalesData
from app.models.user import User
from app.schemas.sales import SalesDataCreate, SalesDataResponse
from app.services.auth_service import get_current_user

router = APIRouter()


def _owned_sale_query(db: Session, current_user: User):
    return db.query(SalesData).filter(SalesData.owner_id == current_user.id)


@router.post("/", response_model=SalesDataResponse, status_code=status.HTTP_201_CREATED)
def create_sales_record(
    sale: SalesDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_sale = SalesData(**sale.model_dump(), owner_id=current_user.id)
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale


@router.get("/", response_model=List[SalesDataResponse])
def get_all_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    restaurant_name: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _owned_sale_query(db, current_user)
    if restaurant_name:
        query = query.filter(SalesData.restaurant_name == restaurant_name)
    return query.order_by(SalesData.id.desc()).offset(skip).limit(limit).all()


@router.get("/{sale_id}", response_model=SalesDataResponse)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sale = _owned_sale_query(db, current_user).filter(SalesData.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sales record not found")
    return sale


@router.put("/{sale_id}", response_model=SalesDataResponse)
def update_sale(
    sale_id: int,
    sale_update: SalesDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sale = _owned_sale_query(db, current_user).filter(SalesData.id == sale_id).first()
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
    current_user: User = Depends(get_current_user),
):
    sale = _owned_sale_query(db, current_user).filter(SalesData.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sales record not found")

    db.delete(sale)
    db.commit()
    return None
