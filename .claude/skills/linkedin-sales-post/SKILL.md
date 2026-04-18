---
name: linkedin-sales-post
description: Draft a LinkedIn post from Dilawar's PERSONAL developer account about agentic AI workflow automation — technical, honest, targeted at one of four personas per post. Use when the user says "LinkedIn post", "write a post", or when the weekly marketing cadence fires. Never posts directly; always stages for approval.
---

# linkedin-sales-post — developer voice, not marketing voice

## When to use
- User prompt contains *"LinkedIn post"*, *"dev post"*, *"write a post"*.
- Weekly cadence fires the Monday / Thursday slot (Gold tier).

## Non-negotiables (phase 1)
- **Brand:** `personal_dilawar` — this is the ONLY active channel until
  the product pages go live. Never stage a post targeting an autosapien,
  xEHR.io, or rcmemployee.com page in this phase.
- **Voice:** engineer-to-engineer. If you wouldn't say it on a GitHub
  issue, don't write it here. No "thrilled to share", no "game-changing",
  no emojis, no em-dash as filler.
- **Theme:** agentic AI workflow automation. Healthcare is the worked
  example, not the topic — the topic is how to build agents that do real
  work under HIPAA-class constraints.

## Post structure (target 140–220 words)
1. **Persona-select first line.** Name one of the four personas
   (CTO at clinic, clinic owner, RCM director, startup founder) in sentence
   one so the reader self-selects. Example:
   *"If you're the only engineer at a healthcare billing company and denials
   are eating your week — this is for you."*
2. **Specific technical hook.** One number or one contrarian claim,
   drawn from an *actual* autosapien build. Use only `verified: ✅`
   metrics from `Business_Goals.md`.
3. **The mechanism (3–5 bullets).** Concrete moving parts — not "AI
   reviewed claims" but "a watcher classifies payer remit codes → skill
   drafts an appeal letter → MCP submits via clearinghouse → HITL
   for anything touching a new payer".
4. **Honest trade-off (1–2 lines).** What's hard. What you tried first
   and dropped. This is the part that makes it dev content, not an ad.
5. **DM CTA (1 line).** *"DM me if you're building something similar and
   want the architecture."* Never "link in bio", never "what do you think?".

Hashtags: 0–2 max. Approved set: `#AgenticAI`, `#WorkflowAutomation`,
`#HIPAA`. Skip hashtags entirely on technical threads — they feel like ads.

## Process
1. Pick this week's angle from a small rotation:
   - Watchers (sensing layer)
   - MCP servers (action layer)
   - Human-in-the-loop patterns
   - Ralph loops / iteration control
   - PHI redaction in practice
   - Observability (JSONL audit, dry-run defaults)
2. Draft into `Plans/PLAN_linkedin_<slug>.md`. Include a "why this
   persona" note at the top so the approver knows who it's for.
3. Self-check:
   - ✅ Exactly one persona named in the first 2 sentences.
   - ✅ Exactly one concrete number (from verified metrics).
   - ✅ No corporate-account voice. If it sounds like it could come from
        a VP of Marketing, rewrite.
   - ✅ No product pitch. xEHR.io / rcmemployee.com are receipts, not asks.
   - ✅ Ends with a DM CTA, not a "thoughts?" question.
4. Create `Pending_Approval/LINKEDIN_<slug>.md`:

```markdown
---
type: approval_request
action: linkedin_post
brand: personal_dilawar
slug: <kebab-slug>
persona_target: <cto|owner|rcm_director|founder>
angle: <watchers|mcp|hitl|ralph|phi|observability>
created: <iso>
expires: <iso +48h>
status: pending
word_count: <n>
verified_metrics_used: [<rows from Business_Goals.md>]
---

## Post content
<exact text>

## Why this persona, why this week
<2 lines>
```

## Output contract
- `Plans/PLAN_linkedin_<slug>.md` (draft + rationale).
- `Pending_Approval/LINKEDIN_<slug>.md` (ready-to-post).
- Update `Dashboard.md` *Recent activity*.
- `<promise>LINKEDIN_DRAFT_COMPLETE</promise>`.
