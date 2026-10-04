FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
WORKDIR /app

# Dependencies first, so code changes do not reinstall them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

COPY . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    DATABASE_URL=sqlite:////data/app.db

RUN useradd --create-home app && mkdir /data && chown app /data
USER app
VOLUME /data
EXPOSE 8000

# One worker process: SQLite has a single writer, and requests are I/O-bound (threads).
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--timeout", "60", "wsgi:app"]
