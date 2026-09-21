# ==============================================================================
# Stage 1: Builder
# ==============================================================================

FROM python:3.12-slim-bookworm AS builder

# Prevent Python from writing .pyc files
# and ensure logs are immediately flushed.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Upgrade pip and build Python wheels.
RUN python -m pip install --upgrade pip

COPY requirements.txt .

RUN pip wheel \
    --no-cache-dir \
    --no-deps \
    --wheel-dir /app/wheels \
    -r requirements.txt


# ==============================================================================
# Stage 2: Runtime
# ==============================================================================

FROM python:3.12-slim-bookworm AS runner

# Runtime environment.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=9000

WORKDIR /app

# ------------------------------------------------------------------------------
# Create non-root application user and group
# ------------------------------------------------------------------------------
RUN groupadd --system appgroup \
    && useradd --system \
        --gid appgroup \
        --create-home \
        --home-dir /home/appuser \
        appuser

# ------------------------------------------------------------------------------
# Install Python dependencies
# ------------------------------------------------------------------------------
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .

RUN pip install \
        --no-cache-dir \
        /wheels/* \
    && rm -rf /wheels \
    && rm -rf /root/.cache/pip

# ------------------------------------------------------------------------------
# Copy application
# ------------------------------------------------------------------------------
COPY . /app

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Give the application user ownership of the application directory
RUN chown -R appuser:appgroup /app

# ------------------------------------------------------------------------------
# Run as non-root user
# ------------------------------------------------------------------------------
USER appuser

EXPOSE 9000

ENTRYPOINT ["/app/entrypoint.sh"]