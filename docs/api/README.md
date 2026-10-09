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

## Feature contract ownership

Each feature owns its route declarations and public schemas. The shared
`backend/api/router.py` only composes these routers under the API version
prefix; it must not become a home for feature business logic.

For Agentic AI, see
[`backend/features/agentic_ai/README.md`](../../app/backend/src/backend/features/agentic_ai/README.md).
The proposed asynchronous run contract is documented in
[`agentic-ai-draft.md`](./agentic-ai-draft.md); it is intentionally not in the
live OpenAPI snapshot. Before implementing it, agree on request limits,
authentication/authorization, idempotency, accepted/run status semantics,
status transitions, result and error shapes, cancellation, and timeout policy.
Add the approved decisions to the feature's Pydantic schemas and route metadata
so they appear in the generated OpenAPI contract. Do not promise queueing,
persistence, or execution guarantees until the system actually provides them.

Use additive, backward-compatible changes within `/api/v1` where possible. If
an incompatible public contract change is necessary, introduce a new API
version and migrate consumers deliberately.
