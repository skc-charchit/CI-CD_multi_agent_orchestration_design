"""Tests for PostgreSQL connection configuration."""

import pytest
from backend.core.config import Settings
from backend.db import schema
from backend.db.base import Base
from backend.db.crud import (
    create_record,
    delete_record,
    get_record,
    list_records,
    update_record,
)
from backend.db.engine import build_database_url
from backend.models import AgentQuery
from pydantic import SecretStr
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Mapped, Session, mapped_column


class Item(Base):
    """Test model used to verify reusable CRUD operations."""

    __tablename__ = "test_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


@pytest.fixture
def db_session():
    """Provide an isolated in-memory database session."""
    test_engine = create_engine("sqlite://")
    Base.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    test_engine.dispose()


def test_build_database_url_from_postgres_settings() -> None:
    config = Settings.model_construct(
        postgres_host="localhost",
        postgres_db="agent_db",
        postgres_user="agent_app",
        postgres_password=SecretStr("local-test-password"),
    )

    url = build_database_url(config)

    assert url is not None
    assert url.drivername == "postgresql+psycopg"
    assert url.host == "localhost"
    assert url.port == 5432
    assert url.database == "agent_db"
    assert url.username == "agent_app"
    assert url.password == "local-test-password"


def test_build_database_url_accepts_postgresql_url() -> None:
    config = Settings.model_construct(
        database_url=SecretStr(
            "postgresql://agent_app:local-test-password@localhost/agent_db"
        )
    )

    url = build_database_url(config)

    assert url is not None
    assert url.drivername == "postgresql+psycopg"
    assert url.database == "agent_db"


def test_build_database_url_returns_none_when_unconfigured() -> None:
    config = Settings.model_construct()

    assert build_database_url(config) is None


def test_build_database_url_rejects_incomplete_settings() -> None:
    config = Settings.model_construct(postgres_host="localhost")

    with pytest.raises(ValueError, match="Incomplete PostgreSQL configuration"):
        build_database_url(config)


def test_create_schema_creates_agent_query_table(monkeypatch) -> None:
    test_engine = create_engine("sqlite://")
    monkeypatch.setattr(schema, "engine", test_engine)

    schema.create_schema(required=True)

    assert inspect(test_engine).has_table(AgentQuery.__tablename__)
    test_engine.dispose()


def test_create_schema_requires_database_when_requested(monkeypatch) -> None:
    monkeypatch.setattr(schema, "engine", None)

    with pytest.raises(RuntimeError, match="Database is not configured"):
        schema.create_schema(required=True)


def test_crud_operations_use_the_callers_transaction(db_session: Session) -> None:
    item = create_record(db_session, Item, {"name": "first"})

    assert item.id == 1
    assert get_record(db_session, Item, item.id) is item
    assert list_records(db_session, Item) == [item]

    updated = update_record(db_session, item, {"name": "updated"})
    assert updated.name == "updated"

    db_session.commit()
    delete_record(db_session, item)
    db_session.commit()

    assert get_record(db_session, Item, item.id) is None


@pytest.mark.parametrize(
    ("offset", "limit"),
    [(-1, 10), (0, 0)],
)
def test_list_records_rejects_invalid_pagination(
    db_session: Session,
    offset: int,
    limit: int,
) -> None:
    with pytest.raises(ValueError, match="offset must be non-negative"):
        list_records(db_session, Item, offset=offset, limit=limit)
