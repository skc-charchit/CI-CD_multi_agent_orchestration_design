"""Small reusable CRUD operations for SQLAlchemy ORM models."""

from typing import Any

from backend.db.base import Base
from sqlalchemy import select
from sqlalchemy.orm import Session


def get_record[ModelT: Base](
    session: Session,
    model: type[ModelT],
    record_id: Any,
) -> ModelT | None:
    """Return one model instance by its primary key."""
    return session.get(model, record_id)


def list_records[ModelT: Base](
    session: Session,
    model: type[ModelT],
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[ModelT]:
    """Return a bounded page of model instances."""
    if offset < 0 or limit < 1:
        raise ValueError("offset must be non-negative and limit must be positive")
    statement = select(model).offset(offset).limit(limit)
    return list(session.scalars(statement).all())


def create_record[ModelT: Base](
    session: Session,
    model: type[ModelT],
    values: dict[str, object],
) -> ModelT:
    """Create and persist a model instance using the current transaction."""
    record = model()
    for field, value in values.items():
        setattr(record, field, value)
    session.add(record)
    session.flush()
    session.refresh(record)
    return record


def update_record[ModelT: Base](
    session: Session,
    record: ModelT,
    values: dict[str, object],
) -> ModelT:
    """Update fields on a model instance using the current transaction."""
    for field, value in values.items():
        setattr(record, field, value)
    session.flush()
    session.refresh(record)
    return record


def delete_record(session: Session, record: Base) -> None:
    """Delete a model instance using the current transaction."""
    session.delete(record)
    session.flush()
