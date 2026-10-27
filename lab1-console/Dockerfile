FROM python:3.12-slim-bookworm@sha256:6dd8b6dab6b3adc7812bab69eca5dbdc1a5cc690ad28306d234ffb4ef8ac9753 AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY lab1-console/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY lab1-console/src/ ./

FROM base AS tests
COPY lab1-console/requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt
COPY lab1-console/tests/ ./tests/
CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]

FROM base AS app
USER 1000:1000
CMD ["python", "-m", "tickets"]

