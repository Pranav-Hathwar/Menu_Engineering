"""Authentication endpoints."""

import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import AuthMessage, Token, UserCreate, UserResponse
from app.services.auth_service import authenticate_user, create_user, get_current_user, normalize_email
from app.utils.security import create_access_token

router = APIRouter()
_failed_logins: dict[str, deque[float]] = defaultdict(deque)


def _rate_limit_key(request: Request, email: str) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{normalize_email(email)}"


def _assert_login_allowed(key: str):
    now = time.time()
    attempts = _failed_logins[key]
    while attempts and now - attempts[0] > settings.LOGIN_LOCKOUT_SECONDS:
        attempts.popleft()
    if len(attempts) >= settings.LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
        )


def _record_failed_login(key: str):
    _failed_logins[key].append(time.time())


def _clear_failed_logins(key: str):
    _failed_logins.pop(key, None)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db=db, user=user)


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    key = _rate_limit_key(request, form_data.username)
    _assert_login_allowed(key)

    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        _record_failed_login(key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _clear_failed_logins(key)
    access_token = create_access_token(data={"sub": user.email, "uid": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", response_model=AuthMessage)
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully. Remove the token on the client."}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
