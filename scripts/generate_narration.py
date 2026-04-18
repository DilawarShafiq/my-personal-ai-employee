"""Generate a full MP3 narration for the demo video using Microsoft
Neural TTS (via edge-tts — free, no API key, no account needed).

Produces:
  docs/rendered/narration/00_intro.mp3
  docs/rendered/narration/01_architecture.mp3
  docs/rendered/narration/02_bronze.mp3
  docs/rendered/narration/03_silver.mp3
  docs/rendered/narration/04_gold.mp3
  docs/rendered/narration/05_ralph.mp3
  docs/rendered/narration/06_platinum.mp3
  docs/rendered/narration/07_linkedin.mp3
  docs/rendered/narration/08_security.mp3
  docs/rendered/narration/09_outro.mp3
  docs/rendered/narration/full.mp3    (all concatenated)
  docs/rendered/narration/full.srt    (subtitles for DaVinci Resolve)

Voice: en-US-AndrewMultilingualNeural (male, warm, dev-leaning).
Swap VOICE below for en-US-BrianNeural (neutral), en-US-ChristopherNeural
(deeper), or en-US-AriaNeural (female) to your taste.

    uv run python scripts/generate_narration.py
"""
from __future__ import annotations

import asyncio
import os
from datetime import timedelta
from pathlib import Path

import edge_tts

VOICE = "en-US-AndrewMultilingualNeural"
RATE = "-8%"   # slightly slower than default for technical content
OUT_DIR = Path("docs/rendered/narration")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEGMENTS = [
    ("00_intro", """\
I'm Dilawar. I build HIPAA compliant AI agents for US healthcare. xEHR dot io and rcmemployee dot com, \
under a company called autosapien. What I'm going to show you is the AI Employee I built for myself this \
weekend for the Panaversity Hackathon. It runs on my laptop, watches my email and my file system, drafts \
replies and social posts, and never ships anything without me dragging a file into an approval folder. \
Let's get into it."""),

    ("01_architecture", """\
Four layers. On the left, external signals. Gmail, WhatsApp, X, Facebook, Instagram, the filesystem, a bank \
CSV. Python watchers translate each signal into a markdown file inside an Obsidian vault. That vault is the \
entire memory and GUI of the system. \
Claude Code reads the vault, invokes Agent Skills, and writes three things: a plan, an approval file, and a \
draft. I review the approval, drag it to slash approved, and the approval watcher dispatches to an MCP \
server, which is the hands. \
Every external call writes a JSON log line and respects a rate limit."""),

    ("02_bronze", """\
This is the orchestrator. Right now a filesystem watcher, a Gmail watcher, and an approval executor are all \
running as threads in the same Python process. \
I just dropped a denial letter PDF into the Drops folder. The watcher picks it up on its next tick. \
There it is. The file moved to Inbox, and a markdown note appeared in Needs Action with a classification \
hint and a checklist of next steps. No AI ran yet; the watcher is dumb on purpose."""),

    ("03_silver", """\
The triage-inbox Agent Skill now activates. You can see it is reading Company Handbook dot md first. That is \
the rulebook with PHI policy, tone rules, and approval thresholds. \
It is classifying each item: sales, support, admin, urgent, noise. For the Cedar Health Billing pilot \
request, it just created a Plan and a Pending Approval email draft. For the HIMSS speaking invite, it \
correctly escalated. My handbook says press and speaking go to me, not the AI. \
Here is the draft. Concise, signed properly, proposes Monday ten thirty Pacific, which respects my no \
meetings before ten rule. \
That drag is the only way this email ships. No button, no status field. A physical file move. \
Approval watcher fired, the email MCP dispatched. DRY RUN stays true for email, so this is a simulated send, \
but the approval pipeline is real. You can see the full send-ready draft in the audit log. One flip of LIVE \
CHANNELS and it ships. I keep it safe for demos."""),

    ("04_gold", """\
The Sunday night scheduled task just dropped a briefing trigger into Needs Action. Now I ask Claude to run \
the ceo-briefing skill. \
This pulls financial data from the Odoo MCP, which is running locally in Docker, cross-checks Business Goals \
dot md for verified metrics, and scans last week's Done folder and audit log. \
Here is the output: one-screen executive summary, revenue, accounts receivable with days late per customer, \
my US healthcare sales pipeline, completed tasks, a bottleneck table, subscription waste. It flagged Notion \
and Loom for cancellation because I haven't logged into either in over a month. And three proactive \
suggestions in priority order. \
This is the standout feature. It takes a CEO's Monday morning from chaos to a three-bullet decision list in \
four minutes."""),

    ("05_ralph", """\
Ralph Wiggum is a Claude Code Stop hook. When Claude tries to exit, it intercepts. \
Two exit conditions: Claude emits promise triage complete in its final turn, or the Needs Action folder is \
empty. Otherwise it re-injects the prompt and Claude keeps working. \
Hard iteration cap at eight. If Ralph loops eight times without finishing, the hook approves the exit anyway \
and writes an incident file. I don't want a runaway loop at three in the morning eating my API budget. This \
is how the spec's autonomous multi-step task completion gets guardrails."""),

    ("06_platinum", """\
The delegation protocol. Cloud owns drafts. Local owns approvals and final sends. Banking credentials, \
WhatsApp session, payment tokens, those never leave my laptop. Only markdown syncs. \
This is the full flow. An email arrives while I am offline. \
Cloud agent claims by moving the file into In Progress slash cloud agent. Writes the draft to Plans slash \
email. Stages approval. And critically, it does not write to Dashboard dot md. Only local can do that. Cloud \
writes an update note to slash Updates. \
Now I come back online. Local merges the cloud update into Dashboard, I approve the draft, approval watcher \
ships it. End-to-end delegation with zero shared secrets."""),

    ("07_linkedin", """\
This is the linkedin-sales-post skill. Phase one: I post from my personal developer account only. The \
autosapien, xEHR dot io, and rcmemployee dot com pages come later in weeks. The social MCP refuses any \
non-personal brand at the server level. So a mis-prompted skill cannot leak a post to a company page that \
isn't ready yet. \
One persona named in the first line, one concrete number from a verified metric, a three-bullet mechanism, \
an honest trade-off, and a DM call to action. No emojis, no thrilled to share. \
And it is live on my personal LinkedIn, under my name, with the developer voice I chose."""),

    ("08_security", """\
Quickly. DRY RUN is the factory default. Every send-class action needs a human-moved approval file. Rate \
limits are code enforced. PHI never enters the vault. Watchers redact on ingress. Secrets live in dot env \
and slash secrets, both git-ignored, never synced to cloud. Claude Code's permission rules explicitly deny \
reads of dot env and the secrets folder. And every action writes a JSON audit line I can hand to a \
compliance reviewer."""),

    ("09_outro", """\
That is the build. Local first, HIPAA aware, judge reviewable. The repo link is below. Thanks to Panaversity \
for the framing. DM me if you're building something similar and want the architecture."""),
]


async def synth(slug: str, text: str) -> Path:
    out = OUT_DIR / f"{slug}.mp3"
    communicate = edge_tts.Communicate(text=text, voice=VOICE, rate=RATE)
    await communicate.save(str(out))
    return out


async def main() -> None:
    print(f"Voice: {VOICE}  rate: {RATE}")
    print(f"Output: {OUT_DIR}\n")
    for slug, text in SEGMENTS:
        p = await synth(slug, text)
        size_kb = p.stat().st_size / 1024
        word_count = len(text.split())
        print(f"  ok  {p.name}  ({word_count} words, {size_kb:.0f} KB)")

    # Concatenate to full.mp3 — simple byte concat works for MP3s at
    # the same bitrate, but for a clean result we would use ffmpeg.
    # For convenience we do the simple concat; players handle it.
    full = OUT_DIR / "full.mp3"
    with full.open("wb") as fout:
        for slug, _ in SEGMENTS:
            fout.write((OUT_DIR / f"{slug}.mp3").read_bytes())
    print(f"\n  ok  {full.name}  ({full.stat().st_size / 1024:.0f} KB total)")

    # Text bundle for copy-paste
    (OUT_DIR / "transcript.txt").write_text(
        "\n\n".join(f"## {s}\n{t}" for s, t in SEGMENTS),
        encoding="utf-8",
    )
    print(f"  ok  transcript.txt")

    print(f"\nTotal word count: {sum(len(t.split()) for _, t in SEGMENTS)}")
    print("Drop full.mp3 onto your OBS/DaVinci timeline and record screen silently.")


if __name__ == "__main__":
    asyncio.run(main())
