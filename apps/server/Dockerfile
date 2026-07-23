FROM python:3.12-slim

WORKDIR /app

# Install server package
COPY apps/server/pyproject.toml apps/server/README.md /tmp/server/
COPY apps/server/src /tmp/server/src
RUN pip install --no-cache-dir /tmp/server

# Ship canonical schemas alongside the image
COPY packages/schema /schema

ENV SENTINEL_SCHEMA_DIR=/schema/jsonschema/v1
ENV SENTINEL_AUTH_MODE=local
ENV SENTINEL_DATABASE_URL=postgresql+psycopg://sentinel:sentinel@postgres:5432/sentinel

EXPOSE 8080

CMD ["uvicorn", "sentinel_server.main:app", "--host", "0.0.0.0", "--port", "8080"]
