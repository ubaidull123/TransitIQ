# Stage 1 — build the React intake console
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


# Stage 2 — FastAPI app + agent
FROM python:3.13-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8765

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

COPY --from=frontend /build/dist ./frontend/dist

EXPOSE 8765

CMD ["/app/.venv/bin/transitiq-api"]
