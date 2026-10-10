# API contracts

## Source of truth

FastAPI route declarations and Pydantic schemas are the source of truth for the
HTTP API. The live OpenAPI document is available at `/openapi.json`; Swagger UI
is at `/docs`. The reviewed snapshot in [openapi.json](./openapi.json) is
checked into the repository so frontend and backend contributors can review
contract changes in pull requests without a running service.

After changing a route, request/response model, or documented status code:

```bash
uv run python scripts/export_openapi.py
uv run python scripts/export_openapi.py --check
```

Review the OpenAPI diff as part of the same change. CI runs `--check` and fails
if the snapshot no longer matches the implementation.

## Current endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | API overview |
| `GET` | `/api/v1/health` | Process health probe |
| `POST` | `/api/v1/examples/echo` | Validated request/response example |
| `POST` | `/api/v1/agentic-ai/chat` | Synchronous OpenAI arithmetic assistant |
| `GET` | `/api/v1/agentic-ai/history` | Browse persisted agent turns |

### `POST /api/v1/examples/echo`

Request:

```json
{
  "message": "Hello from Feature Studio"
}
```

Successful response (`200 OK`):

```json
{
  "id": "c73a7712-e636-4e3c-a672-67374347daf2",
  "message": "Hello from Feature Studio",
  "received_at": "2026-10-09T12:30:00Z"
}
```

`message` is required and must contain 1–500 characters. Invalid request
bodies receive FastAPI's `422 Unprocessable Entity` validation response. This
demonstration does not store the message or start an AI workflow.

### `POST /api/v1/agentic-ai/chat`

Request:

```json
{
  "message": "What is 19 + 23?"
}
```

Successful response (`200 OK`):

```json
{
  "answer": "19 + 23 = 42."
}
```

`message` is required and limited to 2,000 characters. Missing OpenAI
credentials, database configuration, or server-side API-key configuration
return `503 Service Unavailable`; missing or invalid bearer credentials return
`401 Unauthorized`. Send `Authorization: Bearer <AGENT_API_KEY>` from a
trusted server-side client. Do not expose this key in browser code. Each
request is a separate turn; its question, answer, UTC input/output timestamps,
and tool names/arguments/results are saved in the PostgreSQL `agent_queries`
table. Requests invoke the configured OpenAI model and may incur provider
charges.

### `GET /api/v1/agentic-ai/history`

Use this authenticated endpoint in Swagger to browse saved turns, including
the question, answer, input/output timestamps, and tool calls/results. It
returns the newest turns first and accepts `limit` (1–100, default 50) and
`offset` (default 0) query parameters for pagination.

Successful response (`200 OK`):

```json
{
  "items": [
    {
      "id": 12,
      "question": "What is 19 + 23?",
      "answer": "The answer is 42.",
      "input_at": "2026-10-10T12:30:00Z",
      "output_at": "2026-10-10T12:30:01Z",
      "tools_used": [
        {
          "name": "add",
          "arguments": {"a": 19, "b": 23},
          "result": "42"
        }
      ]
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

The endpoint uses the same server-side bearer authentication as the chat
endpoint and does not invoke the model.

## Feature contract ownership

Each feature owns its route declarations and public schemas. The shared
`backend/api/router.py` only composes these routers under the API version
prefix; it must not become a home for feature business logic.

For Agentic AI, see
[`backend/features/agentic_ai/README.md`](../../app/backend/src/backend/features/agentic_ai/README.md).
The proposed asynchronous run contract is separately documented in
[`agentic-ai-draft.md`](./agentic-ai-draft.md) and is not implemented by the
synchronous chat endpoint.

Use additive, backward-compatible changes within `/api/v1` where possible. If
an incompatible public contract change is necessary, introduce a new API
version and migrate consumers deliberately.
