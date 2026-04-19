"""Cloud health endpoint — 200 OK iff every subsystem is alive.

  GET /healthz  ->  aggregate health (HTTP 200 or 503)
  GET /livez    ->  simple "am I running" probe
  GET /metrics  ->  JSON: heartbeat age, vault state, Odoo reachability

Fronted by Caddy on HTTPS. Point UptimeRobot / Cloudflare Workers at
https://<DOMAIN>/healthz.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

ODOO_URL = os.getenv("ODOO_URL", "http://odoo:8069")
VAULT = Path(os.getenv("VAULT_PATH", "/vault"))

app = FastAPI(title="autosapien-cloud healthcheck")


def _orchestrator_heartbeat_age() -> float:
    hb = VAULT / ".heartbeat.cloud"
    if not hb.exists():
        hb = VAULT / ".heartbeat"  # fall back to generic
    if not hb.exists():
        return 10**9
    return time.time() - hb.stat().st_mtime


def _odoo_reachable() -> bool:
    try:
        r = httpx.get(f"{ODOO_URL}/web/login", timeout=5)
        return r.status_code < 500
    except Exception:
        return False


@app.get("/livez")
def livez() -> Response:
    return Response(content="ok", media_type="text/plain")


@app.get("/healthz")
def healthz() -> Response:
    hb_age = _orchestrator_heartbeat_age()
    odoo_ok = _odoo_reachable()
    ok = hb_age < 60 and odoo_ok

    body = {
        "ok": ok,
        "heartbeat_age_s": round(hb_age, 1),
        "odoo_reachable": odoo_ok,
    }
    return JSONResponse(content=body, status_code=200 if ok else 503)


@app.get("/metrics")
def metrics() -> Response:
    items_needs_action = 0
    items_in_progress_cloud = 0
    items_pending_approval = 0
    try:
        items_needs_action = sum(
            1 for p in (VAULT / "Needs_Action").iterdir()
            if p.suffix == ".md" and not p.name.startswith(".")
        )
        items_in_progress_cloud = sum(
            1 for p in (VAULT / "In_Progress" / "cloud-agent").iterdir()
            if p.suffix == ".md"
        ) if (VAULT / "In_Progress" / "cloud-agent").exists() else 0
        for sub in (VAULT / "Pending_Approval").rglob("*.md"):
            items_pending_approval += 1
    except Exception:
        pass

    body = {
        "heartbeat_age_s": round(_orchestrator_heartbeat_age(), 1),
        "odoo_reachable": _odoo_reachable(),
        "needs_action_count": items_needs_action,
        "in_progress_cloud_count": items_in_progress_cloud,
        "pending_approval_count": items_pending_approval,
    }
    return JSONResponse(content=body)
