"""PostgreSQL engine and request-scoped session helpers."""

from collections.abc import Generator

from backend.db.engine import engine
from sqlalchemy.orm import Session, sessionmaker

SessionLocal: sessionmaker[Session] | None = (
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
    if engine is not None
    else None
)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session."""
    if SessionLocal is None:
        raise RuntimeError(
            "Database is not configured. Set DATABASE_URL or all POSTGRES_* "
            "settings to persist agent conversations."
        )
    with SessionLocal() as session:
        yield session
