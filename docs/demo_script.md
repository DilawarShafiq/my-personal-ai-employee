# Demo video shot list (target 8 minutes)

Record with OBS + a single monitor. Two windows visible: a terminal
pinned to the left half, VS Code or Obsidian on the right half. Voice
over calm, engineer voice (you are not pitching, you are showing how
it works).

> **Before you hit record:** `DRY_RUN=true`, seed vault is fresh,
> Claude Code is open and pointed at the repo.

---

## 0:00–0:30 — The 30-second hook
- Camera on Obsidian vault + terminal.
- Say: *"I'm Dilawar from autosapien. I build HIPAA-compliant AI
  agents for US healthcare. This is my personal AI employee. It runs
  on my laptop, watches my email and file drops, drafts replies and
  social posts, never sends anything without my approval. Here's how."

## 0:30–1:30 — The architecture in 60 seconds
- Open `docs/architecture.md`, scroll the ASCII diagram.
- Narrate: *"Four layers. Watchers see the world. The vault is memory
  and GUI at once. Claude Code reasons, using Agent Skills as the
  playbook. MCP servers are the hands. Every send-class action goes
  through a file-move approval."*

## 1:30–3:00 — Bronze + Silver demo
- Terminal: `uv run python scripts/seed_vault.py`
- Show Obsidian sidebar: 5 seeded items in `/Needs_Action`.
- Terminal: `uv run autosapien-orchestrator &`
- Drag a fake `denial_letter.pdf` into `AI_Employee_Vault/Drops/`.
- Show new `FILE_denial_letter_*.md` appear in `/Needs_Action`.
- Open Claude Code, say: *"triage my inbox"*.
- Watch Claude run `triage-inbox`. Show it:
  - Reading `Company_Handbook.md` first.
  - Creating `Plans/PLAN_cedar_pilot_kickoff.md`.
  - Creating `Pending_Approval/EMAIL_*.md` with the draft reply.
  - Moving handled items to `/Done/`.
  - Updating `Dashboard.md`.

## 3:00–4:30 — HITL approval (the money shot)
- Camera on Obsidian.
- Drag one approval file from `/Pending_Approval/` → `/Approved/`.
- Switch to terminal — show the orchestrator log emitting
  `approval.dispatch` and `approval.email_dry_run`.
- Show the JSONL audit line in `AI_Employee_Vault/Logs/`.
- Show the file now in `/Done/`.
- Say: *"That's the whole contract. Drag to approve. Nothing else
  ships."*

## 4:30–5:30 — CEO Briefing (the standout feature)
- Terminal: `uv run python scripts/trigger_ceo_briefing.py`
- Show the new `BRIEFING_TRIGGER_*.md` in `/Needs_Action`.
- Claude Code: *"run the ceo-briefing skill"*.
- Watch it call the Odoo MCP (falls back to seed data — honest),
  aggregate the week's `Done/` items, check `Business_Goals.md`.
- Open the generated `Briefings/2026-04-19_Monday_Briefing.md`.
- Scroll through: revenue, AR, sales pipeline, bottlenecks, 3
  proactive suggestions.

## 5:30–6:30 — Ralph Wiggum in action
- Delete the `<promise>TRIAGE_COMPLETE</promise>` from a fake test
  run to force the Stop hook to loop.
- Show `.claude/hooks/ralph_stop.sh` re-injecting the prompt.
- Show the iteration counter in `.ralph_state/iter.count`.
- Ctrl-C. Say: *"Claude doesn't go home until the queue is empty
  or the iteration cap fires."*

## 6:30–7:30 — Platinum-lite demo
- Terminal: `uv run python scripts/platinum_demo.py`
- Narrate over the output:
  - Email arrives while "local is offline".
  - Cloud agent claims via `/In_Progress/cloud-agent/`.
  - Cloud writes draft to `/Plans/email/`, approval to
    `/Pending_Approval/email/`, update to `/Updates/`.
  - Human approves — `Dashboard.md` merges the cloud update.
  - Approval watcher ships. File lands in `/Done/`.
- Point out the git-sync boundary: *"Secrets don't sync. Markdown
  does. Cloud never touches my banking creds."*

## 7:30–8:00 — Wrap
- Show `SECURITY.md` briefly.
- Say: *"DRY_RUN is true by default. You could git-clone this and
  run it tonight without fear. Every escalation — new recipient,
  payment, press, legal — goes through me. That's the deal I wanted
  with my AI employee. Thanks to Panaversity for the framing."*

## Submission checklist (after recording)
- [ ] Upload video to YouTube unlisted.
- [ ] Final README pass — ensure quickstart works on a clean clone.
- [ ] Push repo to GitHub (public).
- [ ] Submit to https://forms.gle/JR9T1SJq5rmQyGkGA — tier = **Gold
      (+ Platinum-lite)**.
