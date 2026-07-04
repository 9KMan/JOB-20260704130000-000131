# Multi-stage Dockerfile for the lovable-audit CLI.
# The image is intentionally small (slim base, single Python file).

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy ONLY the package and its metadata; install in editable mode.
COPY pyproject.toml README.md /app/
COPY lovable_audit /app/lovable_audit

RUN pip install --no-cache-dir -e .

# Copy the rest of the repo so the CLI can find templates/, etc.
COPY templates /app/templates
COPY diagrams /app/diagrams
COPY scripts /app/scripts
COPY fixtures /app/fixtures

# Smoke-test that the CLI is importable.
RUN lovable-audit --version

# Default: print help. Override with `docker run ... lovable-audit <path>`.
ENTRYPOINT ["lovable-audit"]
CMD ["--help"]
