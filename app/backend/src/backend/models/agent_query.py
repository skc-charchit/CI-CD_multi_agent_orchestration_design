"""Database model for completed Agentic AI turns."""

from datetime import date, datetime
from typing import Any

from backend.db.base import Base
from sqlalchemy import JSON, Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column


class AgentQuery(Base):
    """One successfully answered user turn and its tool activity."""

    __tablename__ = "agent_queries"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column("query", Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    input_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
    )
    output_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tools_used: Mapped[list[dict[str, Any]]] = mapped_column(
        "tools_called",
        JSON,
        nullable=False,
        default=list,
    )
    query_date: Mapped[date] = mapped_column(Date, nullable=False)
