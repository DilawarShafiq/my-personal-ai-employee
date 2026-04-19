# autosapien cloud-agent container.
# Builds from the repo root — context must be "../.." relative to this file.
#
# Runs scripts/cloud_agent.py which is the cloud-restricted orchestrator
# (no WhatsApp, no banking, no final sends; drafts only).
FROM python:3.11-slim-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    curl ca-certificates git \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.6.8

WORKDIR /app

# Copy dependency manifest first so pip layer caches across code changes.
COPY pyproject.toml ./
RUN uv pip install --system --no-cache \
    watchdog>=4.0 python-dotenv>=1.0 google-api-python-client>=2.120 \
    google-auth-oauthlib>=1.2 google-auth-httplib2>=0.2 httpx>=0.27 \
    pydantic>=2.6 python-dateutil>=2.9 rich>=13.7 structlog>=24.1 \
    pyyaml>=6.0 mcp>=1.0

# Copy the project into the image AFTER deps cached.
COPY watchers/ ./watchers/
COPY mcp_servers/ ./mcp_servers/
COPY orchestrator/ ./orchestrator/
COPY scripts/ ./scripts/
COPY .claude/ ./.claude/

# Non-root user — Cloud agent should never touch /secrets writably.
RUN useradd -m -u 10001 -s /bin/bash cloudagent \
 && mkdir -p /vault /secrets \
 && chown -R cloudagent:cloudagent /app /vault
USER cloudagent

ENV PYTHONUNBUFFERED=1 \
    AUTOSAPIEN_ROLE=cloud \
    VAULT_PATH=/vault \
    DRY_RUN=true

# Safety check at container start: fail-closed if role env is wrong.
CMD ["python", "-m", "scripts.cloud_agent"]
