# Pre-flight checklist — run this once before recording

One clean terminal session, top to bottom. Expect ~25 min if nothing
is installed yet, ~5 min if you've done this once.

All commands run from the repo root:
`C:\Users\TechTiesIbrahim\hackathon0_by_dilawar`

## 1. Dependencies (2 min)

```powershell
uv sync                                # install Python deps
uv run playwright install chromium     # one-time browser install
```

## 2. Environment file (1 min)

```powershell
copy .env.example .env
```

Open `.env` and set these (leave everything else as the default):

```
DRY_RUN=true
LIVE_CHANNELS=linkedin          # only LinkedIn goes live in the demo
ENABLE_GMAIL_WATCHER=true
ENABLE_WHATSAPP_WATCHER=false   # off for this demo; enable later
ODOO_PASSWORD=admin             # matches what you'll set in Odoo step 5
```

## 3. Gmail OAuth (10 min — first time only)

See **`docs/gmail_oauth_setup.md`**. End state:

- `secrets/gmail_credentials.json` exists
- `secrets/gmail_token.json` exists (minted from a one-time OAuth
  browser dance)

## 4. LinkedIn session (3 min — first time only)

```powershell
uv run python scripts\capture_linkedin_session.py
```

Log in as yourself, complete 2FA, wait for the feed to load, close the
browser. Session persists at `secrets/linkedin_session/`.

## 5. Odoo (5 min — first time only)

```powershell
docker compose up -d
```

Wait ~90 seconds for the DB to init. Then:

1. Open **http://localhost:8069** in a browser.
2. "Create Database" form:
   - Master password: `admin` (or anything; write it down)
   - Database Name: **`autosapien`**
   - Email: **admin**
   - Password: **admin**
   - Language: English (US)
   - Country: United States
   - Uncheck "Demo data" (we'll seed via MCP)
3. Click **Create database**. Wait ~60 s.
4. Log in with `admin` / `admin`. Verify you see the Odoo dashboard.

## 6. Seed the vault (30 s)

```powershell
uv run python scripts\seed_vault.py
```

You should see 5 items in `AI_Employee_Vault/Needs_Action/`.

## 7. Verify everything boots (30 s)

```powershell
uv run python -c "from watchers.filesystem_watcher import FileSystemWatcher; from watchers.gmail_watcher import GmailWatcher; from mcp_servers.odoo_mcp.server import _safe_snapshot; s = _safe_snapshot(); print('gmail import OK, odoo live:', s['live'])"
```

If `odoo live: True` — all four live pieces are ready.
If `odoo live: False` — Docker is off; the demo will gracefully
degrade but you miss the "Odoo snapshot" beat in the briefing.

## 8. OBS sanity record (3 min)

1. Open OBS Studio.
2. Apply the settings from `docs/production_guide.md § 2`.
3. Create the three scenes (Main, Intro, Outro).
4. Record 30 s of you saying hello + a terminal command. Play it back.
   Confirm audio is clean and cursor is legible.

## 9. Silence notifications (1 min)

- Windows: **Focus assist → Alarms only** (Win+A).
- Quit Slack, Discord, Teams, Outlook.
- Close every browser tab that isn't the ones you need for the demo
  (localhost:8069, LinkedIn, Google Cloud Console).

## 10. Clear state immediately before recording

```powershell
uv run python scripts\seed_vault.py     # re-seed to pristine state
```

Then restart the orchestrator so watcher processed-ids are fresh:

```powershell
uv run autosapien-orchestrator
```

Ctrl+C it before you start recording (you'll start it live on camera).

You're ready. Hit **F9** in OBS and deliver the narration from
`docs/production_guide.md § 3`.
