#!/bin/bash
set -e

: "${BACKEND_HOST:=127.0.0.1}"
: "${BACKEND_PORT:=8000}"
: "${FRONTEND_PORT:=3000}"
: "${HOSTNAME:=0.0.0.0}"

cd /app/backend
uvicorn main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" &
BACKEND_PID=$!

cd /app/frontend
PORT="$FRONTEND_PORT" HOSTNAME="$HOSTNAME" node server.js &
FRONTEND_PID=$!

term() {
  kill -TERM "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap term INT TERM

wait -n
exit_code=$?
term
wait
exit $exit_code
