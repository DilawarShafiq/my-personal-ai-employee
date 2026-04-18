---
type: approval_request
action: linkedin_post
brand: personal_dilawar
slug: agentic-hipaa-watchers
persona_target: cto
angle: watchers
created: 2026-04-13T07:00:00Z
expires: 2026-04-15T07:00:00Z
status: pending
word_count: 178
verified_metrics_used: [denial_overturn_rate]
generated_by: linkedin-sales-post skill
---

## Post content

If you're the CTO or lead engineer at a small healthcare billing
company, this is for you.

The pattern I ship with rcmemployee.com does four things, in order:

1. A **watcher** classifies payer remit codes on ingress (before a
   human touches the file, before anything lands in a markdown vault).
2. A **skill** drafts an appeal letter per remit-code class — no PHI
   in the draft, only claim-level IDs and the code.
3. An **MCP server** submits to the clearinghouse in dry-run by default.
4. A **human approval** is required for any new payer or any
   edge-case remit code the classifier hasn't seen before.

The honest trade-off: we lag about 15 minutes behind a human hitting
F5 on the clearinghouse. In exchange, our denial-overturn rate went
from 48% to 63% last month across the pilot cohort.

If you're building something similar and want the architecture —
DM me.

## Why this persona, why this week
Targeting CTOs because this week's Cedar Health Billing pilot
conversation surfaced that their lead engineer (not the CEO) makes
the tech-stack call. This post should land in his feed tomorrow.

## Hashtags
(none — technical threads read better without them)

## On approve
Move to `/Approved/`. Social MCP posts via the captured Playwright
session (`secrets/linkedin_session/`). With `LIVE_CHANNELS=linkedin`
in `.env`, this posts for real; otherwise it's a dry-run log.
