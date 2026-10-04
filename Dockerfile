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
    PYTHONDONTWRITEBYTECODE=1 \
    AWS_REGION=us-east-2 \
    LIFESIZE_WARM_UP=0 \
    DATABASE_URL=sqlite:////tmp/lifesize.db

EXPOSE 8000

# A single self-contained process with no files outside /tmp, so it starts in any sandbox.
CMD ["python", "-m", "flask", "--app", "wsgi", "run", "--host", "0.0.0.0", "--port", "8000"]
