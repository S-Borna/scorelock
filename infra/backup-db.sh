#!/usr/bin/env bash
# ── ScoreLock Database Backup Script ──────────────────────
# Usage:
#   ./infra/backup-db.sh                     # local Docker backup
#   ./infra/backup-db.sh --railway           # Railway production backup
#
# Backups are stored in ./backups/ with timestamps.
# Railway backups also auto-enabled via dashboard (daily).

set -euo pipefail

BACKUP_DIR="$(cd "$(dirname "$0")/.." && pwd)/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="scorelock_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

if [[ "${1:-}" == "--railway" ]]; then
    # ── Railway production backup ──────────────────────────
    if [[ -z "${DATABASE_URL:-}" ]]; then
        echo "❌ DATABASE_URL not set. Export it from Railway dashboard."
        echo "   export DATABASE_URL='postgresql://...'"
        exit 1
    fi

    echo "📦 Backing up Railway production database..."
    pg_dump "$DATABASE_URL" \
        --no-owner \
        --no-privileges \
        --format=custom \
        --compress=9 \
        -f "$BACKUP_DIR/$FILENAME"

    echo "✅ Production backup saved: $BACKUP_DIR/$FILENAME"

else
    # ── Local Docker backup ────────────────────────────────
    CONTAINER="scorelock-db"
    DB_USER="${POSTGRES_USER:-scorelock}"
    DB_NAME="${POSTGRES_DB:-scorelock}"

    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        echo "❌ Container '$CONTAINER' is not running."
        echo "   Start it with: docker compose up -d db"
        exit 1
    fi

    echo "📦 Backing up local database ($CONTAINER)..."
    docker exec "$CONTAINER" pg_dump \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-privileges \
        --format=custom \
        --compress=9 \
        | cat > "$BACKUP_DIR/$FILENAME"

    echo "✅ Local backup saved: $BACKUP_DIR/$FILENAME"
fi

# ── Cleanup: keep only last 10 backups ─────────────────────
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/scorelock_*.sql.gz 2>/dev/null | wc -l)
if [[ "$BACKUP_COUNT" -gt 10 ]]; then
    echo "🧹 Cleaning old backups (keeping last 10)..."
    ls -1t "$BACKUP_DIR"/scorelock_*.sql.gz | tail -n +11 | xargs rm -f
fi

echo "📊 Backups in $BACKUP_DIR:"
ls -lh "$BACKUP_DIR"/scorelock_*.sql.gz 2>/dev/null || echo "   (none)"
