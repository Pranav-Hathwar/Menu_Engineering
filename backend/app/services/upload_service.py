"""
app/services/upload_service.py

Handles reading CSV/Excel files into Pandas, aggressively fuzzy-mapping columns, 
and storing unstructured data gracefully to the SalesData table.
"""
import pandas as pd
import io
import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.sales import SalesData

def process_upload(file_bytes: bytes, filename: str, db: Session, restaurant_name: str):
    # 1. Load data into Pandas DataFrame
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes), skip_blank_lines=True)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Upload CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File reading error: {str(e)}")

    # Strip completely blank columns/rows that break parsing
    df = df.dropna(how='all', axis=1).dropna(how='all', axis=0).reset_index(drop=True)
    if df.empty or len(df.columns) == 0:
        raise HTTPException(status_code=400, detail="File appears to be completely empty of data grids.")

    # 1.5 Auto-Header Discovery for messy POS exports
    # Check if current headers are actually valid keywords
    current_cols_str = " ".join(df.columns.astype(str).str.lower())
    keywords = ['item', 'name', 'product', 'menu', 'qty', 'quantity', 'price', 'revenue', 'sales', 'total', 'turnover', 'amount', 'dish']
    
    if not any(k in current_cols_str for k in keywords):
        # The true headers are probably trapped in the data rows due to a top-level metadata block!
        # Scan the first 30 rows looking for a high concentration of keywords
        for idx, row in df.head(30).iterrows():
            row_str = " ".join(row.astype(str).str.lower())
            if sum(k in row_str for k in keywords) >= 2: # Found at least 2 strong operational keywords
                df.columns = row.astype(str).tolist()
                df = df.iloc[idx+1:].reset_index(drop=True)
                break

    # Clean raw column names aggressively
    df.columns = df.columns.astype(str).str.lower().str.strip().str.replace(' ', '').str.replace('_', '').str.replace('.', '').str.replace('-', '')

    mapped_columns = {}
    
    # -------------------------------------------------------------
    # Fuzzy Matching with Extreme Structural Fallbacks
    # -------------------------------------------------------------
    
    # Item Name Mapping
    item_cols = [c for c in df.columns if any(k in c for k in ['item', 'name', 'product', 'menu', 'desc', 'title', 'dish'])]
    if not item_cols:
        # Extreme Fallback: Just grab the literal first column natively
        item_cols = [df.columns[0]]
    mapped_columns["item_name"] = item_cols[0]

    # Quick pre-cast for clean numeric detection
    for col in df.columns:
        if col != mapped_columns["item_name"]:
            # Gently coerce strings to numeric just to populate the dtypes for the fallback engine
            temp = pd.to_numeric(df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False), errors='coerce')
            if not temp.isna().all():
                df[col] = temp

    # Revenue/Price Mapping
    rev_cols = [c for c in df.columns if any(k in c for k in ['rev', 'price', 'total', 'sale', 'cost', 'net', 'gross', 'amount', 'value', 'turnover'])]
    if not rev_cols:
        # Fallback to the LAST numeric column (usually Revenue rests at the far-right of tables)
        num_cols = df.select_dtypes(include=['number', 'float', 'int']).columns
        if len(num_cols) > 0:
            rev_cols = [num_cols[-1]]
        elif len(df.columns) > 1:
            rev_cols = [df.columns[-1]] # Just grab the right-most column
        else:
            rev_cols = [df.columns[0]]
    mapped_columns["revenue"] = rev_cols[0]

    # Quantity Mapping
    qty_cols = [c for c in df.columns if any(k in c for k in ['qty', 'quant', 'count', 'sold', '#', 'vol'])]
    if not qty_cols:
        # Fallback: Prefer the FIRST numeric column (Usually Quantity sits before Revenue)
        num_cols = df.select_dtypes(include=['number', 'float', 'int']).columns
        if len(num_cols) > 0 and num_cols[0] != mapped_columns["revenue"]:
            qty_cols = [num_cols[0]]
        else:
            qty_cols = []
    if qty_cols:
        mapped_columns["quantity"] = qty_cols[0]
    
    # Date Mapping
    date_cols = [c for c in df.columns if 'date' in c or 'time' in c or 'day' in c]
    if date_cols:
        mapped_columns["date"] = date_cols[0]

    # Apply explicit mappings
    rename_mapping = {original: standard for standard, original in mapped_columns.items()}
    df = df.rename(columns=rename_mapping)

    # -------------------------------------------------------------
    # Hard Overrides & Constraints for missing data mappings
    # -------------------------------------------------------------
    if "quantity" not in df.columns:
        df["quantity"] = 1
    if "date" not in df.columns:
        df["date"] = datetime.date.today()

    df = df[["item_name", "quantity", "revenue", "date"]]

    # Drop totally empty generic garbage items
    df = df.dropna(subset=["item_name"])
    df["item_name"] = df["item_name"].astype(str).str.strip().str.title()
    
    # Money safety formatter: Clear currency symbols if interpreted as strings natively
    if df['revenue'].dtype == 'object':
        df['revenue'] = df['revenue'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
    
    # Enforce safe primitives
    df["revenue"] = pd.to_numeric(df["revenue"], errors='coerce').fillna(0.0).astype(float)
    df["quantity"] = pd.to_numeric(df["quantity"], errors='coerce').fillna(1).astype(int)

    # Handle dates elegantly
    df["date"] = pd.to_datetime(df["date"], errors='coerce').dt.date
    df["date"] = df["date"].fillna(datetime.date.today())

    # Exclude metadata junk parsing
    df = df[df["revenue"] > 0]

    # Package structure perfectly matching SQL model architectures
    records = df.to_dict(orient="records")
    if not records:
        raise HTTPException(status_code=400, detail="Data successfully parsed, but no valid priced rows remained! Check formatting.")

    sales_objects = [SalesData(**row, restaurant_name=restaurant_name) for row in records]
    
    db.add_all(sales_objects)
    db.commit()
    
    return {"message": f"Successfully ingested {len(sales_objects)} rows into the engine!"}
