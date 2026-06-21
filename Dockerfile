# ── Glas MCP — Dockerfile ──────────────────────────────────────────────────────
# Multi-stage build: install heavy deps in builder, copy to slim runtime image.
# Non-root user for security. Health check included.
#
# Build:   docker build -t glas-mcp .
# Run:     docker run -p 8000:8000 --env-file .env glas-mcp
# Compose: docker-compose up
# ──────────────────────────────────────────────────────────────────[...]

# ── Stage 1: Builder ──────────────────────────────────────────────────────────[...]
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps for WeasyPrint (PDF generation) and other tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libxml2 \
    libxslt1.1 \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY glas_mcp/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────[...]
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="Glas MCP"
LABEL org.opencontainers.image.description="Modular MCP server — web, math, charts, documents"
LABEL org.opencontainers.image.source="https://github.com/anguzudouglas/glas_mcp"
LABEL org.opencontainers.image.version="1.0.0"
LABEL maintainer="Anguzudouglas"

# Runtime system deps (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libxml2 \
    libxslt1.1 \
    fonts-liberation \
    fonts-dejavu \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user
RUN groupadd -r glas && useradd -r -g glas -d /app -s /sbin/nologin glas

WORKDIR /app

# Copy project files
COPY --chown=glas:glas . .

# Create output directories (tools write files here)
RUN mkdir -p /app/generated_docs /app/generated_pdfs && \
    chown -R glas:glas /app/generated_docs /app/generated_pdfs

USER glas

# Environment defaults (override via --env-file or -e)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    DEV=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8000

# Health check — probe the /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["python", "main.py"]
