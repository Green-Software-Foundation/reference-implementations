# syntax=docker/dockerfile:1.7
#
# Multi-stage build. The principles here are themselves green-software
# guidance: small images cut network transfer, faster cold starts cut
# idle energy, and excluding build tooling from the runtime layer cuts
# the resident attack surface and disk usage.
#
# Final image size target: ~80 MB (python:3.12-slim + our code).

# ---------- Stage 1: build ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tooling only in this stage.
RUN pip install --no-cache-dir --upgrade pip build

COPY pyproject.toml README.md ./
COPY src ./src

# Build the wheel.
RUN python -m build --wheel --outdir /wheels


# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

# Non-root user — small but standard security & ops hygiene.
RUN groupadd --system app && useradd --system --gid app --create-home app
USER app
WORKDIR /home/app

# Copy and install the wheel from the build stage. No build tooling in runtime.
COPY --from=builder /wheels/*.whl /tmp/
RUN pip install --no-cache-dir --user /tmp/*.whl && rm /tmp/*.whl

# Ensure pip --user bin dir is on PATH.
ENV PATH=/home/app/.local/bin:$PATH

# Pre-set sensible defaults; override at runtime.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8

ENTRYPOINT ["sci-for-ai"]
CMD ["--help"]
