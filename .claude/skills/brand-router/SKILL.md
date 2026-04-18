---
name: brand-router
description: Decide which brand should speak on a given piece of content — personal_dilawar (default, phase 1), autosapien, xEHR.io, or rcmemployee.com. Use before any social post or outbound message whenever the sender is ambiguous.
---

# brand-router — one post, one brand, one voice

## Phase 1 (today, 2026-04-19)
**Always return `personal_dilawar`.** The company and product pages
haven't started posting yet. Any skill that calls this router today
should hardcode `brand: personal_dilawar` and skip the decision.

## Phase 2 (product pages active — weeks out)
When the flag `brand_routing_enabled: true` is present in
`Business_Goals.md`, apply content-aware routing:

| Signal in the draft | Brand |
|---|---|
| Denials / AR / prior auth / eligibility / clearinghouse / coder | `rcmemployee.com` |
| Charting / intake / SOAP / E&M coding / patient scheduling | `xEHR.io` |
| SOC 2 / hiring / roadmap / funding / company milestone | `autosapien` |
| Architecture / MCP / watchers / agent patterns / philosophy / peer-to-peer dev stories | `personal_dilawar` |

Tie-breaker: pick the most technically specific brand that fits. When
in doubt, route to `personal_dilawar` — the personal account can talk
about anything; the product pages must stay on-topic.

## Output contract
Return a JSON object in your response:
```json
{"brand": "personal_dilawar", "reason": "phase-1 default", "confidence": "certain"}
```
Skills consuming this emit `brand: <value>` in their approval-file
frontmatter so the social MCP dispatches correctly.
