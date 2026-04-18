---
name: subscription-audit
description: Audit monthly subscriptions against usage + BAA + duplication rules, produce a flag list, and stage cancellation approval files for the CEO. Use when the user says "audit subscriptions" / "find software waste" or when a scheduled trigger lands in /Needs_Action.
---

# subscription-audit — the CEO's procurement deputy

## Inputs
- `Business_Goals.md § Subscription audit rules`
- `Business_Goals.md § Current known subscriptions` (our source of truth)
- `Accounting/Current_Month.md` (expense side)
- Future: Odoo `account.move.line` category = *Software*

## Rules (from handbook)
Flag a subscription if **any** apply:
1. `Last login > 30 days`.
2. Cost increased > 20% vs previous month.
3. Duplicate functionality with another tool (two issue trackers, two
   design tools, two docs apps).
4. **Touches PHI without a signed BAA** — this is an instant cancel
   recommendation in a healthcare company, regardless of usage.

## Process
1. Build a table of (vendor, $/mo, last_login, baa, purpose).
2. Apply the four rules. For each flagged row, write a
   `Pending_Approval/CANCEL_<vendor>.md` file:

```markdown
---
type: approval_request
action: cancel_subscription
vendor: <name>
amount_monthly: <n>
reason_codes: [<rule_id>, ...]
evidence: |
  <the specific data that triggered each rule>
created: <iso>
expires: <iso +7d>
status: pending
---

## Recommendation
Cancel <vendor>. Monthly savings: $<n>. Annual: $<n*12>.

## Evidence
- <bullet: last login, cost trend, duplicate tool, BAA status>

## Rollback cost
<how painful is re-onboarding if we change our mind>
```

3. Aggregate totals in a single `Plans/PLAN_subscription_audit_<date>.md`:
   "N tools flagged, $X/mo savings, $Y/yr savings if all approved".

## Non-goals
- Never cancel directly. Always stage approval.
- Never assume a vendor touches PHI without reading the row's `BAA`
  column — if it's marked ❌ and the vendor's purpose is patient-facing,
  flag it; if purpose is "design" or "code editor", it's fine.

## Output contract
- One `Plans/PLAN_subscription_audit_*.md`.
- One `Pending_Approval/CANCEL_<vendor>.md` per flagged tool.
- Append `Dashboard.md`: "Subscription audit: <n> flagged, $<savings>/mo".
- Log JSONL for each flag decision.
- `<promise>SUBSCRIPTION_AUDIT_COMPLETE</promise>`.
