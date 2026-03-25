from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.utils.security import get_password_hash

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    if not db.query(User).filter(User.email == "admin@restaurant.com").first():
        admin = User(email="admin@restaurant.com", hashed_password=get_password_hash("password123"))
        db.add(admin)
        db.commit()
        print("SUCCESS: Admin User Created")
    else:
        print("SUCCESS: Admin User Already Exists")
except Exception as e:
    print(f"ERROR: {e}")
finally:
    db.close()
