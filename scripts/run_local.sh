#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

uvicorn_args=(
    uv run uvicorn backend.main:app
    --reload
    --app-dir app/backend/src
    --host 0.0.0.0
    --port 8000
)

if command -v direnv >/dev/null 2>&1 && [[ -f .envrc ]]; then
    exec direnv exec . "${uvicorn_args[@]}"
fi

exec "${uvicorn_args[@]}"
