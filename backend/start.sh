#!/bin/bash
# DO NOT use set -e — we want full diagnostic output even on errors

echo "========================================="
echo "  ScoreLock API Startup"
echo "========================================="
echo "PORT      = ${PORT:-8000}"
echo "ENVIRONMENT = ${ENVIRONMENT:-not set}"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo YES || echo NO)"
echo "REDIS_URL set:    $([ -n "$REDIS_URL" ] && echo YES || echo NO)"
echo "Python: $(python --version 2>&1)"
echo "PWD:    $(pwd)"
echo "========================================="

# ── 1. Alembic Migrations ─────────────────────────────────
echo "[1/3] Running Alembic migrations..."
if timeout 15 alembic -c /app/alembic.ini upgrade head 2>&1; then
    echo "[1/3] Alembic migrations OK"
else
    echo "[1/3] WARNING: Alembic migrations failed/timed-out (exit $?) — continuing anyway"
fi

# ── 2. Quick import smoke test ─────────────────────────────
echo "[2/3] Testing Python imports..."
python -u -c "
import sys, traceback
try:
    from app.main import app
    print('[2/3] Import OK — app object:', type(app))
except Exception:
    traceback.print_exc()
    print('[2/3] CRITICAL: Import failed — uvicorn will also fail')
    sys.exit(1)
" 2>&1

IMPORT_EXIT=$?
if [ $IMPORT_EXIT -ne 0 ]; then
    echo "FATAL: Python import failed. Sleeping 30s so you can read the logs..."
    sleep 30
    exit 1
fi

# ── 3. Start Uvicorn ───────────────────────────────────────
UVICORN_PORT="${PORT:-8000}"
echo "[3/3] Starting Uvicorn on port ${UVICORN_PORT}..."
echo "========================================="

# exec replaces the shell — PID 1 becomes uvicorn (proper signal handling)
# -u = unbuffered stdout so Railway captures all output
exec python -u -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${UVICORN_PORT}" \
    --log-level info \
    --access-log 2>&1
