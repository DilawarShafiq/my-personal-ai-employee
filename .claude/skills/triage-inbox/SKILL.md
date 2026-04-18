---
name: triage-inbox
description: Triage every file in AI_Employee_Vault/Needs_Action and route it — classify intent, update Dashboard.md, create a Plan if multi-step work is needed, move handled notes to /Done. Use this skill whenever the user says "triage", "process the inbox", or when the Ralph loop is running the Needs_Action queue.
---

# triage-inbox — the first skill every autosapien.com AI Employee loop runs

## When to use this skill
Invoke this skill whenever:
1. The user says *"triage"*, *"process my inbox"*, *"what needs my attention?"*, or
2. The orchestrator / Ralph loop feeds you the prompt `Process all files in /Needs_Action`.

## Inputs
- `AI_Employee_Vault/Needs_Action/*.md` — one file per pending item, written by a watcher.
- `AI_Employee_Vault/Company_Handbook.md` — the rulebook. **Read this first.**
- `AI_Employee_Vault/Business_Goals.md` — priorities for the current quarter.
- `AI_Employee_Vault/Dashboard.md` — the single-writer status page you will update.

## Process
1. **Load the handbook.** Never skip this. If the handbook disagrees with the
   user's prompt, ask before proceeding.
2. For each file in `Needs_Action/`, in oldest-first order:
   1. Read the YAML frontmatter. Extract `type`, `priority`, `status`, `from`.
   2. Classify the item using § 5 *Triage rules* in `Company_Handbook.md`:
      `urgent | sales | support | admin | noise`.
   3. **Decide the next step:**
      - `noise` → move the file directly to `/Done/` with a one-line log.
      - `urgent` → create a `Plans/PLAN_<slug>.md` and surface it in Dashboard.
      - `sales` / `support` / `admin` → draft a reply in `Plans/PLAN_<slug>.md`
        and, if the action is *send-class* (email send, payment, post),
        create a matching `Pending_Approval/<ACTION>_<slug>.md` file.
   4. Never send, post, or pay directly from this skill. The Action layer
      (MCP servers) reads only from `/Approved/`.
3. After the loop, append one entry per handled item to `Dashboard.md`
   under *Recent activity* (most recent first) with the timestamp,
   classification, and action taken.
4. Write a JSON audit line to `Logs/YYYY-MM-DD.jsonl` for every decision
   using the schema in § 6.3 of the hackathon spec.

## Guardrails (non-negotiable)
- **PHI redaction.** If a file contains any of: patient name, DOB, MRN,
  claim number with identifiers, phone number in a clinical context —
  redact before writing anything back into the vault. Replace with
  `[REDACTED_PHI]` and note the category.
- **Approval thresholds.** Apply the table in `Company_Handbook.md § 3`
  literally. If in doubt, require approval.
- **Never invent metrics.** Revenue, denial rates, AR days — only cite
  numbers tagged `verified:` in `Business_Goals.md`.

## Output contract
You are done when:
- Every file originally in `Needs_Action/` has moved to one of:
  `/Plans/`, `/Pending_Approval/`, or `/Done/`.
- `Dashboard.md` has a fresh *Recent activity* entry for each.
- `Logs/<today>.jsonl` has one audit line per decision.
- Your final turn contains the literal promise: `<promise>TRIAGE_COMPLETE</promise>`
  (used by the Ralph Wiggum Stop hook in Gold tier).
