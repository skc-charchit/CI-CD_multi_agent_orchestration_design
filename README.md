# Charchit — Selected Projects

The main app is a standalone React + TypeScript + Vite portfolio. It lists
public GitHub repositories and links visitors to a project's live site or
source repository. It reads public repository data directly from GitHub and
does not require the FastAPI backend.

Optional frontend features and the backend are maintained separately. They
can be developed, tested, and built independently, then integrated into the
main app deliberately when their interfaces and behavior are ready.

## Repository map

```text
.
├── app/
│   ├── frontend/                         # Standalone portfolio website
│   │   ├── src/                          # Frontend source files
│   │   ├── index.html                    # HTML document entry point
│   │   ├── package.json                  # Frontend dependencies and commands
│   │   ├── package-lock.json             # Exact frontend dependency versions
│   │   ├── tsconfig*.json                # TypeScript compiler configuration
│   │   └── vite.config.ts                # Vite frontend build/dev configuration
│   ├── features/
│   │   └── project-guide/                # Independent chatbot feature package
│   │       ├── src/                      # Chat UI, README client and guide logic
│   │       ├── scripts/                  # Feature package build helpers
│   │       ├── package.json              # Feature dependencies and build command
│   │       ├── package-lock.json         # Exact feature dependency versions
│   │       ├── tsconfig.json             # Feature TypeScript configuration
│   │       └── README.md                 # Feature usage and integration notes
│   └── backend/
│       ├── src/backend/                  # FastAPI Python package
│       │   ├── api/                      # Shared API routing/composition
│       │   ├── core/                     # Application-wide infrastructure
│       │   ├── db/                       # Future persistence infrastructure
│       │   ├── features/                 # Backend feature vertical slices
│       │   ├── models/                   # Future domain/persistence models
│       │   └── main.py                   # FastAPI app composition root
│       └── tests/                        # Backend test suite
├── docs/
│   ├── api/                              # API contract docs and OpenAPI snapshot
│   └── architecture.md                   # Architecture and feature workflow
├── .github/workflows/                    # GitHub Actions automation
├── k8s/base/                             # Backend Kubernetes starter manifests
├── scripts/                              # Repository-level developer utilities
├── .docker/                              # Currently empty; unused
├── Dockerfile                            # Backend container build
├── main.py                               # Optional backend launch wrapper
├── pyproject.toml                        # Python metadata, dependencies, tools
├── uv.lock                               # Locked Python dependency versions
├── .python-version                       # Preferred local Python version
├── .env.example                          # Example local backend configuration
├── .dockerignore                         # Files omitted from Docker build context
├── .gitignore                            # Generated/local files excluded from Git
└── LICENSE                               # Project license
```

## Folder-by-folder guide

### `app/frontend/` — main portfolio application

This is the visitor-facing website and the only frontend currently intended
for standalone hosting.

- **`src/`** contains the React and TypeScript implementation:
  - `App.tsx` renders the portfolio, repository cards, search, language
    filters, loading/error states, and footer.
  - `api.ts` fetches and validates public repository data from the GitHub
    REST API. It defaults to `skc-charchit` and omits forks and archived
    repositories.
  - `main.tsx` mounts the React app in the HTML root element.
  - `styles.css` contains the portfolio-only responsive visual styles.
  - `vite-env.d.ts` declares Vite's client-side TypeScript environment types.
- **`index.html`** supplies the document title, metadata, root element, and
  frontend entry script.
- **`package.json`** lists React/Vite/TypeScript dependencies and commands
  such as `dev` and `build`.
- **`package-lock.json`** records exact npm dependency versions for repeatable
  `npm ci` installs.
- **`tsconfig.json`** configures application TypeScript checks;
  **`tsconfig.node.json`** configures checks for Vite's Node-side config.
- **`vite.config.ts`** configures Vite. The portfolio currently calls the
  public GitHub API directly; it does not proxy requests through FastAPI.

The portfolio does not import the Project guide package. This boundary keeps
its build and future static hosting independent from optional features and the
backend.

### `app/features/` — independently developed frontend features

Each child is a feature package with an explicit public interface. A feature
under this directory is **not automatically part of the main app**; integration
requires adding it to the frontend intentionally.

#### `app/features/project-guide/`

This package contains the standalone README-based chatbot feature:

- **`src/ProjectChat.tsx`** is the exported React chat UI. It accepts project
  summary data as a prop and does not fetch the portfolio's repository list.
- **`src/github-readme.ts`** defines the `ProjectSummary` input contract and
  retrieves public README files from GitHub.
- **`src/project-guide.ts`** extracts README sections, ranks them against a
  question, and returns source-grounded excerpts. This is deterministic
  matching, not an LLM or Agentic AI call.
- **`src/styles.css`** styles the feature UI without putting those styles into
  the portfolio stylesheet.
- **`src/assets.d.ts`** declares CSS module imports for TypeScript.
- **`scripts/copy-assets.mjs`** copies the feature stylesheet into the
  generated package output.
- **`package.json`** describes the feature package, React peer dependency,
  build command, and package exports.
- **`package-lock.json`** locks the feature's npm dependencies.
- **`tsconfig.json`** controls type checking and compiled feature output.
- **`README.md`** records the input contract, current limitations, build
  instructions, and future integration guidance.

This feature is currently not rendered in the portfolio. No GitHub token,
model-provider secret, backend service, or database is required for its
current README-only behavior. The package README explains how it may later be
integrated with the Agentic AI backend.

### `app/backend/` — separate FastAPI foundation

The backend can run and be tested independently. The portfolio does not
currently call it.

#### `app/backend/src/backend/`

This is the Python application package in the standard `src` layout.

- **`main.py`** creates the FastAPI application, configures CORS, and includes
  the composed API router.
- **`api/`** owns shared HTTP routing:
  - `router.py` defines the `/api/v1` prefix and registers shared and
    feature-owned routers.
  - `routes/health.py` provides the process health endpoint.
- **`core/`** contains application-wide concerns. `config.py` loads settings
  such as the app name, debug mode, and CORS origins from environment
  variables/`.env`.
- **`features/`** holds backend business capabilities:
  - **`echo/`** is a small working vertical slice. `api/routes.py` handles the
    HTTP boundary, `schemas.py` validates request/response data, and
    `service.py` implements the example use case.
  - **`agentic_ai/`** is reserved for agentic workflow code. Its README
    describes the intended module layout and links to the API proposal. No
    agent endpoint, worker, queue, model provider, or durable run store is
    implemented yet.
- **`db/`** is currently a placeholder for database sessions and repository
  implementations; the current app does not persist data.
- **`models/`** is currently a placeholder for internal domain or persistence
  models. API contracts are currently defined with Pydantic schemas inside
  their features instead.
- **`__init__.py` files** mark Python package directories for imports.

#### `app/backend/tests/`

`test_health.py` checks the root overview and health endpoint.
`test_examples.py` verifies echo input validation, the response contract, and
the configured frontend CORS preflight. Keep API tests and service tests here
as backend capabilities are implemented.

### `docs/` — maintained project documentation

- **`architecture.md`** explains application boundaries, the backend layers,
  and the process for adding features.
- **`api/README.md`** explains the current HTTP contracts, how to update the
  API snapshot, and compatibility expectations.
- **`api/openapi.json`** is the reviewed snapshot generated from the live
  FastAPI routes and Pydantic schemas.
- **`api/agentic-ai-draft.md`** is a proposed asynchronous run contract, not
  an implemented endpoint or an execution guarantee.

### `.github/workflows/` — CI/CD automation

- `ci.yml` runs on pull requests to `main` and pushes to `main`. Independent
  jobs install locked dependencies, test and lint the backend, check the
  OpenAPI snapshot, build the frontend and Project guide, build the Python
  package, and verify that the backend Docker image builds.
- `cd.yml` runs only after successful CI on `main`. It deploys the portfolio
  to GitHub Pages, publishes the backend image to GHCR, and deploys that
  immutable image digest to Kubernetes.

To enable deployment:

1. In repository **Settings → Pages**, set the source to **GitHub Actions**.
2. Create a GitHub Actions environment named `production`. Add the environment
   secrets `KUBE_CONFIG` (the deployment cluster's kubeconfig),
   `GHCR_PULL_USERNAME`, and `GHCR_PULL_TOKEN` (a read-only GHCR package token
   for the cluster to pull the private image). Restrict the environment to
   `main` and configure required reviewers if production approval is wanted.
3. Optionally add the environment variable `K8S_NAMESPACE`; it defaults to
   `default`. Create that namespace before the first deploy. The kubeconfig
   identity must be allowed to create/update the deployment, service, config
   map, and `ghcr-pull-secret` in that namespace.
4. Ensure the GHCR package `backend-app` is associated with this repository.
   The workflow refreshes the Kubernetes `ghcr-pull-secret` on each deploy.

The deploy workflow checks out the exact commit that passed CI and waits for
the Kubernetes rollout. Deployments are serialized so an older run cannot
cancel a newer production rollout.

### `k8s/base/` — backend Kubernetes starting point

- `deployment.yaml` defines backend replicas, health probes, and resource
  requests/limits.
- `service.yaml` exposes the backend inside a Kubernetes cluster.
- `configmap.yaml` supplies non-secret settings. Production secrets should
  come from a Kubernetes Secret or external secret manager.

The CD workflow applies these resources and updates the deployment to the
published image digest. The static portfolio is deployed separately to
GitHub Pages.

### `scripts/` — repository utilities

- `run_local.sh` starts the FastAPI backend with Uvicorn and reload enabled.
- `export_openapi.py` writes the generated OpenAPI document to
  `docs/api/openapi.json`; `--check` fails if the snapshot is stale.

### `.docker/`

This directory currently has no files and is not used by the Docker build.
Docker's actual build instructions are in the root `Dockerfile`; excluded
build-context paths are listed in `.dockerignore`.

## Run the main app locally

From the repository root, install frontend dependencies once after cloning:

```bash
npm --prefix app/frontend ci
```

Start the portfolio whenever you want to run it:

```bash
npm --prefix app/frontend run dev
```

Open the Vite URL (normally `http://localhost:5173`) and stop the server with
`Ctrl+C`. An internet connection is needed to fetch public repositories.
New public repositories appear when a visitor opens or refreshes the page.

The portfolio defaults to the `skc-charchit` GitHub account. Set
`VITE_GITHUB_USERNAME` in the frontend environment before starting Vite to use
a different public profile. Forked and archived repositories are omitted.
Project cards link to the GitHub homepage when configured, or to the
repository otherwise.

## Build the Project guide feature separately

It is not needed to run the main app:

```bash
npm --prefix app/features/project-guide ci
npm --prefix app/features/project-guide run build
```

## GitHub Pages deployment

The CI/CD workflow publishes the standalone portfolio to GitHub Pages after
successful CI on `main`. Enable **Settings → Pages → GitHub Actions** and
merge to `main` to deploy it. To build the static site locally:

```bash
npm --prefix app/frontend ci
npm --prefix app/frontend run build
```

The generated files are in `app/frontend/dist/`. The backend is deployed
independently to Kubernetes; the portfolio currently does not call it.

## Run the backend separately

The backend is a development foundation and is not connected to the portfolio:

```bash
uv sync --dev
uv run uvicorn backend.main:app --reload --app-dir app/backend/src
```

Its current routes are `GET /`, `GET /api/v1/health`, and
`POST /api/v1/examples/echo`. The echo endpoint is an example, not an AI
workflow. See the API docs at `http://localhost:8000/docs` after starting it.

## Root configuration and project files

- **`pyproject.toml`** declares Python runtime requirements, backend
  dependencies, package build configuration, pytest paths, and Ruff rules.
- **`uv.lock`** locks Python dependencies for reproducible `uv sync` installs.
- **`.python-version`** records the preferred Python version for compatible
  version managers.
- **`.env.example`** shows local backend settings. Copy it to `.env` for local
  configuration; never commit real secrets.
- **`Dockerfile`** builds the backend container. It is not required for the
  static frontend or GoDaddy hosting.
- **`main.py`** is a convenience backend launcher; Uvicorn's documented
  command is the usual development entry point.
- **`.dockerignore`** excludes local dependencies, secrets, caches, and build
  output from Docker context.
- **`.gitignore`** excludes local environments, caches, and generated assets.
- **`LICENSE`** contains the project's license terms.
- **`kubectl`** is a bundled Linux x86-64 Kubernetes CLI binary. The source
  code and local frontend do not depend on it; Kubernetes users may use their
  own compatible `kubectl` installation.

Directories such as `.venv/`, `node_modules/`, `dist/`, and cache folders are
generated/local artifacts, not source folders. They should not be committed.

## Quality checks

```bash
uv run pytest -q
uv run ruff check app/backend/src app/backend/tests scripts
uv run ruff format --check app/backend/src app/backend/tests scripts
uv run python scripts/export_openapi.py --check
npm --prefix app/frontend ci
npm --prefix app/frontend run build
npm --prefix app/features/project-guide ci
npm --prefix app/features/project-guide run build
```

GitHub Actions runs these checks and package builds. See the workflow setup
above to enable publishing and deployment.
