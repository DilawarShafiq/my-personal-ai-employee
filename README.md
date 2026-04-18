# autosapien.com — Personal AI Employee (Hackathon 0 submission)

> **Tier:** Gold (+ Platinum-lite stretch)
> **Author:** Dilawar Gopang — CEO, [autosapien.com](https://autosapien.com) — builder of [xEHR.io](https://xEHR.io) and [rcmemployee.com](https://rcmemployee.com)
> **Hackathon:** Panaversity *Personal AI Employee Hackathon 0 — Building Autonomous FTEs in 2026*

A local-first, HIPAA-aware Digital FTE that runs my healthcare-RCM startup's day-to-day work on autopilot. Watchers see the world, Claude Code reasons, Agent Skills codify the playbook, and MCP servers are the hands. Everything non-trivial requires human-in-the-loop approval by file movement — the AI can draft, but only the CEO can send, pay, or post.

## Why this build wins
1. **Real domain, not a toy demo.** Built and narrated as if running `autosapien.com`: healthcare RCM, BAAs, denial overturn rates, PHI redaction baked into every watcher.
2. **Standout feature, polished.** The *Monday Morning CEO Briefing* is generated from an Odoo-backed ledger, a week's worth of completed work, and a subscription-usage audit — not from vibes.
3. **Safety-first architecture.** File-based HITL (`/Pending_Approval` → move to `/Approved`), hard rate limits, DRY_RUN default true, `deny` rules in Claude settings for `.env` and `secrets/`.
4. **Ralph Wiggum loop** implemented as a proper Claude Code Stop hook + a file-movement completion strategy so the agent iterates until each task file lands in `/Done`.
5. **Platinum-lite delegation demo.** Two Claude contexts against one git-synced vault prove the Cloud-drafts / Local-approves pattern with `claim-by-move` and single-writer `Dashboard.md`.

## Architecture at a glance
```
   EXTERNAL  ──►  WATCHERS  ──►   OBSIDIAN VAULT  ──►  CLAUDE CODE  ──►  HITL  ──►  MCP  ──►  ACTION
  (Gmail/WA/                      (Markdown =            (Agent Skills                       (Email,
   Files/Bank/                      Memory + GUI)         + Ralph loop                         Odoo,
   Social)                                                + triage)                            X/FB/IG/LI)
```

## Quickstart (Bronze — runs in 60 seconds)
```bash
# Prereqs: Python 3.11+, uv (https://github.com/astral-sh/uv)
git clone <this repo>
cd hackathon0_by_dilawar

uv sync                                     # install deps
cp .env.example .env                        # DRY_RUN=true is the default
uv run python scripts/seed_vault.py         # populate vault with 5 demo items
uv run autosapien-orchestrator               # starts filesystem watcher
```

Then open the `AI_Employee_Vault/` folder in Obsidian and point Claude Code at this directory — `triage-inbox` will find the seeded messages.

## Tier progression
- **Bronze** — vault + filesystem watcher + `triage-inbox` Agent Skill. Runs anywhere.
- **Silver** — Gmail watcher, LinkedIn auto-sales-post skill, Email MCP, HITL approval loop, Windows Task Scheduler jobs.
- **Gold** — Odoo 19 (Docker) + JSON-RPC MCP, X/FB/IG MCPs, weekly CEO Briefing, Ralph Wiggum Stop hook, audit-log JSONL, error recovery.
- **Platinum-lite** — git-synced vault with `/Updates/` + `claim-by-move` demo of cloud/local split.

## Security disclosure (short version)
- Secrets only in `.env` (gitignored) and `./secrets/` (gitignored). Vault contains zero credentials.
- `DRY_RUN=true` is the factory default; every action script short-circuits with a log line unless explicitly unlocked.
- Payments over $500, new-recipient emails, subscription cancellations, and all press/legal items always require HITL approval.
- Hard rate limits: 10 emails/hour, 6 social posts/day, 3 payments/day.
- PHI never touches the vault — watchers redact on ingress.

See [SECURITY.md](SECURITY.md) for the long version.

## Repo layout
```
hackathon0_by_dilawar/
├── AI_Employee_Vault/      # Obsidian vault (the brain's memory)
├── watchers/               # Python perception layer
├── mcp_servers/            # Action layer (email, Odoo, social)
├── orchestrator/           # Process supervisor + ralph loop glue
├── scripts/                # seed_vault, dev utilities
├── .claude/
│   ├── skills/             # Agent Skills (every AI behavior lives here)
│   ├── hooks/              # Ralph Wiggum Stop hook
│   └── settings.json       # permission allow/deny rules
└── docs/                   # architecture diagrams, demo script
```

## Demo video
See `docs/demo_script.md` for the 8-minute walkthrough shot list and
`docs/production_guide.md` for the OBS + narration + upload checklist.

## Troubleshooting FAQ

**Claude Code says the MCP server won't start.**
Run `uv sync` once in the repo root — the MCP servers execute via
`uv run`, and if the lockfile is stale the command silently errors.
Check `.mcp.json` has absolute paths or is being resolved from the
repo root.

**The orchestrator starts, but no watcher is firing.**
By default only the filesystem watcher runs. Opt into the others by
setting `ENABLE_GMAIL_WATCHER=true` and/or `ENABLE_WHATSAPP_WATCHER=true`
in `.env` and restarting. Gmail also needs `secrets/gmail_credentials.json`.

**Ralph hook never re-injects.**
Check `.claude/settings.json` > `hooks.Stop`. On Windows the bash script
needs Git Bash on PATH; if you use pwsh, swap the `command` to
`./.claude/hooks/ralph_stop.ps1` and `shell` to `powershell`.

**Odoo MCP returns `live: false` with seed data.**
Expected when Docker isn't running. Bring Odoo up with
`docker compose up -d` and wait ~90 seconds for the DB to init.

**YAML "mapping values not allowed" in the approval log.**
A frontmatter field (usually `subject`) contains an unquoted colon
(e.g. `subject: Re: foo`). Always quote free-text fields:
`subject: "Re: foo"`. The `draft-reply` skill template already does this.

**Playwright browser doesn't launch (LinkedIn / WhatsApp).**
Run once: `uv run playwright install chromium`.

**Windows Task Scheduler script says "scripts are disabled".**
Launch an elevated PowerShell and run once:
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.

## Ethics & responsible automation

This AI Employee operates under Dilawar's name, using his credentials,
on his behalf. That is a deliberate design choice, not a technical
accident. The safeguards baked into the repo — HITL on every send, PHI
redaction at ingress, DRY_RUN-by-default, brand guards at the MCP
layer, rate limits in code — all exist because **the human remains
accountable**, full stop.

Things this AI is *never allowed* to do autonomously:

| Surface | Why |
|---|---|
| Sign contracts or BAAs | Legally binding, always human. |
| Respond to press / podcast / speaking inquiries | Reputation-level. |
| Send condolence messages or handle grief contexts | Emotional nuance. |
| Initiate payments to a **new** recipient | Fraud vector. |
| Post to autosapien / xEHR.io / rcmemployee.com pages (phase 1) | Brand guardrail; social MCP refuses this at the server layer. |
| Touch anything containing patient PHI | Hard rule in `Company_Handbook.md § 1`. |

Recommended oversight cadence, borrowed from the hackathon spec:

- **Daily:** 2-minute Dashboard glance.
- **Weekly:** 15-minute `Logs/*.jsonl` review.
- **Monthly:** 1-hour comprehensive audit (approvals, rejections, what
  the AI got wrong).
- **Quarterly:** Full security + access review; rotate credentials.

If you fork this to run your own AI employee, please keep these
guardrails. The system works because the guardrails are there — not
because the guardrails are noise around a working system.

## License
MIT. Fake customer names in seed data are fictional; any resemblance to real clinics is coincidental.
