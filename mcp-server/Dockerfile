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

# Copy package manifest + readme first for layer caching
# (hatchling requires README.md to exist when building wheel metadata)
COPY pyproject.toml README.md ./

# Install dependencies
RUN pip install --upgrade pip \
 && pip install --no-cache-dir "."

# Copy source code
COPY models/ ./models/
COPY prompts/ ./prompts/
COPY tools/ ./tools/
COPY server.py ./

RUN chown -R mcp:mcp /app
USER mcp

# Render injects PORT; default to 8001
ENV PORT=8001

EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# MCP_HOST and MCP_PORT are read from environment in server.py
CMD ["python", "server.py"]
