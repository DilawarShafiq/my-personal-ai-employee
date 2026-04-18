# autosapien.com Personal AI Employee — Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SIGNALS                             │
│  Gmail  │  WhatsApp  │  X/FB/IG DMs  │  Bank CSV  │  File drops     │
└─────┬──────────┬──────────┬───────────────┬──────────┬──────────────┘
      │          │          │               │          │
      ▼          ▼          ▼               ▼          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       PERCEPTION LAYER (watchers/)                  │
│   base_watcher ── gmail_watcher ── filesystem_watcher ── ...        │
│   (PHI redaction happens HERE, on ingress — vault never sees PHI)   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ write markdown
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│              OBSIDIAN VAULT  (AI_Employee_Vault/)                   │
│   Dashboard.md            single-writer (local-agent)               │
│   Company_Handbook.md     rules of engagement                       │
│   Business_Goals.md       verified metrics + subscription truth     │
│   Delegation_Protocol.md  cloud/local split (Platinum)              │
│                                                                     │
│   /Inbox       /Needs_Action   /In_Progress/<agent>/                │
│   /Plans       /Pending_Approval   /Approved   /Rejected            │
│   /Done        /Briefings   /Logs   /Updates   /Signals             │
└─────────┬───────────────────────────────────────────────────────────┘
          │ read
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    REASONING LAYER  (Claude Code)                   │
│   Agent Skills (.claude/skills/):                                   │
│     triage-inbox ── draft-reply ── plan-work ── linkedin-sales-post │
│     ceo-briefing ── subscription-audit ── sales-lead-outreach       │
│     invoice-generator ── brand-router                               │
│                                                                     │
│   Stop hook (.claude/hooks/ralph_stop.sh):                          │
│     <promise>…</promise>  OR  /Needs_Action drained  →  approve exit│
│     else  →  block + re-inject prompt (capped at 8 iterations)      │
└─────────┬───────────────────────────────────────────────────────────┘
          │ writes Plan.md, Pending_Approval/*.md, Updates/*.md
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      HUMAN-IN-THE-LOOP                              │
│   Dilawar reviews /Pending_Approval/ in Obsidian.                   │
│   Approves by DRAGGING a file into /Approved/ — never by typing.    │
│   Rejects by dragging into /Rejected/.                              │
└─────────┬───────────────────────────────────────────────────────────┘
          │ move
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│              ACTION LAYER (mcp_servers/ + orchestrator/)            │
│   approval_watcher.py  polls /Approved/ every 5s, dispatches:       │
│                                                                     │
│   • email_mcp       gmail_get_message / create_draft / send_draft   │
│   • odoo_mcp        financial_snapshot / draft_invoice / post       │
│   • social_mcp      x_post / fb_post / ig_post / linkedin_post      │
│                                                                     │
│   All servers enforce:                                              │
│     · approval-file existence check                                 │
│     · brand allowlist (phase-1 = personal_dilawar only)             │
│     · rate limit counters in /.limits/                              │
│     · DRY_RUN short-circuit                                         │
│     · JSONL audit line on every call (Logs/YYYY-MM-DD.jsonl)        │
└─────────┬───────────────────────────────────────────────────────────┘
          │
          ▼
    EXTERNAL WORLD:  send email · post social · create invoice · ...

┌─────────────────────────────────────────────────────────────────────┐
│           ORCHESTRATION + HEALTH  (orchestrator/)                   │
│   orchestrator.py   threads: filesystem_watcher, gmail_watcher,     │
│                     approval_watcher; writes .heartbeat every 5s    │
│   watchdog.py       parent process: restarts on crash or stale hb;  │
│                     writes Needs_Action/INCIDENT_*.md after Nth fail│
│                                                                     │
│   Windows Task Scheduler registered via                             │
│   scripts/install_windows_tasks.ps1:                                │
│     · autosapien-Orchestrator   (at logon)                          │
│     · autosapien-MondayBriefing (Mon 07:00)                         │
│     · autosapien-SubscriptionAudit (Sun 21:00)                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│          PLATINUM-LITE  — cloud-drafts / local-approves             │
│                                                                     │
│   cloud-agent  ──► /Needs_Action/ claim  ──► /Plans/<domain>/       │
│                ──► /Pending_Approval/<domain>/                      │
│                ──► /Updates/<ts>_cloud.md   (never Dashboard.md!)   │
│                                                                     │
│      [git push]  ───────────────────►  [git pull, human review]     │
│                                                                     │
│   local-agent  ──► merges /Updates/ into Dashboard.md               │
│                ──► moves /Pending_Approval/ → /Approved/            │
│                ──► approval_watcher ships via MCP                   │
│                ──► audit log                                        │
│                                                                     │
│   Secrets (.env, secrets/, .heartbeat, .limits/) never sync.        │
└─────────────────────────────────────────────────────────────────────┘
```

## Why this shape wins
1. **Watchers wake the agent.** No polling by Claude. No idle burn.
2. **The vault IS the protocol.** File movement == authorization,
   state, and audit trail in one. Works offline, works across agents,
   works with Obsidian as the UI.
3. **HITL is a filesystem move, not a UI click.** Impossible to
   accidentally authorize with a keypress. Judges can show this on
   camera in 5 seconds.
4. **Brand guard at MCP layer.** A rogue LinkedIn skill cannot post
   from the company page because the social MCP refuses every
   non-`personal_dilawar` brand in phase 1.
5. **Graceful degradation baked in.** Odoo down → demo data still
   flows through the CEO Briefing. Watchdog respawns crashed
   orchestrators. Ralph loop caps runaway iterations. Rate limiters
   hard-stop runaway sends.
