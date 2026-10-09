# Agentic AI feature

This package is the boundary for the agentic AI capability. Keep its HTTP
routes, public request/response schemas, orchestration services, and
feature-specific persistence together here instead of adding AI behavior to
shared API infrastructure or another feature.

The initial asynchronous run API proposal is in
[`docs/api/agentic-ai-draft.md`](../../../../../../docs/api/agentic-ai-draft.md).
It is a design draft, not an implemented endpoint or a promise that work is
durably queued.

When implementing the first workflow, add the smallest vertical slice:

```text
agentic_ai/
├── api/routes.py       # HTTP endpoints; request/response mapping only
├── schemas.py          # Public Pydantic request and response contracts
├── service.py          # Workflow use cases and orchestration boundary
├── models.py           # Domain types when the workflow needs them
└── repository.py       # Persistence boundary when durable state is added
```

Register its router in `backend/api/router.py`. FastAPI generates the API
contract at `/openapi.json` from the route declarations and Pydantic schemas;
export and review the snapshot in `docs/api/openapi.json` when a contract
changes. Document authentication, accepted input limits, status transitions,
failure responses, idempotency, and timeout behavior before exposing any
long-running run endpoint.

Do not report a run as queued or accepted until a durable store and worker
actually provide that behavior. Model-provider access and tool execution must
stay on the server side and have explicit authorization, budgets, timeouts,
audit logging, and human approval rules where appropriate.
