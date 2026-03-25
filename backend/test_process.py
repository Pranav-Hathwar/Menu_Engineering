from app.database import SessionLocal
from app.services.upload_service import process_upload

def run_test():
    db = SessionLocal()
    with open(r"c:\Users\Pranav\OneDrive\Desktop\Menu_Engineering\frontend\package.json", "rb") as f:
        pass # just to check paths
        
    csv_data = b"Item Name,Quantity,Revenue\nBurger,5,15.00\nFries,10,5.00"
    
    try:
        res = process_upload(csv_data, "test.csv", db, "burger shop")
        print("PYTHON INTERNAL SUCCESS:", res)
    except Exception as e:
        print("PYTHON INTERNAL ERROR FATAL:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
