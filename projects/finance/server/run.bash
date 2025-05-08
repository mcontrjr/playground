#!/usr/bin/env bash
set -e

docker compose -f ../docker-compose.dev.yml up -d db
echo "Waiting for database to be ready..."
sleep 5

uvicorn main:app --host 0.0.0.0 --port "${SERVER_PORT:-8000}" --reload