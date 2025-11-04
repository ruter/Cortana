# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim AS base

ENV POETRY_VERSION=1.8.3 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project metadata first for dependency installation
COPY pyproject.toml README.md requirements.txt .env.example mcp_servers.example.json ./
COPY src ./src
COPY tests ./tests

# Rename the example config file
RUN mv .env.example .env && mv mcp_servers.example.json mcp_servers.json

RUN python -m pip install --upgrade pip \
 && python -m pip install -r requirements.txt --no-dependencies \
 && python -m pip install .

CMD ["python", "-m", "assistant_bot.bot"]
