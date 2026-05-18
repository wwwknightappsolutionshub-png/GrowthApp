#!/usr/bin/env bash
# CustomerFlow AI — PostgreSQL backup script
# Runs inside the backup container (or standalone on VPS)
# Supports: local rotation, optional S3 upload, Slack/webhook alert on failure
set -euo pipefail

# ── Config from env ────────────────────────────────────────────────────────
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-customerflow_ai}"
POSTGRES_USER="${POSTGRES_USER:-customerflow}"
PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}"
export PGPASSWORD

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETAIN_DAILY="${RETAIN_DAILY:-7}"
RETAIN_WEEKLY="${RETAIN_WEEKLY:-4}"
RETAIN_MONTHLY="${RETAIN_MONTHLY:-3}"

S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-customerflow/postgres}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-eu-west-2}"

ALERT_WEBHOOK="${BACKUP_ALERT_WEBHOOK:-}"

# ── Helpers ────────────────────────────────────────────────────────────────
log()  { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"; }
fail() { log "ERROR: $*"; send_alert "FAILED: $*"; exit 1; }

send_alert() {
  local msg="$1"
  if [[ -n "$ALERT_WEBHOOK" ]]; then
    curl -s -X POST "$ALERT_WEBHOOK" \
      -H 'Content-Type: application/json' \
      -d "{\"text\":\"🔴 CustomerFlow AI DB Backup ${msg}\"}" || true
  fi
}

# ── Pre-flight ─────────────────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly" "$BACKUP_DIR/monthly"

# Wait for postgres to be ready
for i in $(seq 1 30); do
  pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    && break || { log "Waiting for postgres ($i/30)..."; sleep 2; }
done
pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  || fail "PostgreSQL is not reachable at $POSTGRES_HOST:$POSTGRES_PORT"

# ── Dump ──────────────────────────────────────────────────────────────────
TIMESTAMP=$(date -u '+%Y%m%dT%H%M%SZ')
DAY=$(date -u '+%d')
DOW=$(date -u '+%u')   # 1=Mon … 7=Sun
FILENAME="${POSTGRES_DB}_${TIMESTAMP}.sql.gz"
DAILY_PATH="$BACKUP_DIR/daily/$FILENAME"

log "Starting pg_dump → $DAILY_PATH"
pg_dump \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --no-password \
  --format=plain \
  --clean \
  --if-exists \
  | gzip -9 > "$DAILY_PATH" \
  || fail "pg_dump failed"

FILESIZE=$(du -sh "$DAILY_PATH" | cut -f1)
log "Dump complete: $DAILY_PATH ($FILESIZE)"

# ── Weekly copy (every Sunday) ─────────────────────────────────────────────
if [[ "$DOW" == "7" ]]; then
  cp "$DAILY_PATH" "$BACKUP_DIR/weekly/$FILENAME"
  log "Weekly backup saved: $BACKUP_DIR/weekly/$FILENAME"
fi

# ── Monthly copy (1st of month) ────────────────────────────────────────────
if [[ "$DAY" == "01" ]]; then
  cp "$DAILY_PATH" "$BACKUP_DIR/monthly/$FILENAME"
  log "Monthly backup saved: $BACKUP_DIR/monthly/$FILENAME"
fi

# ── Rotate old backups ────────────────────────────────────────────────────
log "Rotating: keeping $RETAIN_DAILY daily, $RETAIN_WEEKLY weekly, $RETAIN_MONTHLY monthly"
(cd "$BACKUP_DIR/daily"   && ls -1t *.sql.gz 2>/dev/null | tail -n +$((RETAIN_DAILY   + 1)) | xargs -r rm -v)
(cd "$BACKUP_DIR/weekly"  && ls -1t *.sql.gz 2>/dev/null | tail -n +$((RETAIN_WEEKLY  + 1)) | xargs -r rm -v)
(cd "$BACKUP_DIR/monthly" && ls -1t *.sql.gz 2>/dev/null | tail -n +$((RETAIN_MONTHLY + 1)) | xargs -r rm -v)

# ── Optional S3 upload ────────────────────────────────────────────────────
if [[ -n "$S3_BUCKET" && -n "$AWS_ACCESS_KEY_ID" ]]; then
  log "Uploading to s3://$S3_BUCKET/$S3_PREFIX/daily/$FILENAME"
  export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION
  aws s3 cp "$DAILY_PATH" "s3://$S3_BUCKET/$S3_PREFIX/daily/$FILENAME" \
    --storage-class STANDARD_IA \
    || fail "S3 upload failed"
  log "S3 upload complete"

  if [[ "$DOW" == "7" ]]; then
    aws s3 cp "$DAILY_PATH" "s3://$S3_BUCKET/$S3_PREFIX/weekly/$FILENAME" \
      --storage-class STANDARD_IA || true
  fi
  if [[ "$DAY" == "01" ]]; then
    aws s3 cp "$DAILY_PATH" "s3://$S3_BUCKET/$S3_PREFIX/monthly/$FILENAME" \
      --storage-class STANDARD_IA || true
  fi

  # Apply S3 lifecycle rotation via tag (relies on S3 lifecycle policy being set)
  # See infra/backup/s3-lifecycle.json for the recommended policy
fi

log "Backup finished successfully ✅"
send_alert "SUCCESS — $FILENAME ($FILESIZE)" 2>/dev/null || true
