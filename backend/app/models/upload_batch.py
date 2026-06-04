"""
app/models/upload_batch.py

Tracks each ingestion as a first-class record so uploads can be listed,
de-duplicated (via content hash), and deleted as a unit.
"""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func

from app.database import Base


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id = Column(Integer, primary_key=True, index=True)
    # The UUID also stamped onto every SalesData row in this batch.
    batch_id = Column(String, unique=True, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    restaurant_name = Column(String, index=True, nullable=False)
    filename = Column(String, nullable=True)
    # sha256 of the raw uploaded bytes — used to reject exact re-uploads.
    content_hash = Column(String, index=True, nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
