#!/bin/sh
# Git-based vault sync — Platinum spec § "For Vault sync (Phase 1) use Git".
#
# Runs as a sidecar container. Every 60 seconds:
#   1. cd /vault
#   2. git pull --rebase (fast-forward the shared state)
#   3. git add . ; git commit if dirty
#   4. git push
#
# Secrets never sync because the shared .gitignore excludes them. Cloud
# writes stay in /In_Progress/cloud-agent/, /Plans/<domain>/,
# /Pending_Approval/<domain>/, and /Updates/ — Local claims /Approved/,
# /Done/, Dashboard.md.
set -eu

: "${VAULT_REPO_URL:?must be set}"
: "${VAULT_BRANCH:=main}"

git config --global user.email "${GIT_USER_EMAIL:-cloud-agent@autosapien.example}"
git config --global user.name  "${GIT_USER_NAME:-autosapien-cloud-agent}"
git config --global safe.directory '*'

cd /vault

# First run: bootstrap the vault from the remote if empty.
if [ ! -d .git ]; then
    echo "[vault-sync] cloning $VAULT_REPO_URL (branch $VAULT_BRANCH)..."
    git init -q
    git remote add origin "$VAULT_REPO_URL"
    git fetch origin --depth=1
    git checkout -t "origin/$VAULT_BRANCH" -b "$VAULT_BRANCH" || git checkout "$VAULT_BRANCH"
fi

while true; do
    # 1. Pull — fast-forward wherever possible, rebase on conflict.
    if ! git pull --rebase origin "$VAULT_BRANCH" >/tmp/pull.log 2>&1; then
        echo "[vault-sync] pull failed; aborting rebase for safety"
        git rebase --abort 2>/dev/null || true
    fi

    # 2. Commit-if-dirty.
    git add -A
    if ! git diff --cached --quiet; then
        ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        git commit -q -m "cloud-agent tick @ $ts" || true

        # 3. Push.
        if ! git push origin "$VAULT_BRANCH" >/tmp/push.log 2>&1; then
            echo "[vault-sync] push failed (probably a race); pulling again next tick"
            cat /tmp/push.log | tail -5
        fi
    fi

    sleep 60
done
