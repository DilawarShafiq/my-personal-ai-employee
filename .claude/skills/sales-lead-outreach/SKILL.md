---
name: sales-lead-outreach
description: Draft personalized cold-outreach emails to US healthcare prospects (clinics, billing companies, medical groups) for xEHR.io and rcmemployee.com demos. Use when the user says "draft outreach", "cold email X", "sales email to <clinic>", or when a prospects-list file lands in /Needs_Action.
---

# sales-lead-outreach — the top-of-funnel engine

autosapien's primary KPI for this AI Employee is **qualified demo
requests** from US healthcare. This skill is how we stage them.

## Inputs
- A prospect record — from a CSV drop, a Gmail import, or a user-typed list.
  Minimum fields: `org_name`, `org_type` (clinic | billing_co | medical_group),
  `specialty` (ortho | psych | primary | OB/GYN | ...), `contact_name`, `contact_email`.
- `Business_Goals.md` — which `verified: ✅` metric to cite.
- `Company_Handbook.md § 4 Content & sales motion`.

## Draft shape (opinionated)
- **Subject:** ≤ 40 chars, includes the org's specialty or a specific number.
  *Good:* "cutting denials at Cedar Ortho — 15 min?"
  *Bad:* "Partnership opportunity"
- **Opener (1 line):** A specific observation about them (practice size,
  recent press, a specialty workflow pain). Never "I hope this finds you well."
- **Relevance bridge (2 lines):** What autosapien does *for that archetype*.
  - For clinics → xEHR.io angle (charting, eligibility, intake).
  - For billing companies → rcmemployee.com angle (denials, AR, prior auth).
- **One metric (1 line):** From `Business_Goals.md` verified rows only.
- **Ask (1 line):** "Worth a 15-min call next Tue or Thu?" — specific, easy yes.
- **Signature:** from handbook § 2.

**Total length target: 85–130 words.** Longer = lower reply rate for cold.

## Process
1. Triage the inbound prospect list. Discard rows without a
   valid-looking contact email. Dedupe by domain.
2. Per row, draft the email into `Plans/PLAN_outreach_<slug>.md`.
3. For each draft, create `Pending_Approval/OUTREACH_<slug>.md` with
   `action: send_email` and the draft body. New recipient → always HITL
   per handbook § 3.
4. Update `Dashboard.md`: "Outreach: N drafts staged for <org_type>s".

## PHI safety
Cold outreach NEVER mentions a patient, a provider by name, or a payer
contract. Use publicly verifiable attributes only (practice size, specialty,
location, funding round if relevant).

## Output contract
- Per-prospect `Plans/PLAN_outreach_<slug>.md` + `Pending_Approval/OUTREACH_<slug>.md`.
- Dashboard updated with batch summary.
- `<promise>OUTREACH_DRAFTS_READY</promise>`.
