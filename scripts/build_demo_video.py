"""Build the full demo MP4 from the pre-generated narration.

Pipeline:
  1. Render 10 HTML slides to 1920x1080 PNG (Chrome headless)
  2. Combine each slide PNG + its MP3 into a segment MP4 (ffmpeg)
  3. Concat all segment MP4s into docs/rendered/demo_video.mp4

Output: docs/rendered/demo_video.mp4 (ready to upload to YouTube)

Usage:
    uv run python scripts/build_demo_video.py

Requires:
    - ffmpeg in PATH
    - Chrome installed at C:/Program Files/Google/Chrome/Application/chrome.exe
    - Narration MP3s generated via scripts/generate_narration.py
    - Intro + outro PNGs via scripts/render_cards.ps1
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
NARRATION_DIR = ROOT / "docs" / "rendered" / "narration"
SLIDES_DIR = ROOT / "docs" / "rendered" / "slides"
SEGMENTS_DIR = ROOT / "docs" / "rendered" / "segments"
OUT_DIR = ROOT / "docs" / "rendered"
INTRO_PNG = OUT_DIR / "intro_card.png"
OUTRO_PNG = OUT_DIR / "outro_card.png"
CHROME = Path(r"C:/Program Files/Google/Chrome/Application/chrome.exe")

SLIDES_DIR.mkdir(parents=True, exist_ok=True)
SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)


BASE_CSS = dedent("""\
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

    html, body {
        margin: 0;
        padding: 0;
        width: 1920px;
        height: 1080px;
        overflow: hidden;
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
        font-family: 'Inter', -apple-system, sans-serif;
        color: #f8fafc;
    }
    .stage {
        width: 100%;
        height: 100%;
        position: relative;
        box-sizing: border-box;
        padding: 72px 96px;
    }
    .top-bar, .bottom-bar {
        position: absolute;
        left: 0; right: 0;
        height: 6px;
        background: linear-gradient(90deg, #7c3aed, #06b6d4);
    }
    .top-bar { top: 0; }
    .bottom-bar { bottom: 0; }
    h1 {
        font-size: 68px; font-weight: 700; margin: 0 0 20px 0;
        color: #f8fafc;
    }
    h2 {
        font-size: 32px; font-weight: 400; margin: 0 0 40px 0;
        color: #a5b4fc;
    }
    .code {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 36px 44px;
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 22px;
        line-height: 1.6;
        color: #e2e8f0;
        overflow: hidden;
        white-space: pre;
    }
    .code .c  { color: #94a3b8; font-style: italic; }       /* comment */
    .code .k  { color: #c4b5fd; }                            /* keyword */
    .code .s  { color: #86efac; }                            /* string */
    .code .h  { color: #06b6d4; }                            /* highlight */
    .code .e  { color: #fca5a5; }                            /* error/warn */
    .kpi {
        display: flex; gap: 40px; margin-top: 32px;
    }
    .kpi .box {
        flex: 1;
        background: #1e293b;
        border: 1px solid #475569;
        border-radius: 14px;
        padding: 28px 36px;
    }
    .kpi .label { font-size: 18px; color: #94a3b8; margin-bottom: 8px; }
    .kpi .value { font-size: 44px; font-weight: 700; color: #06b6d4; }
    .kpi .value.purple { color: #c4b5fd; }
    .kpi .sub { font-size: 16px; color: #64748b; margin-top: 6px; }
    .footer {
        position: absolute;
        bottom: 28px;
        left: 96px;
        font-size: 18px;
        color: #64748b;
    }
    .chip {
        display: inline-block;
        padding: 8px 22px;
        border-radius: 999px;
        background: rgba(124, 58, 237, 0.18);
        border: 2px solid #7c3aed;
        color: #c4b5fd;
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 22px;
    }
    """)


def slide_html(title_chip: str, h1: str, h2: str, body: str, footer: str = "autosapien · Personal AI Employee · Panaversity Hackathon 0") -> str:
    return dedent(f"""\
        <!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}</style></head>
        <body><div class="stage">
          <div class="top-bar"></div>
          <div class="chip">{title_chip}</div>
          <h1>{h1}</h1>
          <h2>{h2}</h2>
          {body}
          <div class="footer">{footer}</div>
          <div class="bottom-bar"></div>
        </div></body></html>""")


# ----------------------------------------------------------------------------
#  10 slide definitions
# ----------------------------------------------------------------------------

SLIDES = {}

# 00 - intro (use pre-rendered card)
SLIDES["00_intro"] = None   # use INTRO_PNG directly

# 01 - architecture
SLIDES["01_architecture"] = slide_html(
    "Architecture",
    "Four layers, one markdown vault",
    "Perception -> Memory -> Reasoning -> Action",
    """
    <div class="code"><span class="c">#  The four-layer architecture</span>

  <span class="h">EXTERNAL</span>      Gmail · WhatsApp · X · FB · IG · Files · Bank CSV
       |
       v
  <span class="h">WATCHERS</span>      Python sentinels. PHI redaction on ingress.
       |  writes markdown
       v
  <span class="h">VAULT</span>         Obsidian. Memory + GUI in one filesystem.
       |
       v
  <span class="h">CLAUDE</span>        Agent Skills + Ralph Wiggum Stop hook.
       |  drops approval files
       v
  <span class="h">HUMAN</span>         Drags file to /Approved — that's the signal.
       |
       v
  <span class="h">MCP</span>           email · odoo · social  (DRY_RUN-safe, rate-limited)

  <span class="c">#  Every action writes JSONL. Every secret stays local.</span></div>
    """,
)

# 02 - bronze
SLIDES["02_bronze"] = slide_html(
    "Bronze tier",
    "Watchers wake the agent",
    "Drop a file. No click. A vault note appears.",
    """
    <div class="code"><span class="c">$ uv run autosapien-orchestrator</span>
<span class="s">2026-04-19T07:58:00Z [info] orchestrator.boot</span>
<span class="s">2026-04-19T07:58:00Z [info] orchestrator.watcher.started name=<span class="h">filesystem</span></span>
<span class="s">2026-04-19T07:58:00Z [info] orchestrator.watcher.started name=<span class="h">gmail</span></span>
<span class="s">2026-04-19T07:58:00Z [info] orchestrator.watcher.started name=<span class="h">approval</span></span>

<span class="c"># (drop denial_letter.pdf into AI_Employee_Vault/Drops/)</span>

<span class="s">2026-04-19T07:59:12Z [info] watcher.write</span>
  watcher=filesystem
  path=<span class="h">Needs_Action/FILE_denial_letter_....md</span>

<span class="c"># Vault now contains:</span>
AI_Employee_Vault/
├── Inbox/<span class="h">denial_letter.pdf</span>           <span class="c"># moved here</span>
├── Needs_Action/
│   └── <span class="h">FILE_denial_letter_....md</span>   <span class="c"># YAML + suggested actions</span>
└── ...</div>
    """,
)

# 03 - silver
SLIDES["03_silver"] = slide_html(
    "Silver tier",
    "Claude triages. Human approves. MCP ships.",
    "Drag is the only signal. No buttons.",
    """
    <div class="code"><span class="c">$ claude  "triage my inbox"</span>

  <span class="k">Read</span>  Company_Handbook.md (rules first, always)
  <span class="k">Classify</span>  5 items ->
     cedar_pilot_kickoff     : sales
     valley_billing_invoice  : admin
     harbor_psych_urgent     : support
     himss_speaking_invite   : <span class="e">escalate to human (handbook § 7)</span>
     newsletter              : noise -> /Done

  <span class="k">Draft</span>  /Pending_Approval/EMAIL_cedar_pilot_kickoff.md
  <span class="k">Plan</span>   /Plans/PLAN_cedar_pilot_kickoff.md

<span class="c"># Dilawar drags EMAIL_cedar_pilot_kickoff.md -> /Approved/</span>

<span class="s">2026-04-19T08:03:22Z [info] approval.dispatch  action=send_email</span>
<span class="s">2026-04-19T08:03:22Z [info] approval.email_dry_run to=jruiz@cedar...</span>

<span class="c"># /Logs/2026-04-19.jsonl audit line:</span>
{<span class="k">"action_type"</span>:<span class="s">"email_send"</span>, <span class="k">"result"</span>:<span class="s">"dry_run"</span>,
 <span class="k">"approval_status"</span>:<span class="s">"approved"</span>, <span class="k">"approved_by"</span>:<span class="s">"human"</span>}</div>
    """,
)

# 04 - gold (CEO Briefing)
SLIDES["04_gold"] = slide_html(
    "Gold tier",
    "Monday Morning CEO Briefing",
    "Live Odoo numbers. Three proactive suggestions.",
    """
    <div class="kpi">
      <div class="box"><div class="label">Collected MTD</div>
        <div class="value">$14,835</div>
        <div class="sub">from live Odoo — 4 paid invoices</div></div>
      <div class="box"><div class="label">Bookings MTD</div>
        <div class="value purple">$17,595</div>
        <div class="sub">{percent}% of $35K Q2 target</div></div>
      <div class="box"><div class="label">AR Outstanding</div>
        <div class="value">2</div>
        <div class="sub">Lakeshore 6d late · Valley 0d</div></div>
    </div>
    <div class="code" style="margin-top: 28px;"><span class="c">#  Proactive suggestions (top 3):</span>
  1. <span class="h">Send Lakeshore chase today</span> -- 20 days overdue, draft staged.
  2. <span class="h">Lock Cedar kickoff</span> before counsel adds redlines.
  3. <span class="h">Kill Notion + Loom</span> subscriptions ($33/mo × 12 = $396/yr).

  Approvals waiting: EMAIL_lakeshore_chase · EMAIL_cedar_pilot_kickoff
                     CANCEL_Notion · CANCEL_Loom · LINKEDIN · OUTREACH</div>
    """.replace("{percent}", "50"),
)

# 05 - ralph
SLIDES["05_ralph"] = slide_html(
    "Ralph Wiggum",
    "Autonomy with guardrails",
    "Two exit conditions. Hard iteration cap. No runaway loops.",
    """
    <div class="code"><span class="c"># .claude/settings.json</span>
"hooks": {
  "Stop": [{
    "matcher": "",
    "hooks": [{
      "type": "command",
      "shell": "bash",
      "command": <span class="s">"./.claude/hooks/ralph_stop.sh"</span>
    }]
  }]
}

<span class="c"># .claude/hooks/ralph_stop.sh</span>
<span class="c"># Exit condition 1 -- Claude emitted the promise:</span>
  if echo "$INPUT" | grep -E '&lt;promise&gt;[A-Z_]*_COMPLETE&lt;/promise&gt;'; then
    echo '{"decision": "approve"}'; exit 0
  fi

<span class="c"># Exit condition 2 -- Needs_Action folder is empty:</span>
  if [ "$(find $VAULT/Needs_Action -name '*.md' | wc -l)" = "0" ]; then
    echo '{"decision": "approve"}'; exit 0
  fi

<span class="c"># Otherwise: block the stop, re-inject the prompt.</span>
<span class="c"># Hard cap at 8 iterations -- no 3am API budget runaway.</span></div>
    """,
)

# 06 - platinum
SLIDES["06_platinum"] = slide_html(
    "Platinum-lite",
    "Cloud drafts. Local approves.",
    "Same git-synced vault. Secrets never leave the laptop.",
    """
    <div class="code"><span class="c">$ uv run python scripts/platinum_demo.py</span>

  [Gmail watcher on Cloud] new email from Harbor Family Clinic

  <span class="k">== CLOUD agent turn ==</span>
  [cloud] claimed <span class="h">In_Progress/cloud-agent/EMAIL_...md</span>
  [cloud] drafted Plans/email/PLAN_....md
  [cloud] staged <span class="h">Pending_Approval/email/EMAIL_....md</span>
  [cloud] wrote update Updates/...cloud.md
  [cloud]  <span class="e">NEVER wrote to Dashboard.md — single-writer rule.</span>

  <span class="c"># git push -> git pull ->  human opens Obsidian</span>

  <span class="k">== LOCAL agent turn ==</span>
  [human]  moved EMAIL_... -> /Approved/
  [local]  merged Cloud update into Dashboard.md
  [local]  approval_watcher fired; Done/ has: <span class="s">True</span>

  <span class="c"># Secrets (.env, linkedin_session, banking creds) never synced.</span></div>
    """,
)

# 07 - LinkedIn
SLIDES["07_linkedin"] = slide_html(
    "LinkedIn — developer voice",
    "Personal brand only. Server-enforced.",
    "One persona, one metric, one DM call to action.",
    """
    <div class="code"><span class="c"># /Pending_Approval/LINKEDIN_agentic_hipaa_watchers.md</span>

If you're the CTO or lead engineer at a small healthcare billing
company, this is for you.

The pattern I ship with rcmemployee.com does four things, in order:

  1. A <span class="h">watcher</span> classifies payer remit codes on ingress.
  2. A <span class="h">skill</span> drafts an appeal letter per remit-code class.
  3. An <span class="h">MCP server</span> submits to the clearinghouse in dry-run.
  4. A <span class="h">human approval</span> is required for any new payer.

Honest trade-off: we lag ~15 min vs a human hitting F5. In exchange,
denial overturn rate went from 48% -> <span class="h">63%</span> last month.

If you're building something similar and want the architecture, DM me.

<span class="c"># social MCP refuses any brand != personal_dilawar (phase 1).</span></div>
    """,
)

# 08 - security
SLIDES["08_security"] = slide_html(
    "Security",
    "DRY_RUN is the factory default",
    "Five guardrails, code-level not doc-level.",
    """
    <div class="code"><span class="c"># .env.example</span>
<span class="k">DRY_RUN</span>=<span class="s">true</span>                              <span class="c"># switch (default ON)</span>
<span class="k">LIVE_CHANNELS</span>=                           <span class="c"># per-channel opt-out of dry</span>
<span class="k">MAX_EMAILS_PER_HOUR</span>=<span class="s">10</span>                   <span class="c"># enforced by email MCP</span>
<span class="k">MAX_SOCIAL_POSTS_PER_DAY</span>=<span class="s">6</span>               <span class="c"># enforced by social MCP</span>
<span class="k">MAX_PAYMENTS_PER_DAY</span>=<span class="s">3</span>

<span class="c"># .claude/settings.json  (permissions)</span>
"deny": [
  <span class="s">"Read(./.env)"</span>,                         <span class="c"># Claude cannot read secrets</span>
  <span class="s">"Read(./secrets/**)"</span>,                    <span class="c"># hard block at the tool layer</span>
  <span class="s">"Write(./.env)"</span>, <span class="s">"Write(./secrets/**)"</span>,
  <span class="s">"Bash(curl * | sh)"</span>, <span class="s">"Bash(rm -rf *)"</span>
]

<span class="c"># PHI policy (Company_Handbook.md § 1)</span>
  Watchers redact MRN/SSN/claim-IDs <span class="h">on ingress</span>.
  Vault contains headers + 150-char snippet. Full body stays in Gmail.
  Every action writes a JSONL audit line to Logs/YYYY-MM-DD.jsonl.</div>
    """,
)

# 09 - outro (use pre-rendered card)
SLIDES["09_outro"] = None   # use OUTRO_PNG directly


# ----------------------------------------------------------------------------
#  Pipeline
# ----------------------------------------------------------------------------

def render_html_to_png(html: str, out_png: Path) -> None:
    tmp_html = out_png.with_suffix(".html")
    tmp_html.write_text(html, encoding="utf-8")
    url = "file:///" + str(tmp_html).replace("\\", "/")
    subprocess.run([
        str(CHROME),
        "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--window-size=1920,1080",
        f"--screenshot={out_png}",
        url,
    ], check=True, capture_output=True)
    tmp_html.unlink(missing_ok=True)


def combine_png_and_mp3(png: Path, mp3: Path, out_mp4: Path) -> None:
    """Build a segment MP4: still image for duration of audio."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "30",
        "-i", str(png),
        "-i", str(mp3),
        "-c:v", "libx264", "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0a0e27",
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:])
        raise RuntimeError(f"ffmpeg failed for {out_mp4.name}")


def concat_mp4s(segments: list[Path], out_mp4: Path) -> None:
    """Concat the segments via ffmpeg concat demuxer."""
    listfile = out_mp4.with_suffix(".concat.txt")
    listfile.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in segments) + "\n",
        encoding="utf-8",
    )
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(listfile),
        "-c", "copy",
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:])
        raise RuntimeError("ffmpeg concat failed")
    listfile.unlink(missing_ok=True)


def main() -> None:
    print("Step 1/3  Rendering slides (Chrome headless)...")
    for slug, html in SLIDES.items():
        png = SLIDES_DIR / f"{slug}.png"
        if slug == "00_intro":
            shutil.copy2(INTRO_PNG, png)
        elif slug == "09_outro":
            shutil.copy2(OUTRO_PNG, png)
        else:
            render_html_to_png(html, png)
        print(f"  ok  {png.name}  ({png.stat().st_size / 1024:.0f} KB)")

    print("\nStep 2/3  Building MP4 segments (ffmpeg)...")
    segments: list[Path] = []
    for slug in SLIDES:
        png = SLIDES_DIR / f"{slug}.png"
        mp3 = NARRATION_DIR / f"{slug}.mp3"
        if not mp3.exists():
            print(f"  SKIP  {slug} (no audio)")
            continue
        mp4 = SEGMENTS_DIR / f"{slug}.mp4"
        combine_png_and_mp3(png, mp3, mp4)
        print(f"  ok  {mp4.name}  ({mp4.stat().st_size / 1024 / 1024:.1f} MB)")
        segments.append(mp4)

    print("\nStep 3/3  Concatenating final video...")
    final = OUT_DIR / "demo_video.mp4"
    concat_mp4s(segments, final)
    size_mb = final.stat().st_size / 1024 / 1024
    print(f"  ok  {final.relative_to(ROOT)}  ({size_mb:.1f} MB)")

    # Show duration via ffprobe
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(final)],
        capture_output=True, text=True,
    )
    try:
        secs = float(r.stdout.strip())
        mm, ss = divmod(int(secs), 60)
        print(f"  duration: {mm}:{ss:02d}")
    except ValueError:
        pass

    print("\nDone. Upload demo_video.mp4 to YouTube Unlisted.")


if __name__ == "__main__":
    main()
