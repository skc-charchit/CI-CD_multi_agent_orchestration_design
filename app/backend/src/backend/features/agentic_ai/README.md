# Agentic chatbot feature

Build the chatbot as a backend feature in this directory:

`app/backend/src/backend/features/agentic_ai/`

Do not put LangGraph workflow code in `backend/core/`, shared API routes, the
portfolio frontend, or the separate `app/features/project-guide/` package.
Those are different boundaries: `core/` is for cross-feature infrastructure,
the portfolio is a static app, and Project guide is a separate README-based
frontend feature that is not currently integrated.

The Python project already declares LangGraph in the root `pyproject.toml`.
Add a direct dependency for any other library that this feature imports
(including LangSmith if the code imports its SDK directly), update `uv.lock`
with `uv lock`, and avoid installing AI packages in the frontend.

## Recommended structure

Start with a small vertical slice and add files as real needs arise. A
reasonable target layout is:

```text
app/backend/src/backend/features/agentic_ai/
├── __init__.py
├── api/
│   ├── __init__.py
│   └── routes.py            # FastAPI endpoints; HTTP mapping only
├── schemas.py              # Public request/response Pydantic models
├── service.py              # Use cases called by routes
├── graph/
│   ├── __init__.py
│   ├── state.py            # Typed LangGraph state
│   ├── nodes.py            # Node functions
│   ├── build.py            # Graph construction and compile
│   └── prompts.py           # Feature-owned prompt templates
├── tools/
│   ├── __init__.py
│   └── ...                 # Explicitly permitted tool implementations
├── config.py               # Agent/model-specific settings, if needed
├── repository.py           # Persistence interface, when needed
└── models.py               # Feature domain types, when needed

app/backend/tests/
└── features/
    └── agentic_ai/
        ├── test_graph.py
        ├── test_service.py
        └── test_api.py
```

Do not create empty modules just to match the diagram. For an initial
non-persistent request/response prototype, `api/`, `schemas.py`, `service.py`,
and a compact `graph/` may be enough. Add `tools/` when the graph uses tools;
add persistence abstractions and storage only when requirements call for
saved conversations, resumable runs, or durable history.

### What belongs in each layer

- **`api/routes.py`** validates the HTTP contract, enforces request-level
  authentication/authorization dependencies, calls the feature service, and
  maps results to HTTP responses. Keep prompts, graph nodes, provider calls,
  and storage queries out of routes.
- **`schemas.py`** defines only public API input/output. Do not expose internal
  graph state, chain-of-thought, credentials, raw provider responses, or
  unfiltered tool output.
- **`service.py`** is the use-case boundary. It prepares validated input,
  invokes the graph, applies feature policy, and returns a domain result.
- **`graph/state.py`** declares the minimum typed state needed to move data
  between nodes. Keep it serializable if checkpointing may be required; do not
  put secrets or unbounded conversation history in state.
- **`graph/nodes.py`** contains small workflow steps, such as classifying the
  request, retrieving approved project context, drafting an answer, and
  checking the result. Each node should have a clear input/output and bounded
  work.
- **`graph/build.py`** wires nodes, transitions, conditional edges, and any
  checkpoint configuration, then compiles the graph. Do not compile a new
  graph for every request unless runtime configuration requires it.
- **`graph/prompts.py`** owns feature-specific prompt text. Prompts are not a
  security boundary; tools still require server-side validation and
  authorization.
- **`tools/`** holds narrowly scoped functions the model may request. Validate
  every argument and authorize every operation independently of the model.
  Start with read-only tools and least privilege.
- **`config.py`** holds feature-specific settings. Put only genuinely
  application-wide settings in `backend/core/config.py`. Read API keys from
  environment/secret management; never commit them or return them to clients.
- **`repository.py` / `models.py`** are optional boundaries for durable
  records and domain entities. Do not pretend in-memory state is durable.

Tests belong under `app/backend/tests/`, not inside the runtime feature
package. Keep graph behavior, service policy, and FastAPI contract tests
separate so each layer can be tested without real provider calls.

## LangGraph and LangSmith responsibilities

Use **LangGraph** for explicit workflow state, nodes, edges, retries, and
checkpointing where required. Keep orchestration in this feature; it is not
shared FastAPI infrastructure.

Use **LangSmith** for tracing, evaluation, and debugging of model/graph runs.
It is observability, not the application database, durable job queue, or
authorization system. Configure tracing with deployment environment
variables/secrets (for example `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, and
`LANGSMITH_PROJECT`) and keep tracing disabled or appropriately controlled in
environments where sending prompts or user data to an external service is not
approved. Apply data minimization/redaction and retention settings before
tracing sensitive conversations. Do not log API keys, tokens, or unrestricted
tool outputs.

## Local provider configuration

The model factory uses OpenAI's `gpt-4o` model by default through
`langchain-openai`. Configure `OPENAI_API_KEY` and optionally `OPENAI_MODEL`
in the ignored repository `.envrc` for local development, or inject them
through deployment secrets. Set `OPENAI_BASE_URL` only when using an
OpenAI-compatible provider with a custom endpoint. The backend reads process
environment variables and does not load `.env`. Keep real keys only in
ignored local configuration or a deployment secret store, never in tracked
source or logs.

`PROJECT_NAME` and `PROJECT_NUMBER` are currently exported for local use but
are not consumed by this feature. A valid provider API key is needed when a
request invokes the model; importing the feature and running credential-free
unit tests do not initialize the provider client. A placeholder key will not
authenticate against OpenAI's official API.

## HTTP API

The synchronous endpoint is `POST /api/v1/agentic-ai/chat` with a JSON body
such as `{"message":"What is 19 + 23?"}`. It returns an `answer` string.
Messages are limited to 2,000 characters and require
`Authorization: Bearer <AGENT_API_KEY>` from a trusted server-side client.
Keep this key out of browser code. Each request is a separate turn. Successful
answers are stored in PostgreSQL's `agent_queries` table with the input/output
UTC timestamps and tool calls. Missing provider or database configuration is
reported as a service-unavailable response rather than a fabricated or
unsaved answer.

Use the authenticated `GET /api/v1/agentic-ai/history` endpoint in Swagger
(`http://localhost:8000/docs`) to inspect saved turns. It returns questions,
answers, UTC timestamps, and tool calls/results, newest first. `limit` (1–100,
default 50) and `offset` query parameters paginate the results. Authorize in
Swagger with the same server-side bearer token configured as `AGENT_API_KEY`.

## Run the agent interactively

From the repository root, start the terminal chat with:

```bash
direnv exec . uv run python -m backend.features.agentic_ai
```

Type a question such as `What is 19 + 23?`; the terminal displays the tool
call/result when the model uses an arithmetic tool, followed by the agent's
answer. Each successfully answered turn is saved in PostgreSQL's
`agent_queries` table with UTC input/output timestamps and the tool names,
arguments, and results. Enter `/reset` to clear only the in-memory context or
`/quit` to exit; saved rows are not removed. PostgreSQL settings and
`OPENAI_API_KEY` must be configured before starting. Each prompt is sent to
OpenAI (or the configured compatible endpoint), so provider usage and charges
may apply. This starts the local graph directly and does not start FastAPI.

## Implement in this order

1. **Agree on behavior and data policy.** Specify who can use the chatbot,
   which projects/context it may access, what data is retained, input limits,
   expected latency, provider budget, and whether human approval is needed
   for any action. The model must not decide its own authorization.
2. **Define a small contract.** Add request and response models in
   `schemas.py`. Start with one user message and one bounded answer. Decide
   how errors, conversation IDs, and ownership work before exposing them.
3. **Build a pure, bounded graph.** Add typed state, the minimum useful nodes,
   and graph construction. Begin with no external tools or only safe,
   read-only tools. Make external calls time-bounded and validate their
   results.
4. **Wrap it with a service.** Have `service.py` invoke the compiled graph and
   return a domain result. Keep provider configuration server-side.
5. **Add the HTTP layer.** Implement routes in `api/routes.py` and register
   the feature router in
   `app/backend/src/backend/api/router.py` under `/api/v1`. The router is not
   active merely because the folder exists.
6. **Test without live model credentials.** Unit-test graph transitions and
   service policy with fakes/stubs; test request validation and HTTP responses
   through FastAPI's test client. Add separate opt-in integration/evaluation
   runs for a real provider rather than making ordinary CI depend on API keys.
7. **Add LangSmith deliberately.** Configure tracing through deployment
   secrets/environment, verify that captured data is appropriate, and create
   evaluation cases for answer relevance, groundedness, refusals, and tool
   behavior. Do not make a successful trace equivalent to a successful
   product response.
8. **Update the contract and docs.** Once routes are implemented, regenerate
   `docs/api/openapi.json` with `uv run python scripts/export_openapi.py`,
   review the diff, and add API and feature behavior documentation.
9. **Integrate the UI later.** The portfolio is currently standalone. When
   ready, add a frontend integration that calls the public API contract; do
   not import backend Python or provider credentials into the browser.

## Synchronous prototype versus durable runs

For the first narrow chatbot prototype, a synchronous request/response route
may be appropriate if the graph reliably completes within the API timeout and
the product does not promise durable history or resumability.

The existing proposal in
[`docs/api/agentic-ai-draft.md`](../../../../../../docs/api/agentic-ai-draft.md)
instead describes asynchronous runs. Treat it as a draft, not as the current
implementation. Use `202 Accepted` and a `"queued"` status only after a durable
record has been written and a real worker/queue has accepted responsibility
for processing it. Before adopting that design, decide on storage, queue,
ownership checks, idempotency, retries, cancellation, retention, and failure
semantics. A LangGraph checkpoint alone does not automatically provide a
complete public job API.

## Current status

The feature contains a LangGraph arithmetic workflow, typed state, and
add/multiply/divide tools. The terminal app and authenticated FastAPI chat
route use the same service to persist completed turns in PostgreSQL.
Persistence failures are surfaced rather than returning an unsaved success.
Conversation context in the terminal remains process-local; persisted records
are an audit/history log and are not automatically replayed into later
sessions. LangSmith tracing is not configured.
