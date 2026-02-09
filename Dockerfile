# syntax=docker/dockerfile:1.4
FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --create-home --shell /bin/bash appuser \
    && mkdir -p logs db \
    && chown -R appuser:appgroup /app \
    && chmod +x scripts/start-backend.sh scripts/docker-compose-entrypoint.sh

ENV UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    MUNICIPALITY=Tokyo \
    INIT_DB_ON_START=false \
    RUN_FETCH_ON_START=false

EXPOSE 8000

USER appuser

CMD ["/app/scripts/start-backend.sh"]
