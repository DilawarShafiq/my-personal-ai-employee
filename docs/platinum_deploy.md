# Platinum tier deployment runbook

Step-by-step guide to running the autosapien AI Employee as a
production-ish 24/7 cloud + local executive. Total time: **~30 min**
if you already have an Oracle Cloud account; 15 min otherwise.

## 0. What you'll end up with

```
           Local laptop (Windows)                Oracle Free VM (Ubuntu)
           ┌─────────────────────────┐            ┌─────────────────────────┐
           │ local-agent orchestrator│  git pull  │ cloud-agent orchestrator│
           │  - approval watcher     │◄──────────►│  - Gmail watcher        │
           │  - WhatsApp watcher     │            │  - fs watcher           │
           │  - payment MCP          │   Shared   │  - Odoo MCP (drafts)    │
           │  - final send/post     │    vault   │  - no send; no WhatsApp │
           └─────────────┬───────────┘     git    └─────────────┬───────────┘
                         │                                      │
                         ▼                                      ▼
           ┌─────────────────────────────────────────────────────────────┐
           │  Single git-synced Obsidian vault (markdown only, no keys)  │
           │  /In_Progress/local-agent/  /In_Progress/cloud-agent/       │
           │  /Plans/<domain>/   /Pending_Approval/<domain>/   /Updates/ │
           │  Dashboard.md (single-writer: Local)                        │
           └─────────────────────────────────────────────────────────────┘

                                 ┌─────────────────────┐
                                 │  Caddy (HTTPS LE)   │
                                 │  - /healthz         │
                                 │  - /odoo/*          │
                                 │  - /metrics         │
                                 └──────────┬──────────┘
                                            │
                                 ┌──────────┴──────────┐
                                 │   Odoo 19 + PG 16   │
                                 │   nightly backup    │
                                 └─────────────────────┘
```

## 1. Prerequisites

- Oracle Cloud Free Tier account (or any Ubuntu 22.04+ VM with ≥ 2 vCPU / 4 GB RAM).
- A domain with an A record pointing at the VM's public IP. Use
  `<public-ip>.nip.io` if you don't have a domain — it's free and works.
- Gmail OAuth credentials already minted on Local (see `docs/gmail_oauth_setup.md`).
- Local side already set up (repo cloned + watchers running — the rest of this repo).

## 2. Create the Oracle Free Tier VM

1. Sign up at https://cloud.oracle.com (free forever tier, no credit card charge).
2. **Compute → Instances → Create Instance**:
   - Image: **Ubuntu 22.04 (Canonical)**
   - Shape: **VM.Standard.A1.Flex** — pick **4 OCPU / 24 GB RAM**. Always-free eligible.
   - Network: default VCN + public subnet. Assign public IP.
   - SSH keys: upload your public key or generate one now.
3. **Networking → VCN → Subnet → Security List**: open ingress on TCP **80** and **443**
   (Oracle leaves these closed by default).
4. Wait ~60 s for provisioning. Copy the public IP.

## 3. Set up DNS (optional but recommended)

At your DNS provider (Cloudflare, Route 53, etc.):
- Add an A record: `autosapien-cloud.yourdomain.example` → `<public-ip>`.
- Wait ~5 min for propagation.

No domain? Use `<public-ip>.nip.io` — works out of the box with Let's Encrypt.

## 4. SSH in and bootstrap

```bash
ssh ubuntu@your-vm-ip

# Clone into /root/autosapien (matches the systemd unit paths)
sudo git clone https://github.com/DilawarShafiq/my-personal-ai-employee.git /root/autosapien

# One-shot deployer — installs Docker, opens firewall, generates Odoo
# DB password, writes .env.cloud, brings up the full stack, installs
# the nightly backup systemd timer.
sudo bash /root/autosapien/deploy/cloud/bootstrap_oracle_free.sh \
    autosapien-cloud.yourdomain.example \
    dilawar.gopang@gmail.com
```

The script finishes with:
```
Deployment complete.
  Public: https://autosapien-cloud.yourdomain.example/healthz
  Odoo:   https://autosapien-cloud.yourdomain.example/odoo/web/login
```

## 5. Upload Gmail credentials + create DB

On your Local machine:

```bash
scp secrets/gmail_credentials.json secrets/gmail_token.json \
    ubuntu@your-vm-ip:/tmp/
```

Then on the VM:

```bash
sudo mv /tmp/gmail_*.json /root/autosapien/deploy/cloud/secrets/
sudo chown root:root /root/autosapien/deploy/cloud/secrets/*.json
sudo chmod 600 /root/autosapien/deploy/cloud/secrets/*.json

# Restart the cloud-agent so it picks up the credentials.
cd /root/autosapien/deploy/cloud
sudo docker compose restart autosapien-cloud
```

Create the Odoo DB and seed it (same scripts as Local, but pointed
at the public URL):

```bash
ODOO_URL=https://autosapien-cloud.yourdomain.example/odoo \
ODOO_DB=autosapien \
ODOO_PASSWORD="$(grep ODOO_DB_PASSWORD .env.cloud | cut -d= -f2)" \
sudo docker compose exec autosapien-cloud \
    python scripts/create_odoo_db.py

# Then seed healthcare data (customers + products + invoices):
ODOO_URL=... sudo docker compose exec autosapien-cloud \
    python scripts/seed_odoo.py
```

## 6. Set up the shared vault repo

The spec requires a **git-synced vault**. Two options:

### Option A (simpler, recommended) — vault lives in this repo
You're doing this already. The `AI_Employee_Vault/` folder is inside
the public repo. Cloud pulls and pushes back via the
`vault-sync` sidecar container. Merge conflicts are rare because
Cloud and Local write to disjoint folders by convention.

**Caveat:** every vault update creates a commit in the public repo.
Fine for a demo; noisy long-term.

### Option B (tidier) — dedicated vault repo
Create a **private** repo `autosapien-vault` and cherry-pick the
`AI_Employee_Vault/` folder into it. Set `VAULT_REPO_URL` in
`.env.cloud` to that repo. Then the vault-sync sidecar works against
that repo only, and the main code repo stays stable.

See `deploy/cloud/README.md` § Vault sync for details.

## 7. Run the Platinum demo against the real cloud

On your Local machine, with the cloud stack running:

```bash
# Send yourself an email from any account to dilawar.gopang@gmail.com.
# Wait ~60-120 s for the Cloud Gmail watcher to pick it up.

# Watch the vault sync pull the new /Needs_Action/EMAIL_<id>.md:
cd C:\Users\TechTiesIbrahim\hackathon0_by_dilawar
git pull            # or let the sidecar do it on its timer

# You should see:
#   /Needs_Action/EMAIL_<gmail_id>.md         (written by Cloud)
#   /In_Progress/cloud-agent/EMAIL_...md      (claimed by Cloud)
#   /Plans/email/PLAN_...md                   (drafted by Cloud reasoning)
#   /Pending_Approval/email/EMAIL_...md       (staged for your approval)
#   /Updates/<ts>_cloud.md                    (Cloud's dashboard bump)

# Review the draft, drag to /Approved/.  Local approval watcher
# dispatches the real send via the Email MCP.  Cloud never does.
```

That's the **Platinum minimum passing gate** from the spec:
*Email arrives while Local is offline → Cloud drafts reply + writes
approval file → when Local returns, user approves → Local executes
send via MCP → logs → moves task to /Done.*

## 8. Health monitoring

Point **UptimeRobot** (free) or **Cloudflare Workers Cron** at:
```
https://autosapien-cloud.yourdomain.example/healthz
```

Returns 200 when orchestrator heartbeat is < 60 s old and Odoo is
reachable; 503 otherwise.

## 9. Backups

Happens automatically via the systemd timer (`autosapien-backup.timer`).
Runs nightly at 03:00 UTC:

1. `pg_dump autosapien | gzip` → `/var/backups/odoo/<date>.sql.gz`
2. Keeps last 7 days on disk.
3. If `B2_APPLICATION_KEY` is set, uploads off-site to Backblaze B2.

Verify with:
```bash
ls -la /var/backups/odoo/
journalctl -u autosapien-backup.timer --since yesterday
```

## 10. Shutting down

```bash
sudo systemctl stop autosapien-cloud.service
cd /root/autosapien/deploy/cloud
sudo docker compose down           # keeps volumes
# or: sudo docker compose down -v  # NUKES Odoo data — don't do unless you have a backup
```

## Troubleshooting

**Caddy can't provision the cert.**
Check the A record points at the VM's public IP; check Oracle's
Security List opens TCP 80. Let's Encrypt needs port 80 to complete
the ACME http-01 challenge.

**`vault-sync` container keeps crashing.**
The git deploy key at `deploy/cloud/secrets/git_deploy_key` must be
readable and authorized to push to the vault repo. Add it as a deploy
key on GitHub/GitLab with write permissions.

**Cloud-agent refuses to start.**
Read the boot log: it will name the forbidden env var that triggered
the fail-closed check. Usually `ENABLE_WHATSAPP_WATCHER=true` snuck
into `.env.cloud`. Remove it.

**Odoo login page 502s.**
`proxy_mode=True` must be set in `odoo/config/odoo.conf`. Already
configured in the repo, but double-check the container mounted it.

---

**You're pure Platinum now.** Local + Cloud, git-synced vault, HTTPS
Odoo, nightly backups, health monitoring, fail-closed role separation.
The architecture matches the spec § Platinum line by line.
