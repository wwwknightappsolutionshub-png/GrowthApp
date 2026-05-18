#!/bin/bash
set -euo pipefail

# CustomerFlow AI — VPS Deploy Script
# Usage: ./deploy.sh [--migrate]

COMPOSE_FILE="$(dirname "$0")/../docker-compose.yml"

echo "==> Pulling latest images..."
docker compose -f "$COMPOSE_FILE" pull

echo "==> Recreating containers..."
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

if [[ "${1:-}" == "--migrate" ]]; then
  echo "==> Running database migrations..."
  docker compose -f "$COMPOSE_FILE" exec api alembic upgrade head
fi

echo "==> Checking health..."
sleep 10
docker compose -f "$COMPOSE_FILE" ps

echo "==> Deploy complete."
