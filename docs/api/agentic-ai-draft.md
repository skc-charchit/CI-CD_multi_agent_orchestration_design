# Agentic AI run API — design draft

**Status:** Proposed; not implemented and not included in the live OpenAPI
contract. This draft is for frontend/backend collaboration. Approve or revise
it before treating it as a stable client contract.

## Resource model

An agentic workflow is a long-running **run**. Clients submit a run, receive a
stable run identifier, and fetch its status/result separately; the HTTP
request does not stay open while the model reasons or tools execute.

### Submit a run

`POST /api/v1/agentic-ai/runs`

Proposed request:

```json
{
  "input": "Research the latest deployment failure and summarize likely causes."
}
```

Proposed accepted response (`202 Accepted`):

```json
{
  "run_id": "d14db29e-3519-4c2e-b87a-d7ed9f9c04eb",
  "status": "queued",
  "created_at": "2026-10-09T12:30:00Z",
  "status_url": "/api/v1/agentic-ai/runs/d14db29e-3519-4c2e-b87a-d7ed9f9c04eb"
}
```

Return `202` only after the run has been durably recorded and accepted for
processing. Validation failures should use the normal `422` contract; the
service must not return a successful-looking run ID if it could not persist
the request.

### Read a run

`GET /api/v1/agentic-ai/runs/{run_id}`

The response should include the run ID, current status, creation/update
timestamps, and a status-appropriate result or safe error. Proposed statuses:

```text
queued -> running -> completed
                  -> failed
                  -> waiting_for_approval -> running
                  -> cancelled
```

Only completed runs expose their result. Errors must be safe for clients and
must not expose prompts, credentials, internal tool output, or stack traces.
Clients should be able to distinguish a not-found run from a failed run.

## Decisions required before implementation

- Authentication, tenant/user ownership, and authorization for run reads.
- Maximum input size, accepted attachments, retention, and data handling.
- Whether submission supports an `Idempotency-Key` and its replay semantics.
- Durable queue/store choice and the exact meaning of `202 Accepted`.
- Final status set, approval/cancellation behavior, and retry semantics.
- Result schema, public error codes, rate limits, budgets, and timeout policy.
- Whether clients poll only or also receive server-sent events/webhooks.

When approved, implement the behavior and Pydantic schemas under
`app/backend/src/backend/features/agentic_ai/`, register routes through
`backend/api/router.py`, add contract/service tests, then regenerate and review
`docs/api/openapi.json`. Until durable storage and a worker exist, keep these
routes out of the application and do not advertise a queued-run capability.
