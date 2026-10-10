"""PostgreSQL URL, engine, and connectivity helpers."""

from backend.core.config import Settings, settings
from sqlalchemy import URL, create_engine, make_url, text
from sqlalchemy.engine import Engine


def build_database_url(config: Settings) -> URL | None:
    """Build a PostgreSQL URL from settings, or return None if unconfigured."""
    postgres_settings = (
        config.postgres_host,
        config.postgres_port,
        config.postgres_db,
        config.postgres_user,
        config.postgres_password,
    )
    if config.database_url is not None:
        if any(value is not None for value in postgres_settings):
            raise ValueError(
                "Set either DATABASE_URL or POSTGRES_* settings, not both."
            )
        url = make_url(config.database_url.get_secret_value())
        if url.get_backend_name() != "postgresql":
            raise ValueError("DATABASE_URL must use PostgreSQL.")
        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg")
        elif url.drivername != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use the psycopg driver.")
        return url

    if not any(value is not None for value in postgres_settings):
        return None

    required_settings = {
        "POSTGRES_HOST": config.postgres_host,
        "POSTGRES_DB": config.postgres_db,
        "POSTGRES_USER": config.postgres_user,
        "POSTGRES_PASSWORD": config.postgres_password,
    }
    missing = [name for name, value in required_settings.items() if value is None]
    if missing:
        raise ValueError(
            "Incomplete PostgreSQL configuration; missing " + ", ".join(missing)
        )

    assert config.postgres_host is not None
    assert config.postgres_db is not None
    assert config.postgres_user is not None
    assert config.postgres_password is not None
    return URL.create(
        "postgresql+psycopg",
        username=config.postgres_user,
        password=config.postgres_password.get_secret_value(),
        host=config.postgres_host,
        port=config.postgres_port or 5432,
        database=config.postgres_db,
    )


database_url = build_database_url(settings)
engine: Engine | None = (
    create_engine(database_url, pool_pre_ping=True)
    if database_url is not None
    else None
)


def check_database_connection() -> None:
    """Verify the configured database is reachable."""
    if engine is not None:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
