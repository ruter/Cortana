# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN python -m pip install --upgrade pip \
 && python -m pip install -r requirements.txt

# Copy project files
COPY pyproject.toml README.md ./
COPY mcp_servers.example.json mcp_servers.json
COPY src/ ./src/
COPY tests/ ./tests/

# Install the package itself
RUN python -m pip install -e .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
 && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import assistant_bot; print('OK')" || exit 1

CMD ["python", "-m", "assistant_bot.bot"]
