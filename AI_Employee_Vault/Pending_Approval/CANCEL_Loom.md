---
type: approval_request
action: cancel_subscription
vendor: Loom
amount_monthly: 18
reason_codes: [no_login_30d, duplicate_functionality]
evidence: |
  Last Loom recording: 2026-03-02 (42 days ago).
  Duplicate functionality: OBS Studio (free) covers 100% of what we
  used Loom for — customer demo recordings and internal walkthroughs.
  We also moved demo hosting to YouTube unlisted.
created: 2026-04-13T07:00:00Z
expires: 2026-04-20T07:00:00Z
status: pending
generated_by: subscription-audit skill
---

## Recommendation
Cancel Loom. Monthly savings: $18. Annual: $216.

## Evidence
- Last recording created: 2026-03-02.
- OBS Studio is the upgrade path for recording (we use it for the demo
  videos in this repo).
- YouTube unlisted is the upgrade path for hosting.
- No customer links from Loom videos in the last 60 days (zero
  external views per Loom analytics).

## Rollback cost
Loom keeps recordings for 30 days post-cancellation. The 12 videos
worth keeping were already exported locally on 2026-04-12 to
`/Vault/Archives/loom_exports_2026-04-12/`.

## On approve
Move this file to `/Approved/`. Same manual-billing-UI pattern as
Notion — the approval watcher records the intent, Dilawar clicks
cancel in the Loom billing portal.
