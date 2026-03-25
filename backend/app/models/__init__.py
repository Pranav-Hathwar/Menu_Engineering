"""
app/models/__init__.py

Centralizes model imports. 
Importing this file ensures that SQLAlchemy registers all models with `Base.metadata`
before calls to `Base.metadata.create_all()` are made.
"""
from app.models.user import User  # noqa: F401
from app.models.menu import MenuItem  # noqa: F401
from app.models.sales import SalesData  # noqa: F401
