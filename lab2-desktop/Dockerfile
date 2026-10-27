FROM python:3.12-slim-bookworm@sha256:6dd8b6dab6b3adc7812bab69eca5dbdc1a5cc690ad28306d234ffb4ef8ac9753 AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DISPLAY=:99
RUN apt-get update && apt-get install -y --no-install-recommends libtk8.6 xvfb xauth openbox x11vnc novnc websockify fonts-dejavu-core && rm -rf /var/lib/apt/lists/* && useradd --create-home --uid 1000 app
WORKDIR /app
COPY lab2-desktop/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY lab2-desktop/src/ ./
COPY lab2-desktop/desktop.py .
EXPOSE 6080

FROM base AS tests
COPY lab1-console/requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt
COPY lab2-desktop/tests/ ./tests/
USER app
CMD ["xvfb-run", "-a", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]

FROM base AS app
USER app
CMD ["python", "desktop.py"]
