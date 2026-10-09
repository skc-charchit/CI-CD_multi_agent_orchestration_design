#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

uv run uvicorn backend.main:app --reload --app-dir app/backend/src --host 0.0.0.0 --port 8000
