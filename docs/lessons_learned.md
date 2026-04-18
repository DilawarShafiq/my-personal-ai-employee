# Lessons learned — building the autosapien.com AI Employee

> Required by Gold tier. These are honest notes from a one-day sprint
> against the Panaversity Hackathon 0 spec, by Dilawar Gopang.

## 1. The vault IS the API. Don't build a separate one.

I spent ~15 minutes early on tempted to add a tiny REST layer between
watchers and the orchestrator. I didn't. The markdown-vault-as-protocol
idea in the spec is the thing that makes the architecture composable:
a watcher, a skill, a human, and an MCP server can all collaborate
without knowing anything about each other — they only know how to read
and write files in known folders. The moment you add an API in the
middle, every new agent has to learn that API.

**Takeaway:** For multi-agent systems, a shared filesystem + agreed
folder names is a more portable "protocol" than any JSON contract.

## 2. HITL must be a file move, never a keypress.

The first version of the approval flow used a `status: approved` field
in YAML that the human was supposed to flip. I killed that pattern
within an hour: it's too easy to automate by accident. The final design
requires a physical file move from `/Pending_Approval/` to `/Approved/`.
Obsidian makes this a drag-and-drop; a script cannot "accidentally"
do it without explicit intent.

**Takeaway:** Authorization by *gesture* beats authorization by *state
edit* for an AI employee. Make the consent signal impossible to
hallucinate.

## 3. YAML frontmatter will betray you.

Spent 15 minutes debugging why `subject: Re: HIPAA question before demo`
parsed as an empty frontmatter. YAML read the second colon as a nested
mapping and errored out silently because the approval watcher swallowed
the `YAMLError` and returned `{}`. Fix was in two places:

1. Always quote user-supplied string fields (`subject: "..."`).
2. In the parser, add a line-by-line fallback so one bad field never
   nukes the whole approval.

**Takeaway:** Template any user-derived text fields with explicit
quotes, and don't let a single YAML bug silence a full approval.

## 4. Graceful degradation needs to be the default, not an afterthought.

The Odoo MCP returns a hand-authored demo snapshot whenever the real
Odoo is unreachable, tagged `live: false, source: demo_fallback`. This
was a 5-line change that made the entire demo resilient to Docker
being off. The alternative — throwing a `ConnectionRefusedError` up
into Claude's reasoning — would crash the CEO Briefing skill mid-run.

**Takeaway:** For every external call in an agentic system, ask *"what
does this return when the world is on fire?"* and write that path
first. The happy path is the exception, not the rule.

## 5. Ralph Wiggum needs a hard iteration cap, not just a promise.

My first Stop hook only checked for `<promise>TASK_COMPLETE</promise>`.
During testing I wrote a skill that forgot to emit the promise on the
"nothing to do" branch and the hook re-injected the prompt forever.
Solution: dual-condition exit (promise OR queue-empty) plus a
hard-coded 8-iteration cap via `.ralph_state/iter.count`.

**Takeaway:** Any self-reinjecting loop needs at least three ways to
terminate. Never trust the model alone to know when it's done.

## 6. Brand guard at the MCP layer, not the prompt layer.

I could have instructed the LinkedIn skill: *"don't post to the
autosapien page, only personal_dilawar"*. Instead the social MCP
refuses any `brand != "personal_dilawar"` at the server level. This
means a rogue skill — or a future me changing the prompt without
reading the handbook — still cannot leak a post to a product page
before those pages go live.

**Takeaway:** Enforce consequential business rules as code at the edge
of the system, not as text in a prompt. Prompts drift; code doesn't.

## 7. PHI redaction belongs on the watcher, not on the skill.

First draft had the Gmail watcher copying message bodies into
`Needs_Action/` and the `triage-inbox` skill redacting before writing
further notes. That's backwards — by the time the skill runs, the
body is already on disk. Fixed the watcher to store only headers +
a 150-char Gmail snippet; the full body is fetched on-demand through
the Gmail MCP when (and only when) a skill explicitly needs it.

**Takeaway:** In a HIPAA-adjacent system, make sensitive data need to
be *pulled in*, never simply *present by default*.

## 8. Windows line endings vs bash Stop hook.

The Ralph bash hook stopped firing mid-development because Git silently
converted it to CRLF on Windows. `.gitattributes` with
`.claude/hooks/* text eol=lf` fixed it permanently. A PowerShell
variant (`ralph_stop.ps1`) ships alongside so Windows-first developers
have a native option.

**Takeaway:** Cross-platform shell scripts need `.gitattributes` *and*
a platform-native alternative — don't assume bash is available.

## 9. What I'd do differently with another day.

- Real Ralph hook plugin using the canonical layout at
  `anthropics/claude-code/.claude/plugins/ralph-wiggum` instead of my
  ad-hoc `.claude/hooks/*` scripts.
- Actual cloud VM for Platinum — Oracle Free tier, not a simulator.
  The simulator is a great demo but a real Git-synced dual-agent setup
  exposes race conditions (two agents claiming the same item in the
  same second) that a single-process demo hides.
- Replace the Playwright LinkedIn flow with LinkedIn's marketing API
  once the company page is ready — session scraping is fragile.
- Add a `dry_run: false` gated CI test that actually sends to a test
  inbox weekly, so we catch when a Gmail API field rename breaks us.

## 10. What the spec got exactly right.

The "Ralph Wiggum" framing and the "watchers wake the agent" framing
are not just cute names — they're load-bearing architecture choices.
Without Ralph, Claude stops after one turn and the AI employee is
useless for multi-step tasks. Without watchers, you're back to a
chatbot. The spec nailed both. All I had to do was implement them
honestly.
