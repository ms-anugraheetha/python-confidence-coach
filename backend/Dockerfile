# backend/Dockerfile
#
# Multi-stage build keeps the final image lean by separating the
# dependency installation layer from the runtime layer.
#
# Stage 1 — builder: installs all Python packages into /install
# Stage 2 — runtime: copies /install, adds source code, runs uvicorn
#
# Build:
#   docker build -t coach-backend .
#
# Run (dev-like, env vars from .env):
#   docker run --env-file .env -p 8000:8000 coach-backend

# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install build tools needed for some packages (e.g. psycopg's C extension)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy the package manifest + README first to leverage Docker layer caching.
# (hatchling requires README.md to exist when building wheel metadata —
# pyproject.toml declares readme = "README.md", so it must be present here.)
COPY pyproject.toml README.md ./

# Install the package in non-editable mode into an isolated prefix.
# Using --no-build-isolation is NOT set — we want the full build chain.
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir "."


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Runtime deps only (libpq for asyncpg's binary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source code (everything except what's in .dockerignore)
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Change ownership so the non-root user can read/write
RUN chown -R app:app /app
USER app

# Render and most PaaS providers inject PORT; fall back to 8000
ENV PORT=8000

# Expose for documentation purposes (PaaS ignores this but it's useful locally)
EXPOSE $PORT

# Health check — hits our /health endpoint every 30 s
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

# Start uvicorn.
# --host 0.0.0.0  → listen on all interfaces (required in containers)
# --workers 1     → single worker; increase via env var on Render
# Note: app/core/config.py requires LOG_LEVEL uppercase (DEBUG/INFO/...),
# but uvicorn's CLI --log-level flag requires lowercase — lowercase it
# here just for uvicorn, independent of what's stored in the env var.
CMD uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers "${UVICORN_WORKERS:-1}" \
    --log-level "$(echo "${LOG_LEVEL:-info}" | tr 'A-Z' 'a-z')"
