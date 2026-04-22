# syntax=docker/dockerfile:1.7

# ---------- Stage 1: backend venv ----------
FROM python:3.11-slim AS backend-builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY backend/pyproject.toml ./

# The repo's uv.lock is scoped to macOS (see [tool.uv] environments in
# pyproject.toml), so resolve fresh from pyproject.toml dependencies on Linux.
RUN python -m venv /app/backend/.venv
ENV PATH="/app/backend/.venv/bin:$PATH"
RUN python -c "import tomllib; d=tomllib.loads(open('pyproject.toml').read()); print('\n'.join(d['project']['dependencies']))" > /tmp/requirements.txt \
 && pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /tmp/requirements.txt


# ---------- Stage 2: frontend standalone build ----------
FROM node:22-alpine AS frontend-builder

RUN corepack enable

WORKDIR /app/frontend

COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend/ ./

# Empty string -> fetch(`${API_URL}/validate`) becomes same-origin `/validate`,
# which next.config.ts rewrites to the backend inside the container.
ENV NEXT_PUBLIC_API_URL=
RUN pnpm build


# ---------- Stage 3: runtime (Python 3.11 + Node 22) ----------
FROM python:3.11-slim AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates tini gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && apt-get purge -y gnupg \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend: venv from builder + source tree
COPY --from=backend-builder /app/backend/.venv /app/backend/.venv
COPY backend/ /app/backend/
ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Frontend: Next.js standalone output + static assets + public/
COPY --from=frontend-builder /app/frontend/.next/standalone /app/frontend
COPY --from=frontend-builder /app/frontend/.next/static /app/frontend/.next/static
COPY --from=frontend-builder /app/frontend/public /app/frontend/public

COPY docker/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

ENV HOSTNAME=0.0.0.0 \
    FRONTEND_PORT=3000 \
    BACKEND_HOST=127.0.0.1 \
    BACKEND_PORT=8000

EXPOSE 3000
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/start.sh"]
