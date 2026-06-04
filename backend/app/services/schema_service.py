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

        _backfill_upload_batches(db, inspect(engine))
    finally:
        db.close()


def _backfill_upload_batches(db: Session, inspector) -> None:
    """Create UploadBatch rows for sales uploaded before the table existed.

    Legacy batches have no original bytes, so their content_hash is a synthetic
    'legacy:<batch_id>' sentinel that can never collide with a real sha256.
    """
    if "upload_batches" not in inspector.get_table_names():
        return

    legacy = db.execute(
        text(
            """
            SELECT s.upload_batch_id AS batch_id,
                   MIN(s.owner_id)        AS owner_id,
                   MIN(s.restaurant_name) AS restaurant_name,
                   COUNT(*)               AS row_count,
                   COALESCE(SUM(s.revenue), 0) AS total_revenue
            FROM sales_data s
            WHERE s.upload_batch_id IS NOT NULL
              AND s.upload_batch_id NOT IN (SELECT batch_id FROM upload_batches)
            GROUP BY s.upload_batch_id
            """
        )
    ).fetchall()

    for row in legacy:
        db.execute(
            text(
                """
                INSERT INTO upload_batches
                    (batch_id, owner_id, restaurant_name, filename, content_hash, row_count, total_revenue)
                VALUES
                    (:batch_id, :owner_id, :restaurant_name, :filename, :content_hash, :row_count, :total_revenue)
                """
            ),
            {
                "batch_id": row.batch_id,
                "owner_id": row.owner_id,
                "restaurant_name": row.restaurant_name,
                "filename": "(imported before batch tracking)",
                "content_hash": f"legacy:{row.batch_id}",
                "row_count": row.row_count,
                "total_revenue": round(float(row.total_revenue or 0.0), 2),
            },
        )
    if legacy:
        db.commit()
        logger.info("Backfilled %s legacy upload batch record(s)", len(legacy))
