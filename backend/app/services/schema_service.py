"""Runtime schema guards for local/dev databases.

Production deployments should use Alembic migrations. This guard keeps the
current project usable with the existing SQLite files while the migration
folder is introduced later.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.models.user import User

logger = logging.getLogger(__name__)


def ensure_runtime_schema(engine, session_factory):
    inspector = inspect(engine)
    if "sales_data" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("sales_data")}
    additions = {
        "owner_id": "INTEGER",
        "upload_batch_id": "VARCHAR",
    }

    with engine.begin() as connection:
        for column, sql_type in additions.items():
            if column not in existing_columns:
                logger.info("Adding missing sales_data.%s column", column)
                connection.execute(text(f"ALTER TABLE sales_data ADD COLUMN {column} {sql_type}"))

    db: Session = session_factory()
    try:
        first_user = db.query(User).order_by(User.id.asc()).first()
        if first_user:
            db.execute(
                text("UPDATE sales_data SET owner_id = :owner_id WHERE owner_id IS NULL"),
                {"owner_id": first_user.id},
            )
            db.commit()
    finally:
        db.close()
