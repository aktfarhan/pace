# The API server Render runs
FROM python:3.13-slim

# Boston time in the logs
ENV TZ=America/New_York \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MALLOC_ARENA_MAX=2 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements-server.txt .
RUN pip install -r requirements-server.txt

COPY backend backend
COPY prompts prompts
COPY models/artifacts/delay.pkl models/artifacts/delay.pkl

# The timetable and its cached days
RUN python -m backend.planner.scrape_gtfs

# The nightly refresh rewrites the timetable
RUN useradd --create-home pace && chown -R pace /app/data
USER pace

CMD ["sh", "-c", "exec uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --timeout-graceful-shutdown 20"]
