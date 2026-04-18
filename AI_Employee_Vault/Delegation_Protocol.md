---
type: protocol
version: 1.0
phase: platinum-lite
---

# Delegation Protocol — Cloud ↔ Local agents, one synced vault

This file is the rulebook for the Platinum-tier work-zone split. It is
read at the top of every Cloud-agent turn, and every Local-agent turn
that touches anything in `/Updates/`, `/In_Progress/`, or
`/Pending_Approval/`.

## Agents

| Agent | Runs where | Owns | NEVER touches |
|---|---|---|---|
| **local-agent** | Dilawar's laptop / mini-PC | `Dashboard.md`, all `/Pending_Approval → /Approved` moves, WhatsApp session, banking creds, payment MCPs, final email/social sends. | `/Updates/` (read-only mirror of Cloud work) |
| **cloud-agent** | Oracle Cloud Free VM (or simulated via second Claude context for demo) | Email triage + draft replies, social post drafts + scheduling, Odoo-draft-only bookkeeping, CEO-briefing pre-aggregation. | `.env`, `secrets/`, `Dashboard.md`, anything in `/Approved/` |

## Shared surfaces (both agents read/write)

- `/Needs_Action/` — Cloud can claim by moving to `/In_Progress/cloud-agent/`.
- `/In_Progress/<agent>/` — claim-by-move. Contents are opaque to the other agent.
- `/Plans/<domain>/` — flat: `email/`, `social/`, `accounting/`, `outreach/`.
- `/Pending_Approval/<domain>/` — Cloud writes, Local approves.
- `/Updates/` — Cloud's only way to influence the Dashboard. Local merges entries here into `Dashboard.md` on the next cycle.
- `/Signals/` — small control messages (e.g. `PAUSE_CLOUD.flag`, `RESUME_CLOUD.flag`).

## Ownership invariants (enforced by convention + hooks)

1. **Single-writer rule for `Dashboard.md`.** Only `local-agent` ever
   edits. Cloud writes entries to `/Updates/<iso>_cloud.md` instead;
   Local merges on sync.
2. **Claim-by-move.** An item is "owned" by the first agent to move it
   from `/Needs_Action/` into `/In_Progress/<agent>/`. Other agents
   **must ignore** anything in the other agent's In_Progress folder.
3. **Send/post stays Local.** Any MCP call that transmits to the outside
   world (email send, payment, LinkedIn/X/FB/IG post) is callable only
   by `local-agent`. Cloud's role is drafts + approvals files, never
   actual delivery.
4. **Secrets never sync.** `.gitignore` already excludes `.env`,
   `secrets/`, `.heartbeat`, `.limits/`, `.ralph_state/`. Cloud does
   not have access to WhatsApp session, banking credentials, or
   payment tokens. Period.

## Flow: the Platinum demo (judges' minimum passing gate)

1. **Email arrives** while Dilawar is offline (laptop asleep).
2. Cloud Gmail watcher fires → creates `/Needs_Action/EMAIL_<id>.md`.
3. Cloud claims: moves file into `/In_Progress/cloud-agent/`.
4. Cloud's `triage-inbox` + `draft-reply` skills run → produce
   `/Plans/email/PLAN_<id>.md` + `/Pending_Approval/email/EMAIL_<id>.md`.
5. Cloud writes an update note at `/Updates/<iso>_cloud.md`
   ("1 email drafted, awaiting approval").
6. Cloud pushes git.
7. Dilawar wakes his laptop. Local-agent `git pull`s; sees the new
   pending approval.
8. Dilawar reviews the draft in Obsidian, moves it to `/Approved/`.
9. Local-agent approval watcher fires → email MCP sends → file to `/Done/`.
10. Local-agent merges the `/Updates/` note into `Dashboard.md` and
    writes the audit entry.

Every step above has an audit line in `Logs/<date>.jsonl`.

## Safety tripwires

- A file in `/In_Progress/local-agent/` older than **24h** is abandoned;
  Local may reclaim or delete. Same for Cloud at **4h** (shorter because
  Cloud is always on).
- If `/Signals/PAUSE_CLOUD.flag` exists, Cloud pauses all drafting on
  its next cycle. Local creates this flag before any sensitive manual
  work (contract redline, press response) to avoid conflicting drafts.
- If `/Signals/SIGNING.lock` exists, NO agent may modify
  `/Pending_Approval/` — used during multi-party e-signature flows.
