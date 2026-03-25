"""
app/services/upload_service.py

Handles reading CSV/Excel files into Pandas, cleaning the data, 
mapping columns based on aliases, and storing to the SalesData table.
"""
import pandas as pd
import io
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.sales import SalesData

# Define the acceptable aliases for each core column
COLUMN_MAPPINGS = {
    "item_name": ["item_name", "item", "product", "name"],
    "quantity": ["quantity", "qty"],
    "revenue": ["revenue", "price", "total"],
    "date": ["date"]
}

def process_upload(file_bytes: bytes, filename: str, db: Session):
    # 1. Load data into Pandas DataFrame based on file extension
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Upload CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File reading error: {str(e)}")

    # 2. Normalize raw column names (lowercase and strip whitespace)
    df.columns = df.columns.astype(str).str.lower().str.strip()

    # 3. Detect and map columns
    mapped_columns = {}
    for standard_name, aliases in COLUMN_MAPPINGS.items():
        found = False
        for col in df.columns:
            if col in aliases:
                mapped_columns[standard_name] = col
                found = True
                break
        if not found:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing column for '{standard_name}'. Expected one of: {aliases}"
            )

    # Apply the mapping
    rename_mapping = {original: standard for standard, original in mapped_columns.items()}
    df = df.rename(columns=rename_mapping)

    # Filter to only the columns we care about
    df = df[["item_name", "quantity", "revenue", "date"]]

    # 4. Data Cleaning
    # Drop rows with any missing crucial values
    df = df.dropna()

    # Drop exact duplicates
    df = df.drop_duplicates()

    # Strip whitespace and title-case the item names
    df["item_name"] = df["item_name"].astype(str).str.strip().str.title()

    # Enforce data types
    try:
        df["quantity"] = pd.to_numeric(df["quantity"], errors='coerce').fillna(0).astype(int)
        df["revenue"] = pd.to_numeric(df["revenue"], errors='coerce').fillna(0.0).astype(float)
        # Parse dates. Any unparseable dates become NaT
        df["date"] = pd.to_datetime(df["date"], errors='coerce').dt.date
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Type conversion error: {str(e)}")

    # Drop rows where date parsing failed (NaT)
    df = df.dropna(subset=["date"])

    # 5. Store cleaned data into SalesData table
    # We leave menu_item_id null for now per the "Start simple" constraint.
    records = df.to_dict(orient="records")
    sales_objects = [SalesData(**row) for row in records]
    
    db.add_all(sales_objects)
    db.commit()
    
    return {"message": f"Successfully cleaned and inserted {len(sales_objects)} sales records."}
