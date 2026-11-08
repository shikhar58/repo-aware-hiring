"""Database access with SQLAlchemy."""
import os

from sqlalchemy import create_engine, text

engine = create_engine(os.environ.get("DATABASE_URL", "postgresql+psycopg://localhost/orders"))


def list_orders(user_id):
    with engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text("SELECT * FROM orders WHERE user_id = :u"), {"u": user_id})]
