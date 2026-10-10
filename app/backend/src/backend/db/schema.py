"""Initialize database tables needed by the running application."""

from backend.db.engine import engine
from backend.models import AgentQuery
from sqlalchemy import inspect, text


def create_schema(*, required: bool = False) -> None:
    """Create or safely upgrade the agent query table."""
    if engine is None:
        if required:
            raise RuntimeError(
                "Database is not configured. Set DATABASE_URL or all POSTGRES_* "
                "settings to persist agent conversations."
            )
        return

    if engine.dialect.name != "postgresql":
        AgentQuery.metadata.create_all(engine)
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtext('backend.agent_queries.schema'))"
            )
        )
        inspector = inspect(connection)
        if "agent_queries" not in inspector.get_table_names():
            AgentQuery.metadata.create_all(connection)
            return

        columns = {
            column["name"]: column for column in inspector.get_columns("agent_queries")
        }
        required_columns = {
            "id",
            "query",
            "answer",
            "tools_called",
            "created_at",
            "query_date",
        }
        missing_columns = required_columns - columns.keys()
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise RuntimeError(
                "Existing agent_queries table has an unsupported schema; "
                f"missing columns: {missing}."
            )

        if not getattr(columns["created_at"]["type"], "timezone", False):
            connection.execute(
                text(
                    "ALTER TABLE agent_queries "
                    "ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE "
                    "USING created_at AT TIME ZONE 'UTC'"
                )
            )

        connection.execute(
            text(
                "ALTER TABLE agent_queries "
                "ADD COLUMN IF NOT EXISTS output_at TIMESTAMP WITH TIME ZONE"
            )
        )
        output_column = columns.get("output_at")
        if output_column is not None and not getattr(
            output_column["type"],
            "timezone",
            False,
        ):
            connection.execute(
                text(
                    "ALTER TABLE agent_queries "
                    "ALTER COLUMN output_at TYPE TIMESTAMP WITH TIME ZONE "
                    "USING output_at AT TIME ZONE 'UTC'"
                )
            )
        connection.execute(
            text(
                "UPDATE agent_queries SET output_at = created_at "
                "WHERE output_at IS NULL"
            )
        )
        connection.execute(
            text("ALTER TABLE agent_queries ALTER COLUMN output_at SET NOT NULL")
        )
