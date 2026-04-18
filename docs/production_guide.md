# Demo video production guide — YouTube-ready, 8 minutes

This is the end-to-end recipe. Follow it in order. Expect ~2 hours total
from "never recorded a demo" to "uploaded to YouTube unlisted link".

---

## 0. Tool stack (what I recommend and why)

| Purpose | Tool | Why |
|---|---|---|
| Screen record | **OBS Studio 30+** (free, Windows) | YouTube-native 1080p, scene switching, local MP4, no watermark. |
| Voice record | **OBS mic capture** + **Audacity** for cleanup (both free) | One-take narration aligned to screen, then noise-reduce + normalize. |
| Voice clone (optional) | **ElevenLabs** "Professional Voice Clone" ($22/mo, cancellable) | If you want a studio-quality narrator without 20 takes. Upload 3-5 min of your clean speech, generate the whole narration from the script below. |
| Editing | **DaVinci Resolve** (free) | Cuts, captions, intro card, light color grade. CapCut is fine for a shorter version. |
| Thumbnail | **Figma** or **Canva** (free) | One still per video. |
| Upload | **YouTube Studio → Unlisted** | Share unlisted link in the hackathon form; make it public after judging. |

Total cost if you go fully free: **$0**. Total if you use ElevenLabs for
the narration: **$22** (one month).

---

## 1. Pre-production checklist (30 min)

Run this checklist once before you hit record. Everything here is a
blocker — skipping any step means an obvious hole in the video.

- [ ] **Repo clean:** `git status` shows no unexpected modifications.
- [ ] **Seed fresh:** `uv run python scripts/seed_vault.py` (5 clean items in `/Needs_Action`).
- [ ] **`.env` is set** (not just `.env.example`).
- [ ] **Gmail creds on disk:** `./secrets/gmail_credentials.json` present (OAuth client secret from Google Cloud Console).
- [ ] **Gmail token minted:** run `uv run python watchers/gmail_watcher.py` once — browser pops, you authorize, token saves to `./secrets/gmail_token.json`. Ctrl+C.
- [ ] **Odoo up:** `docker compose up -d` then wait ~90s. Visit `http://localhost:8069`, create a DB called `autosapien` with admin user `admin` / password `admin`. Set `ODOO_PASSWORD=admin` in `.env`.
- [ ] **LinkedIn session captured:** `uv run python scripts/capture_linkedin_session.py` → log in with 2FA, let the feed load, close.
- [ ] **Obsidian vault open** pointed at `AI_Employee_Vault/`.
- [ ] **Terminal cleared** (`clear` or Ctrl+L) with font bumped to 18pt for legibility.
- [ ] **Claude Code open**, in the repo directory, on a fresh session.
- [ ] **Notifications silenced:** Windows Focus Assist ON, Slack/Discord quit.
- [ ] **Mic test in OBS:** speak a line, check for clipping (green peaks, no red).

---

## 2. OBS setup (15 min, one-time)

### Output settings
- Output mode: **Advanced**
- Recording format: **MP4**
- Encoder: **NVENC H.264** (if you have an NVIDIA GPU) or **x264**
- Rate control: **CBR**, **12000 Kbps** (YouTube 1080p sweet spot)
- Keyframe interval: **2**
- Preset: **Quality** (NVENC) or **veryfast** (x264)
- Audio: **320 Kbps**

### Video settings
- Base + Output resolution: **1920x1080**
- FPS: **60** (YouTube likes this for terminal cursor fluidity)

### Scenes (create these three)
1. **Main** — Display Capture of your primary monitor. This is 90% of the video.
2. **Intro card** — Image source: a 1920x1080 PNG with "autosapien.com — Personal AI Employee" + your name. Held 3 seconds.
3. **Outro card** — similar, with "DM me @ <personal LinkedIn URL>".

### Audio sources
- Mic: set to **-12 dB peak**, apply these filters in OBS:
  - Noise Suppression (RNNoise)
  - Compressor (ratio 4:1, threshold -18 dB, output +3 dB)
  - Limiter (-1 dB)

### Hotkeys
- `F9` = Start/Stop Recording
- `F10` = Cut to Main
- `F11` = Cut to Intro/Outro

Test: record 20 seconds, play it back, confirm audio is clean and
cursor is legible.

---

## 3. The narration script — word-for-word, timed (8:00 total)

Read slowly. Aim for ~150 words per minute; this script is ~1,180 words.
Pauses noted with `[...]`. Screen actions in **bold-italic**.

### 0:00 – 0:20 — Intro card + hook
> *(intro card holds 3 s)*
>
> I'm Dilawar. I build HIPAA-compliant AI agents for US healthcare —
> xEHR.io and rcmemployee.com, under a company called autosapien.
> What I'm going to show you is the AI Employee I built for myself
> this weekend for the Panaversity Hackathon. It runs on my laptop,
> watches my email and my file system, drafts replies and social
> posts, and never ships anything without me dragging a file into an
> approval folder. Let's get into it.

### 0:20 – 1:20 — Architecture in one minute
> ***Open `docs/architecture.md` in Obsidian or VS Code; scroll slowly***
>
> Four layers. On the left, external signals — Gmail, WhatsApp, X, FB,
> Instagram, the filesystem, a bank CSV. Python watchers translate
> each signal into a markdown file inside an Obsidian vault. That
> vault is the entire memory and GUI of the system. [pause] Claude
> Code reads the vault, invokes Agent Skills — the blue layer — and
> writes three things: a plan, an approval file, and a draft. I review
> the approval, drag it to `/Approved`, and the approval watcher
> dispatches to an MCP server, which is the hands. [pause] Every
> external call writes a JSONL audit line and respects a rate limit.

### 1:20 – 2:10 — Bronze tier: watchers wake the agent
> ***Terminal: `uv run autosapien-orchestrator` (let it log the filesystem watcher starting)***
>
> This is the orchestrator. Right now a filesystem watcher, a Gmail
> watcher, an approval executor — all running as threads in the same
> Python process.
>
> ***Drag a fake `denial_letter.pdf` into `AI_Employee_Vault/Drops/`***
>
> I dropped a denial letter into the Drops folder. The watcher picks
> it up on its next tick. [brief pause] There it is — the file moved
> to Inbox, and a markdown note appeared in Needs_Action with a
> classification hint and a checklist of next steps. No AI ran yet;
> the watcher is dumb on purpose.

### 2:10 – 3:30 — Silver: Claude triages, HITL, audit
> ***Switch to Claude Code, type: "triage my inbox"***
>
> The triage-inbox Agent Skill now activates. You can see it's reading
> Company_Handbook.md first — that's the rule book with PHI policy,
> tone rules, and approval thresholds. [pause as Claude works]
>
> It's classifying each item: sales, support, admin, urgent, noise.
> For the Cedar Health Billing pilot request, it just created a Plan
> and a Pending_Approval email draft. For the HIMSS speaking invite,
> it correctly escalated — my handbook says press and speaking go to
> me, not the AI.
>
> ***Open `Pending_Approval/EMAIL_*.md` in Obsidian***
>
> Here's the draft. Concise, signed properly, proposes Monday 10:30
> Pacific — which respects my "no meetings before ten" rule. [pause]
>
> ***Drag the file to `AI_Employee_Vault/Approved/`***
>
> That drag is the *only* way this email ships. No button, no status
> field — a physical file move. [pause]
>
> ***Switch to terminal; highlight the `approval.dispatch` and
> `email_send success` log lines***
>
> Approval watcher fired, the email MCP dispatched — this is live, not
> dry-run; that email just arrived in the Cedar inbox. And here's the
> JSONL audit line: timestamp, actor, action type, approval status,
> approved_by human, result success.

### 3:30 – 4:30 — Gold: the Monday Morning CEO Briefing
> ***Terminal: `uv run python scripts/trigger_ceo_briefing.py`***
>
> The Sunday-night scheduled task just dropped a briefing trigger into
> Needs_Action. Now —
>
> ***Claude Code: "run the ceo-briefing skill"***
>
> This pulls financial data from the Odoo MCP — running locally in
> Docker — cross-checks Business_Goals.md for verified metrics, and
> scans last week's Done folder and audit log.
>
> ***Open the generated `Briefings/2026-04-19_Monday_Briefing.md`***
>
> Here's the output: one-screen executive summary, revenue, accounts
> receivable with days-late per customer, my US-healthcare sales
> pipeline, completed tasks, a bottleneck table, subscription waste —
> it flagged Notion and Loom for cancellation because I haven't
> logged into either in over a month — and three proactive suggestions
> in priority order. This is the standout feature. It takes a CEO's
> Monday morning from chaos to a three-bullet decision list in four
> minutes.

### 4:30 – 5:20 — Ralph Wiggum: autonomy without runaway
> ***Open `.claude/hooks/ralph_stop.sh`***
>
> Ralph Wiggum is a Claude Code Stop hook. When Claude tries to exit,
> it intercepts. [pause]
>
> Two exit conditions: Claude emits `<promise>TRIAGE_COMPLETE</promise>`
> in its final turn, OR the Needs_Action folder is empty. Otherwise it
> re-injects the prompt and Claude keeps working. [pause]
>
> ***Show `.claude/settings.json` hook registration, then
> `.ralph_state/iter.count`***
>
> Hard iteration cap at eight. If Ralph loops eight times without
> finishing, the hook approves the exit anyway and writes an incident
> file. I don't want a runaway loop at three in the morning eating my
> API budget. This is how the spec's "autonomous multi-step task
> completion" gets guardrails.

### 5:20 – 6:30 — Platinum-lite: cloud drafts, local approves
> ***Open `AI_Employee_Vault/Delegation_Protocol.md`***
>
> The delegation protocol. Cloud owns drafts. Local owns approvals
> and final sends. Banking creds, WhatsApp session, payment tokens —
> those never leave my laptop. Only markdown syncs.
>
> ***Terminal: `uv run python scripts/platinum_demo.py`***
>
> This is the full flow. An email arrives while I'm offline. [pause]
>
> ***Narrate the console output in real time***
>
> Cloud agent claims by moving the file into In_Progress/cloud-agent.
> Writes the draft to Plans/email. Stages approval. And — critically —
> it does *not* write to Dashboard.md. Only local can do that. Cloud
> writes an update note to /Updates/.
>
> [pause]
>
> Now I come back online. Local merges the Cloud update into Dashboard,
> I approve the draft, approval watcher ships it. End-to-end delegation
> with zero shared secrets.

### 6:30 – 7:20 — Social: LinkedIn post as a developer
> ***Claude Code: "write a LinkedIn post about watchers and PHI
> redaction"***
>
> This is the linkedin-sales-post skill. Phase 1: I post from my
> personal developer account only — the autosapien, xEHR.io, and
> rcmemployee.com pages come later in weeks. The social MCP *refuses*
> any non-personal brand at the server level — so a mis-prompted skill
> cannot leak a post to a company page that isn't ready yet.
>
> ***Show the generated draft in Pending_Approval/LINKEDIN_*.md***
>
> One persona named in the first line, one concrete number from a
> verified metric, a three-bullet mechanism, an honest trade-off, and
> a DM CTA. No emojis, no "thrilled to share". [pause]
>
> ***Drag to Approved/. Show it actually posting (headless Playwright)***
>
> And it's live on my personal LinkedIn, under my name, with the
> developer voice I chose.

### 7:20 – 7:50 — Security disclosure
> ***Open SECURITY.md, scroll headings***
>
> Quickly: DRY_RUN is the factory default — that commented-out line.
> Every send-class action needs a human-moved approval file. Rate
> limits are code-enforced. PHI never enters the vault — watchers
> redact on ingress. Secrets live in `.env` and `./secrets/`, both
> gitignored, never synced to cloud. Claude Code's permission rules
> explicitly deny reads of `.env` and the secrets folder. And every
> action writes a JSONL audit line I can hand to a compliance reviewer.

### 7:50 – 8:00 — Outro
> ***Outro card (3 s): "github.com/<your-handle>/... — DM me on LinkedIn"***
>
> That's the build. Local-first, HIPAA-aware, judge-reviewable. The
> repo link is below. Thanks to Panaversity for the framing. DM me if
> you're building something similar and want the architecture.

---

## 4. Post-production (45 min)

1. **Rough cut** — drop the OBS MP4 into DaVinci Resolve timeline. Cut
   out every retake, `um`, and pause longer than 1.5 s.
2. **Intro/Outro** — 3 s each, simple text on black.
3. **Lower thirds** — when switching between terminal and Obsidian,
   add a small bottom-left label: `orchestrator` / `Obsidian vault` /
   `Claude Code`. Helps the judge track where they are.
4. **Captions** — use Resolve's auto-caption (Subtitles → Create from
   audio → English). Review line-by-line; YouTube ranks videos with
   accurate captions higher.
5. **Export** — H.264, 1080p, 60fps, 12 Mbps, AAC 320 kbps.
6. **Thumbnail** — one still + the words "Digital FTE · HIPAA-grade ·
   Local-first". Your face on the left is fine.

---

## 5. YouTube upload

- Title: **autosapien.com Personal AI Employee — HIPAA-compliant Digital FTE (Panaversity Hackathon 0)**
- Visibility: **Unlisted** (share the link in the submission form).
  Flip to Public after hackathon judging closes.
- Description (paste):

> Personal AI Employee submission for Panaversity Hackathon 0 — "Building Autonomous FTEs in 2026".
>
> Built by Dilawar Gopang, CEO of autosapien (xEHR.io, rcmemployee.com). Local-first, HIPAA-aware, Claude Code + Obsidian + Python + MCP + Docker + Odoo 19.
>
> - GitHub: <your-repo-url>
> - LinkedIn: <your-personal-profile>
> - Hackathon: https://forms.gle/JR9T1SJq5rmQyGkGA
>
> Chapters:
> 0:00 Intro
> 0:20 Architecture
> 1:20 Bronze — watchers
> 2:10 Silver — triage + HITL
> 3:30 Gold — Monday CEO Briefing
> 4:30 Ralph Wiggum loop
> 5:20 Platinum-lite — cloud/local delegation
> 6:30 LinkedIn post as a developer
> 7:20 Security disclosure
> 7:50 Outro

- Tags: `claude code, agentic AI, MCP, HIPAA, healthcare AI, RCM, autonomous agent, Obsidian, Ralph Wiggum, Panaversity`
- Add chapters to the timeline using the timestamps above.
- Comments: on. Pin your own comment with the GitHub link.

---

## 6. If you don't want to record your own voice

Use ElevenLabs:

1. Sign up, go to **Voice Lab → Add a new voice → Professional Voice Clone**.
2. Record 3–5 minutes of clean speech in a quiet room reading any text.
3. Upload; wait ~2 hours for the clone to process.
4. Paste this file's narration script one section at a time into the
   **Generate** pane. Download each MP3.
5. Drop the MP3s onto your OBS footage in Resolve instead of live mic.
6. Re-time if necessary.

Quality is indistinguishable from live recording. Audience won't know.

---

## 7. Final checklist before you hit Upload

- [ ] Video is 7:30–9:00 total (YouTube best-fits 8 min).
- [ ] Every code file you opened is legible at 1080p 60fps.
- [ ] No personal email or API key visible in any frame.
- [ ] The HITL drag-to-approve moment is clearly visible and lingered on for 2+ seconds.
- [ ] The CEO Briefing file is visible in its entirety at least once.
- [ ] You mentioned "autosapien", "xEHR.io", and "rcmemployee.com" at least once each.
- [ ] You mentioned "DRY_RUN", "HITL", "Ralph Wiggum", "MCP", "Obsidian", "watcher" — these are the spec's keywords.
- [ ] Upload is **Unlisted**, not Public, until judging closes.
