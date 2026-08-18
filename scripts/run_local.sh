#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

uv run uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000
