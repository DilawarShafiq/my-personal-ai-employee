---
type: file_drop
completed: 2026-04-12T16:00:00Z
classification: business_data
source: filesystem_watcher
duration_minutes: 12
---

# Q1 2026 denials CSV — routed to /Accounting

Dilawar dropped `cedar_q1_denials_4200rows.csv.enc` into /Drops. The
filesystem watcher moved it to /Inbox with a metadata sidecar.
AI classified as customer business data, confirmed the file was still
encrypted, and routed to `/Accounting/cedar_pilot/` without decrypting.

(Encryption-at-rest rule: the AI never decrypts customer PHI exports;
only the human unlocks.)
