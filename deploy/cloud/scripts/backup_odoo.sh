#!/bin/sh
# Nightly Odoo backup: pg_dump + 7-day local retention + optional B2 upload.
# Runs inside the postgres container so pg_dump matches the server version.
# Invoked by systemd timer (autosapien-backup.timer) on the host, or by the
# `backup` compose service directly.
set -eu

TARGET_DIR="/var/backups/odoo"
mkdir -p "$TARGET_DIR"

STAMP=$(date -u +%Y-%m-%dT%H-%M-%SZ)
OUT="$TARGET_DIR/autosapien-$STAMP.sql.gz"

echo "[backup] dumping $PGDATABASE -> $OUT"
pg_dump --no-owner --no-privileges "$PGDATABASE" | gzip -9 >"$OUT"
SIZE_MB=$(du -m "$OUT" | awk '{print $1}')
echo "[backup] ok  size=${SIZE_MB} MB"

# Keep the last 7 days locally.
find "$TARGET_DIR" -type f -name "autosapien-*.sql.gz" -mtime +7 -delete

# Optional Backblaze B2 upload if credentials are in env.
if [ -n "${B2_APPLICATION_KEY_ID:-}" ] && [ -n "${B2_APPLICATION_KEY:-}" ] && [ -n "${B2_BUCKET:-}" ]; then
    if ! command -v b2 >/dev/null 2>&1; then
        # Alpine-friendly install via pip; the postgres image has python but not pip.
        # Skip upload if b2 CLI isn't installed — local copy is kept either way.
        echo "[backup] b2 CLI not installed; skipping off-site upload"
    else
        b2 authorize-account "$B2_APPLICATION_KEY_ID" "$B2_APPLICATION_KEY" >/dev/null
        b2 upload-file "$B2_BUCKET" "$OUT" "odoo/$(basename "$OUT")"
        echo "[backup] uploaded to b2://$B2_BUCKET/odoo/$(basename "$OUT")"
    fi
fi

# Drop a vault-visible breadcrumb so the CEO Briefing can note backup age.
if [ -d "/vault/Logs" ]; then
    echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"actor\":\"backup\",\"action_type\":\"odoo_backup\",\"result\":\"success\",\"parameters\":{\"size_mb\":$SIZE_MB}}" \
      >> "/vault/Logs/$(date -u +%Y-%m-%d).jsonl"
fi
