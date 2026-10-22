# Offline image. The default command does not call a network and does not read an API key.
# Audio measurement needs the optional audio extra and is not installed in this image.
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LIVE_ENABLED=0

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 appuser

USER appuser

CMD ["python", "-m", "consent_lab", "about"]
