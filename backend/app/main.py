"""
app/main.py

The entry point of the FastAPI application.

Responsibilities:
  - Create the FastAPI app instance
  - Configure CORS (so the React frontend can talk to this server)
  - Register all routers
  - Create DB tables on startup (dev only — production uses Alembic migrations)
  - Mount a health-check route so you can verify the server is alive
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.models import *  # Ensure models are registered for create_all

# ---------------------------------------------------------------------------
# Create tables — wrapped in try/except so the server starts even without
# a live PostgreSQL connection (useful during local dev without a DB).
# In production, use Alembic migrations instead.
# ---------------------------------------------------------------------------
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[WARNING] Could not connect to database on startup: {e}")
    print("[WARNING] Server starting without DB — connect PostgreSQL and restart.")

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description="Restaurant menu engineering and analytics platform",
    version="0.1.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
)

# ---------------------------------------------------------------------------
# CORS
# Allow the React dev server (port 5173 / 3000) to call this API.
# In production, replace "*" origins with your actual domain.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — add each feature router here as we build them
from app.routers import auth, sales, upload, analytics
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

# Future examples:
#   from app.routers import upload, menu
#   app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
#   app.include_router(menu.router,   prefix="/api/menu",   tags=["Menu"])
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Health check — always keep this alive
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": "0.1.0",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
