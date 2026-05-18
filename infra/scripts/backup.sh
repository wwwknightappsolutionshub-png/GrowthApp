#!/bin/bash
set -euo pipefail

# CustomerFlow AI — Nightly Backup Script
# Add to crontab: 0 2 * * * /path/to/backup.sh >> /var/log/customerflow-backup.log 2>&1

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/tmp/customerflow_backups"
BACKUP_FILE="${BACKUP_DIR}/customerflow_${TIMESTAMP}.sql.gz"

source "$(dirname "$0")/../../.env" 2>/dev/null || true

mkdir -p "$BACKUP_DIR"

echo "[${TIMESTAMP}] Starting backup..."

# Dump PostgreSQL
docker compose -f "$(dirname "$0")/../docker-compose.yml" exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-customerflow}" "${POSTGRES_DB:-customerflow_ai}" | \
  gzip > "$BACKUP_FILE"

echo "[${TIMESTAMP}] Backup created: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

# Upload to Backblaze B2 (requires rclone configured)
if command -v rclone &>/dev/null && [[ -n "${B2_BUCKET_NAME:-}" ]]; then
  rclone copy "$BACKUP_FILE" "b2:${B2_BUCKET_NAME}/postgres/"
  echo "[${TIMESTAMP}] Uploaded to B2: ${B2_BUCKET_NAME}/postgres/"
fi

# Keep only last 7 local backups
find "$BACKUP_DIR" -name "customerflow_*.sql.gz" -mtime +7 -delete
echo "[${TIMESTAMP}] Cleanup done."
