"""
Database Engine and Session Configuration
==========================================

Sets up the core SQLAlchemy components used across the application:

- **engine** — A ``create_engine`` instance connected to the PostgreSQL
  database specified by ``DATABASE_URL``.  ``pool_pre_ping`` is enabled to
  transparently reconnect stale connections.  SQL statement logging (``echo``)
  is turned on in development mode only.

- **SessionLocal** — A ``sessionmaker`` factory configured with
  ``autocommit=False`` and ``autoflush=False`` so that transactions are
  explicit.  All CRUD and router code should obtain sessions through the
  ``get_db`` dependency rather than calling ``SessionLocal()`` directly.

- **Base** — The declarative base class that every ORM model inherits from.
  Alembic's ``env.py`` imports ``Base.metadata`` to detect schema changes
  when generating migrations.

- **get_db()** — A FastAPI dependency (generator) that yields a session and
  guarantees it is closed after the request finishes, even on exceptions.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

# ---------------------------------------------------------------------------
# SQLAlchemy engine
# ---------------------------------------------------------------------------
# ``pool_pre_ping=True`` issues a lightweight ``SELECT 1`` before handing out
# a connection from the pool, which guards against "server has gone away"
# errors after idle periods or database restarts.
# For production, consider tuning pool_size / max_overflow for concurrency.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.ENVIRONMENT == "development",  # Log SQL in development
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
# autocommit=False: requires explicit ``db.commit()`` calls.
# autoflush=False:  prevents automatic flushes before queries, giving the
#                   developer full control over when writes hit the DB.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
# All ORM models (User, Role, Batch, Plantation, etc.) inherit from this Base.
# Its ``metadata`` object is referenced by Alembic to auto-generate migrations.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a scoped database session.

    Yields a ``SessionLocal`` instance and ensures it is closed once the
    request completes (or if an unhandled exception occurs).

    Usage::

        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Always close the session to return the connection to the pool
        db.close()
