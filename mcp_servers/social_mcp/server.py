"""Unified social MCP — X (Twitter), Facebook, Instagram, LinkedIn.

One MCP server, three tool families, one consistent approval gate. Each
tool ends up in the same shape:
  * `*_draft`  — safe, always allowed, writes a /Pending_Approval note.
  * `*_post`   — requires a matching /Approved file; rate-limited; DRY_RUN aware.

LinkedIn uses the Playwright session captured earlier
(`scripts/capture_linkedin_session.py`). X uses v2 API via httpx + OAuth1.
Facebook/Instagram use Meta Graph API long-lived page tokens.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

SERVER_NAME = "autosapien-social"
VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()
APPROVED = VAULT / "Approved"
LOGS = VAULT / "Logs"
LIMITS = VAULT / ".limits"
LIMITS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
MAX_POSTS_PER_DAY = int(os.getenv("MAX_SOCIAL_POSTS_PER_DAY", "6"))

server: Server = Server(SERVER_NAME)


# --- shared helpers ----------------------------------------------------------
def _audit(event: dict[str, Any]) -> None:
    event.setdefault("timestamp", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    event.setdefault("actor", "social_mcp")
    log_file = LOGS / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _rate_limit_ok(channel: str) -> bool:
    counter = LIMITS / f"{channel}_posts_day.json"
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data = {"day": day, "count": 0}
    if counter.exists():
        data = json.loads(counter.read_text())
        if data.get("day") != day:
            data = {"day": day, "count": 0}
    if data["count"] >= MAX_POSTS_PER_DAY:
        return False
    data["count"] += 1
    counter.write_text(json.dumps(data))
    return True


def _approval_ok(prefix: str, slug: str) -> bool:
    return bool(list(APPROVED.glob(f"{prefix}_{slug}*.md")))


# --- tool definitions --------------------------------------------------------
@server.list_tools()
async def list_tools() -> list[Tool]:
    base_post_schema = {
        "type": "object",
        "properties": {
            "slug": {"type": "string", "description": "Same slug used in /Approved/ filename."},
            "content": {"type": "string"},
            "brand": {
                "type": "string",
                "enum": ["personal_dilawar", "autosapien", "xehr", "rcmemployee"],
                "default": "personal_dilawar",
                "description": "Phase 1: always personal_dilawar — product pages are not active yet.",
            },
        },
        "required": ["slug", "content"],
    }
    return [
        Tool(name="x_post",
             description="Post to X (Twitter). Requires /Approved/X_<slug>.md. Rate-limited.",
             inputSchema=base_post_schema),
        Tool(name="facebook_post",
             description="Post to Facebook Page. Requires /Approved/FACEBOOK_<slug>.md.",
             inputSchema=base_post_schema),
        Tool(name="instagram_post",
             description="Post to Instagram Business. Image required. Uses Graph API.",
             inputSchema={
                 "type": "object",
                 "properties": {
                     "slug": {"type": "string"},
                     "caption": {"type": "string"},
                     "image_url": {"type": "string", "description": "Publicly reachable URL."},
                 },
                 "required": ["slug", "caption", "image_url"],
             }),
        Tool(name="linkedin_post",
             description="Post to LinkedIn via captured Playwright session. "
             "Requires /Approved/LINKEDIN_<slug>.md.",
             inputSchema=base_post_schema),
        Tool(name="social_weekly_summary",
             description="Generate a cross-channel summary of what was posted this week. "
             "Pure read — safe, no approval needed.",
             inputSchema={"type": "object", "properties": {}}),
    ]


# --- tool implementations ----------------------------------------------------
def _do_x_post(content: str) -> dict:
    if DRY_RUN:
        return {"posted": True, "dry_run": True, "platform": "x",
                "preview": content[:160]}
    import tweepy  # type: ignore[import-not-found]

    auth = tweepy.OAuth1UserHandler(
        os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"],
    )
    api = tweepy.API(auth)
    status = api.update_status(status=content[:280])
    return {"posted": True, "tweet_id": status.id_str}


def _do_facebook_post(content: str) -> dict:
    if DRY_RUN:
        return {"posted": True, "dry_run": True, "platform": "facebook"}
    page_id = os.environ["META_PAGE_ID"]
    token = os.environ["META_LONG_LIVED_TOKEN"]
    r = httpx.post(f"https://graph.facebook.com/v21.0/{page_id}/feed",
                   data={"message": content, "access_token": token}, timeout=30)
    r.raise_for_status()
    return {"posted": True, **r.json()}


def _do_instagram_post(caption: str, image_url: str) -> dict:
    if DRY_RUN:
        return {"posted": True, "dry_run": True, "platform": "instagram"}
    ig_user = os.environ["META_IG_USER_ID"]
    token = os.environ["META_LONG_LIVED_TOKEN"]
    container = httpx.post(
        f"https://graph.facebook.com/v21.0/{ig_user}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
        timeout=30,
    ).json()
    published = httpx.post(
        f"https://graph.facebook.com/v21.0/{ig_user}/media_publish",
        data={"creation_id": container["id"], "access_token": token},
        timeout=30,
    ).json()
    return {"posted": True, **published}


def _do_linkedin_post(content: str) -> dict:
    from mcp_servers.linkedin_poster import post as lp

    ok = lp(content, dry_run=DRY_RUN)
    return {"posted": ok, "dry_run": DRY_RUN, "platform": "linkedin"}


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    channel_map = {
        "x_post": ("x", "X", "content"),
        "facebook_post": ("facebook", "FACEBOOK", "content"),
        "instagram_post": ("instagram", "INSTAGRAM", None),
        "linkedin_post": ("linkedin", "LINKEDIN", "content"),
    }

    if name in channel_map:
        channel, prefix, content_key = channel_map[name]
        slug = arguments.get("slug", "")
        brand = arguments.get("brand", "personal_dilawar")
        # Phase-1 guardrail: only personal_dilawar is live. Refuse product/company
        # brand posts at the MCP layer so a mis-routed skill can't leak a post.
        if brand != "personal_dilawar":
            _audit({"action_type": f"{channel}_post", "result": "brand_not_live",
                    "parameters": {"slug": slug, "brand": brand}})
            return [TextContent(
                type="text",
                text=f"REFUSED: brand '{brand}' is not live yet (phase 1 = personal_dilawar only).",
            )]
        if not _approval_ok(prefix, slug):
            _audit({"action_type": f"{channel}_post", "result": "denied_no_approval",
                    "parameters": {"slug": slug}})
            return [TextContent(type="text",
                                text=f"REFUSED: no /Approved/{prefix}_{slug}*.md")]
        if not _rate_limit_ok(channel):
            _audit({"action_type": f"{channel}_post", "result": "rate_limited",
                    "parameters": {"slug": slug}})
            return [TextContent(type="text", text="REFUSED: rate limit (posts/day).")]

        try:
            if name == "x_post":
                result = _do_x_post(arguments["content"])
            elif name == "facebook_post":
                result = _do_facebook_post(arguments["content"])
            elif name == "instagram_post":
                result = _do_instagram_post(arguments["caption"], arguments["image_url"])
            else:
                result = _do_linkedin_post(arguments["content"])
        except Exception as e:  # noqa: BLE001
            _audit({"action_type": f"{channel}_post", "result": "error",
                    "error": str(e), "parameters": {"slug": slug}})
            return [TextContent(type="text", text=f"ERROR: {e}")]

        _audit({"action_type": f"{channel}_post",
                "result": "dry_run" if DRY_RUN else "success",
                "parameters": {"slug": slug, **result},
                "approval_status": "approved", "approved_by": "human"})
        return [TextContent(type="text", text=json.dumps(result))]

    if name == "social_weekly_summary":
        # Summarize this week's audit entries for posts.
        from datetime import timedelta
        start = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
        counts: dict[str, int] = {"x": 0, "facebook": 0, "instagram": 0, "linkedin": 0}
        for log_path in sorted(LOGS.glob("*.jsonl")):
            if log_path.stem < start:
                continue
            for line in log_path.read_text().splitlines():
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                at = entry.get("action_type", "")
                if at.endswith("_post") and entry.get("result") in ("success", "dry_run"):
                    channel = at.rsplit("_post", 1)[0]
                    counts[channel] = counts.get(channel, 0) + 1
        return [TextContent(type="text", text=json.dumps({"week_start": start, "posts": counts}))]

    return [TextContent(type="text", text=f"ERROR: unknown tool '{name}'")]


async def _run() -> None:
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


def main() -> None:
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()
