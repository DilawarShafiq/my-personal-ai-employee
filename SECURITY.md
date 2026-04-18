# Security disclosure — autosapien.com Personal AI Employee

> Required by hackathon submission rules. Read this before running the
> code against any account that actually matters.

## Threat model (who we are defending against)
1. **The AI itself.** The most likely incident is *not* malice — it's a
   confident hallucination leading to a sent email, posted tweet, or
   paid invoice the human never approved. Every send-class action
   therefore requires a human-moved approval file.
2. **Prompt injection.** Inbound email / WhatsApp / file drop content
   is treated as untrusted data. Skills never execute instructions
   embedded in customer messages; they reason about them.
3. **Local filesystem compromise.** If the dev laptop is compromised,
   anything in `.env` or `secrets/` is lost. That is accepted. The
   vault contains zero credentials and no PHI, so even the markdown
   files that sync via git are safe to expose.
4. **Cloud agent compromise (Platinum).** Cloud never has payment,
   WhatsApp, or banking secrets. Worst case on a cloud breach: drafts
   get polluted — but nothing ships without a local approval move.

## Credential handling
- **All secrets live in `./.env` (gitignored) or `./secrets/` (gitignored).**
  A `.env.example` ships in the repo showing every required key *without
  values*. See [.env.example](./.env.example).
- **OS keyring** (`keyring` library) is the upgrade path for production;
  the hackathon build uses `.env` for speed.
- **No secret ever lands in the vault.** Search regex scripts can verify
  this by grepping the vault for keys like `AKIA`, `Bearer `,
  `ACCESS_TOKEN`, `password:` — zero hits is the passing bar.
- **Gmail OAuth** uses the standard installed-app flow with
  `offline` access. Tokens are stored at `./secrets/gmail_token.json`
  with filesystem perms 600 on Unix; on Windows the file is inside
  the gitignored `secrets/` folder.
- **LinkedIn** uses a captured Playwright session (also gitignored).
  No LinkedIn password is stored in the repo.
- **X, FB, IG** use long-lived app tokens that live in `.env` only.

## Sandboxing & dry-run (belt + suspenders)
- `DRY_RUN=true` is the **factory default** in `.env.example`. With
  this set, every MCP tool short-circuits before performing the real
  external action and returns a canned success response plus a
  `dry_run: true` flag. This is what the demo video uses.
- Separate test Gmail / X / LinkedIn accounts are strongly recommended
  during development. The hackathon submission was built against test
  accounts only.
- **Rate limits** are enforced in code, not just docs:
  - `MAX_EMAILS_PER_HOUR=10` (email MCP, on-disk counter)
  - `MAX_SOCIAL_POSTS_PER_DAY=6` per channel (social MCP)
  - `MAX_PAYMENTS_PER_DAY=3` (accounting MCP — draft ceiling)
- **Rate limiters are process-wide and date-keyed** so restarting the
  orchestrator cannot reset the counter mid-window.

## HITL approval contract
- Every send-class action (email send, invoice post, payment,
  subscription cancel, social post) writes a file into
  `AI_Employee_Vault/Pending_Approval/<domain>/`.
- Files execute **only** when the human moves them to
  `AI_Employee_Vault/Approved/`.
- The approval watcher verifies the approval file by filename
  convention (`EMAIL_<msg_id>*.md`, `INVOICE_<draft_id>*.md`, etc.).
  MCP tools re-check the approval file existence before taking the
  action — defense in depth against a rogue skill call.
- Approvals expire 24–48h after creation (declared in frontmatter);
  a stale approval is ignored at dispatch.

## PHI policy (why this is HIPAA-flavored, not HIPAA-certified)
- **The vault never stores PHI.** Every watcher redacts at ingress.
  Gmail watcher stores only headers + the 150-char Gmail snippet. The
  message body stays in Gmail and is only read on-demand via the
  Gmail MCP when a skill explicitly needs it. WhatsApp and file-drop
  watchers follow the same rule.
- If Claude accidentally proposes a note containing PHI, the `triage-inbox`
  and `draft-reply` skills require a re-read against
  `Company_Handbook.md § 1 PHI & security policy` before writing.
- **This hackathon build is not a HIPAA-certified system.** It is a
  demonstration of the patterns Dilawar uses in production. A real
  HIPAA deployment would require: BAAs with every cloud vendor,
  encrypted-at-rest vault, SIEM-backed audit log retention, and a
  security review Dilawar's team runs internally.

## Audit logging
- Every external action writes a JSONL line to
  `AI_Employee_Vault/Logs/<YYYY-MM-DD>.jsonl` with:

```json
{
  "timestamp": "2026-04-19T08:03:12Z",
  "actor": "email_mcp|social_mcp|approval_watcher",
  "action_type": "email_send",
  "result": "success|dry_run|denied_no_approval|rate_limited|error",
  "target": "...",
  "parameters": {"subject": "...", "draft_id": "..."},
  "approval_status": "approved|pending|none",
  "approved_by": "human|null"
}
```

- Logs are **append-only** during a run (no in-process rewriting).
- Retention per hackathon spec: **90 days minimum**. The vault's
  `Logs/` folder is not pruned automatically.

## Permission boundaries (Claude Code scope)
Defined in `.claude/settings.json`:
- **Allow:** read/write inside `AI_Employee_Vault/**` only; run `uv`
  commands, local Python modules, and `docker compose` for Odoo.
- **Deny:** read or write `.env`, anything in `secrets/`, shell
  pipelines like `curl | sh`, and `rm -rf`.

## Known limitations (be honest)
- Ralph Stop hook has a hard `RALPH_MAX_ITERATIONS=8` cap. A
  genuinely complex multi-day task will hit this and surface an
  incident file — that is intentional.
- The Playwright LinkedIn flow uses HTML selectors that change when
  LinkedIn redesigns. Expect to re-capture the session 2–3×/year.
- On Windows, Ralph's bash hook requires Git Bash (or WSL) on PATH. A
  PowerShell variant is provided for pwsh users.

## Responsible disclosure
If you spot a security issue in this submission, please email
`dilawar.gopang@gmail.com` directly before opening a public issue.
