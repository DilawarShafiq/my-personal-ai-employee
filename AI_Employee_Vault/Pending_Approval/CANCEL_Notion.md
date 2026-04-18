---
type: approval_request
action: cancel_subscription
vendor: Notion
amount_monthly: 15
reason_codes: [no_login_30d]
evidence: |
  Last login by any autosapien user: 2026-02-14 (58 days ago, as of 2026-04-13).
  Anthropic API billing shows zero Notion-webhook invocations since Feb.
  Current usage is zero across both of Dilawar's workspaces.
created: 2026-04-13T07:00:00Z
expires: 2026-04-20T07:00:00Z
status: pending
generated_by: subscription-audit skill
---

## Recommendation
Cancel Notion. Monthly savings: $15. Annual: $180.

## Evidence
- Last login: 2026-02-14, any user in the autosapien workspace.
- Zero active documents edited in the last 45 days (Notion API usage log).
- Our active docs moved to the Obsidian vault (this repo) in mid-February.
- No BAA on file — which was never an issue because we also never stored
  PHI there, but it means zero compliance reason to keep it.

## Rollback cost
Notion retains data for 30 days post-cancellation on the paid tier.
If we reverse inside 30 days, everything comes back. Past 30 days, a
re-subscription starts fresh — but we already mirrored the useful
pages to `/Vault/Archives/notion_export_2026-02-17/`.

## On approve
Move this file to `/Approved/`. The approval watcher will log the
cancellation intent (no automated cancel API — this one requires a
final click in the Notion billing UI, which Dilawar does manually).
