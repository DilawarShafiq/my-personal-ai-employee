# Platinum tier — Always-On Cloud deployment

Everything in this folder is the pure-Platinum cloud deployment of the
autosapien AI Employee. Works on **Oracle Cloud Free Tier** (4 OCPU /
24 GB Ampere ARM VM — free forever) or any Ubuntu 22.04+ box.

## What the cloud deployment runs

| Service | Purpose | Port |
|---|---|---|
| `autosapien-cloud` | Cloud-side orchestrator (email triage + drafts only) | — |
| `odoo` | Odoo 19 Community (healthcare accounting) | 8069 (internal) |
| `db` | Postgres 16 | 5432 (internal) |
| `caddy` | HTTPS reverse proxy + automatic Let's Encrypt | 80, 443 |
| `backup` | Nightly `pg_dump` to `/var/backups/odoo/` | — |
| `healthcheck` | `/healthz` endpoint for uptime monitoring | 8080 (behind Caddy) |

## Role separation (spec § Platinum > Work-Zone Specialization)

**Cloud owns**:
- Email triage (Gmail watcher)
- Draft replies → `/Plans/email/`, `/Pending_Approval/email/`
- Social post **drafts** → `/Pending_Approval/social/`
- Odoo **draft-only** accounting actions

**Cloud is forbidden from**:
- WhatsApp sessions (stay on Local)
- Banking / payment credentials
- Final `send_email` / `post_linkedin` / `post_invoice` actions
- Writing to `Dashboard.md` (single-writer rule — Local-only)

These rules are enforced **in code** in `scripts/cloud_agent.py` via a
fail-closed `_enforce_role_separation()` check at boot.

## Deploy in 15 minutes (Oracle Free Tier)

On a fresh Oracle Cloud Free Tier Ubuntu 22.04 VM:

```bash
# 1. SSH in as ubuntu user
ssh ubuntu@your-vm-ip

# 2. Clone and run the bootstrap
git clone https://github.com/DilawarShafiq/my-personal-ai-employee.git autosapien
cd autosapien
sudo bash deploy/cloud/bootstrap_oracle_free.sh yourdomain.example
```

`yourdomain.example` must be a domain you own with an A record pointing
at the VM's public IP. Caddy auto-provisions HTTPS via Let's Encrypt.

If you don't have a domain yet, use `--self-signed` and point Caddy at
`your-vm-ip.nip.io` — a free DNS that resolves to the IP.

## Vault sync (Phase 1: Git-backed)

Local and Cloud share a **git-synced vault**. The spec explicitly
permits this:

> *For Vault sync (Phase 1) use Git (recommended) or Syncthing.*

How it works:
- `AI_Employee_Vault/` is already in the public repo.
- `.gitignore` blocks every secret (`.env`, `secrets/`, `.heartbeat*`,
  `.limits/`, `.ralph_state/`).
- Cloud runs `deploy/cloud/scripts/vault_sync.sh` every 60 seconds:
  pull → tick → commit-if-dirty → push.
- Local runs the same script on its own cadence.
- Merge conflicts are rare because Cloud writes only to
  `/In_Progress/cloud-agent/`, `/Plans/<domain>/`,
  `/Pending_Approval/<domain>/`, and `/Updates/`. Local writes to
  `/Approved/`, `/Done/`, `Dashboard.md`, and `/In_Progress/local-agent/`.

**Important:** use a dedicated **vault-only** repo (or branch) for
sync to avoid churning your main codebase. See `docs/platinum_deploy.md`
for the two-repo pattern.

## Secrets never sync (spec § Platinum > Security rule)

Confirmed by inspecting `.gitignore`:
```
.env                       # env vars never leave the host
.env.*
secrets/                   # Gmail token, LinkedIn session, banking creds
whatsapp_session/
*.pem
*.key
token.json
```

Cloud's `.env.cloud` (a copy of `deploy/cloud/.env.cloud.example` with
real values filled in) intentionally **omits**:
- `WHATSAPP_SESSION_PATH` (Cloud is fail-closed against it)
- `BANK_*`
- `STRIPE_SECRET_KEY`
- `LIVE_CHANNELS` (Cloud is always dry-run; Local flips live channels)

## Health monitoring

`healthcheck.py` exposes three endpoints (behind Caddy, TLS-terminated):

- `GET /healthz` — 200 OK if all subsystems are alive
  (orchestrator heartbeat < 60 s, Odoo reachable, Postgres reachable)
- `GET /metrics` — JSON with tick count, last claim, Gmail queue depth
- `GET /livez` — lightweight liveness probe for Kubernetes-style checks

Point UptimeRobot, Better Uptime, or Cloudflare Worker cron at
`https://yourdomain.example/healthz`.

## Backups

`backup_odoo.sh` runs nightly at 03:00 UTC via systemd timer:

1. `pg_dump autosapien | gzip > /var/backups/odoo/<date>.sql.gz`
2. Rotate: keep last 7 days local.
3. If `B2_APPLICATION_KEY` is set, also upload to Backblaze B2.
4. Alert to `/Updates/<ts>_backup.md` on failure.

## The A2A upgrade (Phase 2, optional)

The spec calls out:

> *Optional A2A Upgrade (Phase 2): Replace some file handoffs with
> direct A2A messages later, while keeping the vault as the audit record.*

Under `deploy/cloud/a2a/` you'll find a minimal Server-Sent-Events
endpoint that Cloud exposes for Local to stream "I just staged
an approval" notifications, cutting the round-trip from
`60 s git poll` → `<1 s push`. Vault still records everything for
auditability.

Not required for Platinum pass — included because the spec flagged it
as a stretch.

## See also

- `docs/platinum_deploy.md` — step-by-step deployment runbook (what to
  click / paste in the Oracle Cloud console).
- `scripts/cloud_agent.py` — the restricted orchestrator.
- `docker-compose.cloud.yml` — full service graph with healthchecks.
- `Caddyfile` — HTTPS config.
- `systemd/` — unit files for non-Docker deployments.
