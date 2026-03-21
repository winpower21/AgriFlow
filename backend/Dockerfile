FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies into project virtual environment
RUN uv sync --frozen --no-dev

# Copy rest of application
COPY . .

# Optional documentation only
EXPOSE 8000

# Run FastAPI
CMD uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2
