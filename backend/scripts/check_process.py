"""Dev helper: run the upload pipeline against an in-process sample CSV.

Usage (from the backend/ directory, with the venv active):
    python scripts/check_process.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.services.upload_service import process_upload  # noqa: E402


def run_check():
    db = SessionLocal()
    csv_data = b"Item Name,Quantity,Revenue\nBurger,5,15.00\nFries,10,5.00"
    try:
        res = process_upload(csv_data, "test.csv", db, "burger shop")
        print("UPLOAD PIPELINE SUCCESS:", res)
    except Exception:
        print("UPLOAD PIPELINE ERROR:")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    run_check()
