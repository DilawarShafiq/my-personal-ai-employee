---
name: plan-work
description: Turn a multi-step task into a Plan.md with checkboxes, owner, and approval gates. Use when a Needs_Action item has more than one distinct action (e.g., "send BAA + schedule kickoff + share agenda") or when the user says "plan this" / "break this down".
---

# plan-work — the reasoning loop's working memory

## When to use
Fire this skill when:
- An inbound item needs ≥ 2 distinct actions (email + calendar + doc share).
- A project has a multi-day arc (pilot kickoff, SOC 2 evidence pull).
- The user says *"plan this"*, *"break this down"*, *"what's the plan for X"*.

## Output: a Plan.md in `/Plans/`
Every plan follows this exact schema so the Ralph loop, the dashboard
updater, and the human can all read it reliably.

```markdown
---
type: plan
slug: <kebab-case>
objective: <one sentence>
owner: ai_employee   # or `human` if Claude should not proceed unattended
created: <iso>
status: in_progress
linked_source: Needs_Action/<original_file.md>
approval_gates: [<action>, ...]   # e.g. [send_email, linkedin_post]
---

## Objective
<one paragraph: what "done" looks like>

## Context (redacted, no PHI)
- Source: <file>
- Handbook rules that apply: <§ refs>

## Steps
- [ ] 1. <step> — owner: ai | human | customer
- [ ] 2. <step> — owner: ...
- [ ] 3. <step — REQUIRES APPROVAL: create /Pending_Approval/...>
- [ ] 4. <step>

## Dependencies
- Waiting on: <external blocker if any>

## Acceptance criteria
- [ ] Source file moved to /Done
- [ ] Dashboard.md Recent activity updated
- [ ] Audit line written
```

## Process
1. Read the source `Needs_Action/` file + `Company_Handbook.md`.
2. Decompose the objective into ≤ 7 steps. More than that = make a subplan.
3. For each send-class step, point at the exact `Pending_Approval/*.md`
   file the approval watcher will consume.
4. Create the plan file. Do **not** execute any step yet — the Ralph loop
   will re-invoke the right skill (`draft-reply`, `linkedin-sales-post`, ...)
   for each individual step on subsequent iterations.
5. Append one line to `Dashboard.md` *Recent activity*:
   `[<ts>] Plan created: <slug> — <n> steps, <k> approvals required`.
6. Move the source `Needs_Action/` file into `In_Progress/ai_employee/`
   to claim it (Platinum-lite `claim-by-move` rule — prevents other
   agents from double-working it).

## Output contract
- One `Plans/PLAN_<slug>.md` file.
- Source moved to `In_Progress/ai_employee/`.
- Dashboard updated.
- End turn with `<promise>PLAN_READY</promise>`.
