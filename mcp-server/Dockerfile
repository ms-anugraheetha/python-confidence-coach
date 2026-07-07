# mcp-server/Dockerfile
#
# Single-stage build — the MCP server has no C extensions, so we don't
# need a separate builder stage.
#
# Build:
#   docker build -t coach-mcp .
#
# Run (env vars from .env):
#   docker run --env-file .env -p 8001:8001 coach-mcp

FROM python:3.12-slim

# Non-root user
RUN groupadd -r mcp && useradd -r -g mcp mcp

WORKDIR /app

# Copy package manifest + readme + source before install — hatchling needs
# the actual files present to build the wheel (flat layout, explicit file
# selection in pyproject.toml), so this step can't be cache-split from source.
COPY pyproject.toml README.md ./
COPY config.py ./
COPY models/ ./models/
COPY prompts/ ./prompts/
COPY tools/ ./tools/
COPY server.py ./

# Install dependencies + local package
RUN pip install --upgrade pip \
 && pip install --no-cache-dir "."

RUN chown -R mcp:mcp /app
USER mcp

# Render injects PORT; default to 8001
ENV PORT=8001

EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# MCP_HOST and MCP_PORT are read from environment in server.py
CMD ["python", "server.py"]
