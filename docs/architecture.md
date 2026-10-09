# Application architecture

This repository contains three intentionally separate pieces: a standalone
portfolio frontend, an independently buildable Project guide frontend feature,
and a FastAPI backend foundation. The backend is structured as a modular
monolith with feature modules. Keeping these boundaries explicit makes local
development and deployment straightforward while allowing features to be
integrated deliberately. Split a backend feature into a separately deployed
microservice only when it needs independent scaling, release cadence,
isolation, or ownership.

## Backend layers

```text
HTTP request
  -> backend/api/routes/       shared endpoints (health)
  -> backend/api/router.py     versioned router composition
  -> backend/features/<name>/api/routes.py
  -> backend/features/<name>/schemas.py
  -> backend/features/<name>/service.py
  -> backend/features/<name>/repository.py (when persistence is introduced)
```

- **API routes** translate HTTP inputs to feature use cases and declare
  response models/status codes. They do not contain orchestration or SQL.
- **Schemas** validate untrusted input and define the public API contract.
- **Services** implement feature use cases and coordinate domain work.
- **Repositories** isolate persistence when a database is added.
- **Core** contains shared configuration and infrastructure. Avoid putting
  feature-specific behavior here.
- **API router** composes feature routers and applies the version prefix.
- **Tests** live beside the backend application at `app/backend/tests/` and
  should cover service behavior and public HTTP contracts.

## Adding a feature

1. Create `app/backend/src/backend/features/<feature_name>/`.
2. Keep that feature's `api/routes.py`, `schemas.py`, and `service.py` together.
   Add models/repositories only when the use case needs them.
3. Register its router in `backend/api/router.py`.
4. Add focused service tests and API tests under `app/backend/tests/`.
5. Export and review the OpenAPI snapshot as described in
   [`api/README.md`](./api/README.md).
6. If the feature is intended for the portfolio, define and consume its public
   HTTP contract from the frontend. Do not call internal services directly
   from UI components. The current portfolio is standalone and reads public
   GitHub data directly; it does not currently use the FastAPI backend.

The example feature demonstrates a complete but intentionally small vertical
slice. The Agentic AI folder documents its ownership boundary and contract
planning requirements. The proposed asynchronous contract is in
[`api/agentic-ai-draft.md`](./api/agentic-ai-draft.md); it does not pretend
that a model provider, durable run store, or background worker has already
been implemented.

## Frontend/backend boundary

The portfolio frontend currently calls the public GitHub API directly and
does not proxy `/api` to FastAPI. The separate Project guide package reads
public GitHub README files and is not imported or rendered by the portfolio.
The FastAPI backend exposes its own health and example echo routes, but is not
currently connected to either frontend package. CORS is configured for
deployments where browser and API origins differ. Provider credentials,
orchestration policy, and privileged tools belong only on the server.

## Delivery and deployment

GitHub Actions runs Python tests, Ruff lint/format checks, OpenAPI snapshot
verification, independent production builds for the portfolio and Project
guide, and the Python package build. The root Dockerfile builds the backend;
frontend assets need a static host or a separate frontend container/reverse
proxy in production. Keep CI settings and production secrets in GitHub
Environments or a secret manager, not in source.
