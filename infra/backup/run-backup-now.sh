#!/usr/bin/env bash
# Trigger an immediate backup from the host VPS (outside Docker)
# Usage: ./run-backup-now.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "🗄️  Triggering immediate database backup..."
docker compose exec backup /usr/local/bin/backup.sh
echo "✅ Done. Check logs above for details."
