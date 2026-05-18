#!/usr/bin/env bash
# CustomerFlow AI — PostgreSQL restore script
# Usage: ./restore.sh /backups/daily/customerflow_ai_20240101T120000Z.sql.gz
#    or: ./restore.sh s3://my-bucket/customerflow/postgres/daily/customerflow_ai_20240101T120000Z.sql.gz
set -euo pipefail

BACKUP_FILE="${1:?Usage: $0 <backup-file-path|s3-uri>}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-customerflow_ai}"
POSTGRES_USER="${POSTGRES_USER:-customerflow}"
PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}"
export PGPASSWORD

log()  { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"; }

# Download from S3 if needed
LOCAL_FILE="$BACKUP_FILE"
if [[ "$BACKUP_FILE" == s3://* ]]; then
  LOCAL_FILE="/tmp/restore_$(basename "$BACKUP_FILE")"
  log "Downloading from S3: $BACKUP_FILE → $LOCAL_FILE"
  aws s3 cp "$BACKUP_FILE" "$LOCAL_FILE"
fi

[[ -f "$LOCAL_FILE" ]] || { log "ERROR: File not found: $LOCAL_FILE"; exit 1; }

# Safety prompt
echo ""
echo "⚠️  WARNING: This will DROP and recreate the '$POSTGRES_DB' database."
echo "   Source: $LOCAL_FILE"
echo "   Target: $POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
echo ""
read -r -p "Type 'yes' to continue: " CONFIRM
[[ "$CONFIRM" == "yes" ]] || { log "Aborted."; exit 0; }

log "Restoring from $LOCAL_FILE..."
gunzip -c "$LOCAL_FILE" | psql \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --no-password \
  || { log "ERROR: Restore failed."; exit 1; }

log "Restore complete ✅"
