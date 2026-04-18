---
type: approval_request
action: send_email
to: jruiz@cedarhealthbilling.example
subject: "Re: RCM pilot — can we start next Monday?"
thread_id: ""
gmail_message_id: cedar_pilot_kickoff_001
created: 2026-04-13T07:00:00Z
expires: 2026-04-15T07:00:00Z
status: pending
generated_by: draft-reply skill
---

## Draft

Hi Jen,

Great news — happy to kick off Monday.

Here's what I'll send by end of day today:
1. **BAA** via DocuSign from `legal@autosapien.com` — please forward
   to whoever signs on your side and cc me.
2. **Kickoff agenda** — 30 minutes at **10:30 PT**. I'll send the
   calendar invite once you confirm the slot works.
3. **Clearinghouse credentials list** — the exact fields I'll need from
   your payer setup (no actual secrets by email; we'll handshake those
   via your preferred secrets channel).

One ask: can you confirm the 4,200-claim Q1 export is still
clearinghouse-original format (837P raw) and not a re-export from
your billing system? That changes which remit-code parser we point it
at on day one.

Looking forward to it.

— Dilawar Shafiq, CEO, autosapien
https://www.linkedin.com/in/dilawar-shafiq-b8923062/

---

## Why this is staged for approval
- Existing customer relationship + signed pilot SOW, but the email
  references a BAA and an e-signature flow (Handbook § 7: anything
  touching a BAA goes to Dilawar).
- Proposed 10:30 PT respects the "no meetings before 10" rule.
- No PHI — 4,200 claims are referred to by count only, never by
  patient details.

## On approve
Move to `/Approved/`. Email MCP ships; Dilawar still triggers the
DocuSign BAA manually because that is a separate signature flow
outside the email MCP's scope.
