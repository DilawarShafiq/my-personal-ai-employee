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
See `docs/demo_script.md` for the 8-minute walkthrough shot list.

## License
MIT. Fake customer names in seed data are fictional; any resemblance to real clinics is coincidental.
