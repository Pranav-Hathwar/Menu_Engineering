"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import MenuItem, SalesData, User  # noqa: F401
from app.services.schema_service import ensure_runtime_schema

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

if settings.AUTO_CREATE_TABLES:
    try:
        Base.metadata.create_all(bind=engine)
        ensure_runtime_schema(engine, SessionLocal)
    except Exception:
        logger.exception("Database initialization failed")

app = FastAPI(
    title=settings.APP_NAME,
    description="Restaurant menu engineering and analytics platform",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import analytics, auth, sales, upload  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": "0.2.0",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
