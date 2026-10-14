# Stage 1 (base): Python, our libraries and the app code. Shared by the stages below.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations

# Stage 2 (test): base plus test tools and tests. Only used by "docker compose --profile test".
FROM base AS test

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY pytest.ini ./
COPY tests ./tests

USER appuser

CMD ["pytest"]

# Stage 3 (production): what really runs. No test tools inside. This is the default stage.
FROM base AS production

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
