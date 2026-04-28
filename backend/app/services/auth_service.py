"""Authentication and current-user business logic."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenData, UserCreate
from app.utils.security import get_password_hash, verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == normalize_email(email)).first()


def create_user(db: Session, user: UserCreate):
    email = normalize_email(user.email)
    if get_user_by_email(db, email=email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    db_user = User(email=email, hashed_password=get_password_hash(user.password), is_active=True)
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from exc
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception
        email = payload.get("sub")
        user_id = payload.get("uid")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, user_id=user_id, token_type=payload.get("type"))
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = get_user_by_email(db, email=token_data.email)
    if user is None or not user.is_active:
        raise credentials_exception
    if token_data.user_id is not None and user.id != token_data.user_id:
        raise credentials_exception
    return user
