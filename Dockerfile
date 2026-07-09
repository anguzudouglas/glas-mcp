# ── Stage 1: Build React frontend ─────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install deps first (cached if package.json unchanged)
# Using npm install (not npm ci) since no package-lock.json is committed
COPY frontend/package.json ./
RUN npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build
# Output → /app/glas_mcp/static  (via vite.config.js outDir)


# ── Stage 2: Python backend ────────────────────────────────────
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY glas_mcp/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY glas_mcp/ ./glas_mcp/
COPY main.py ./

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/glas_mcp/static ./glas_mcp/static

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["python", "main.py"]
