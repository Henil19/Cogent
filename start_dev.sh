#!/usr/bin/env bash
set -e

echo "======================================================="
echo "Starting Cogent Research Platform (Development Mode)"
echo "======================================================="

# Trap cleanup
trap 'kill $(jobs -p) 2>/dev/null' EXIT

echo "Starting FastAPI Backend on http://localhost:8000 ..."
(cd backend && source .venv/bin/activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload) &

echo "Starting React Frontend on http://localhost:5173 ..."
(cd frontend && npm run dev) &

echo "======================================================="
echo "Cogent is launching:"
echo "  - Research Cockpit: http://localhost:5173"
echo "  - Interactive Swagger API: http://localhost:8000/docs"
echo "======================================================="

wait
