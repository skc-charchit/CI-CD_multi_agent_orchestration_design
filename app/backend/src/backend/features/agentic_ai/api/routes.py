"""HTTP routes for the Agentic AI feature."""

import hmac
from collections.abc import Generator
from typing import Annotated

from backend.core.config import get_settings
from backend.db.session import SessionLocal, get_db
from backend.features.agentic_ai.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    AgentHistoryResponse,
    AgentQueryResponse,
)
from backend.features.agentic_ai.service import answer_message, list_saved_turns
from backend.features.agentic_ai.tools import ModelConfigurationError
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

router = APIRouter(prefix="/agentic-ai", tags=["agentic-ai"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_agent_session() -> Generator[Session, None, None]:
    """Provide a database session and return an actionable config error."""
    if SessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database is not configured. Set DATABASE_URL or all POSTGRES_* "
                "settings to persist agent conversations."
            ),
        )
    yield from get_db()


def require_agent_api_key(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> None:
    """Require the configured server-side bearer key before calling OpenAI."""
    configured_key = get_settings().agent_api_key
    if configured_key is None:
        raise HTTPException(
            status_code=503,
            detail="Agent API authentication is not configured.",
        )
    if credentials is None or not hmac.compare_digest(
        credentials.credentials,
        configured_key.get_secret_value(),
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="Ask the arithmetic assistant",
    dependencies=[Depends(require_agent_api_key)],
)
def chat(
    request: AgentChatRequest,
    session: Annotated[Session, Depends(get_agent_session)],
) -> AgentChatResponse:
    """Generate and persist the answer for a single message."""
    try:
        turn = answer_message(request.message, session)
    except ModelConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return AgentChatResponse(answer=turn.answer)


@router.get(
    "/history",
    response_model=AgentHistoryResponse,
    summary="List saved agent turns",
    dependencies=[Depends(require_agent_api_key)],
)
def history(
    session: Annotated[Session, Depends(get_agent_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AgentHistoryResponse:
    """Return persisted turns, newest first, for viewing in Swagger."""
    turns, total = list_saved_turns(session, limit=limit, offset=offset)
    return AgentHistoryResponse(
        items=[AgentQueryResponse.model_validate(turn) for turn in turns],
        total=total,
        limit=limit,
        offset=offset,
    )
