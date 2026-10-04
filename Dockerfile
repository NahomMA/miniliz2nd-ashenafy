# LifeSize API. Build from the repository root:  docker build -t lifesize .
# Run:  docker run -p 8000:8000 lifesize        then open http://localhost:8000/health
#
# It starts with no configuration. Without AWS_BEARER_TOKEN_BEDROCK the chat uses the built-in
# scripted interview and the calculator works as normal. To use the live models:
#   docker run -p 8000:8000 -e AWS_BEARER_TOKEN_BEDROCK=<key> -e BEDROCK_GUARDRAIL_ID= lifesize
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
WORKDIR /app

# Dependencies first, so code changes do not reinstall them.
COPY back-end/pyproject.toml back-end/uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

COPY back-end/ .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    AWS_REGION=us-east-2 \
    DATABASE_URL=sqlite:////data/app.db

RUN useradd --create-home app && mkdir /data && chown app /data
USER app
VOLUME /data
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# One worker process: SQLite has a single writer, and requests are I/O-bound (threads).
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--timeout", "60", "wsgi:app"]
